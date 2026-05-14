import json, math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
from booking.models import Booking, TimeSlot, Service, User


def require_auth(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def get_consecutive_slots(start_slot, count):
    """Возвращает список из count подряд идущих слотов начиная с start_slot, или None."""
    if count == 1:
        return [start_slot]

    # Получаем все слоты того же филиала в тот же день, отсортированные по времени
    day_slots = list(TimeSlot.objects.filter(
        branch=start_slot.branch,
        date=start_slot.date,
    ).order_by('time'))

    # Находим позицию start_slot
    try:
        idx = next(i for i, s in enumerate(day_slots) if s.id == start_slot.id)
    except StopIteration:
        return None

    if idx + count > len(day_slots):
        return None

    consecutive = day_slots[idx:idx + count]

    # Проверяем что все свободны и идут подряд (разница 30 мин)
    for i in range(len(consecutive)):
        if not consecutive[i].is_available:
            return None
        if i > 0:
            prev_t = datetime.combine(consecutive[i-1].date, consecutive[i-1].time)
            curr_t = datetime.combine(consecutive[i].date, consecutive[i].time)
            if (curr_t - prev_t).seconds != 1800:  # 30 минут
                return None

    return consecutive


@csrf_exempt
def create(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    user = require_auth(request)
    if not user:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    data = json.loads(request.body)
    try:
        slot = TimeSlot.objects.get(id=data['slot_id'], is_available=True)
        service = Service.objects.get(id=data['service_id'])
    except (TimeSlot.DoesNotExist, Service.DoesNotExist, KeyError):
        return JsonResponse({'error': 'Слот недоступен или услуга не найдена'}, status=400)

    slots_needed = max(1, math.ceil(service.duration / 30))
    slots = get_consecutive_slots(slot, slots_needed)

    if not slots:
        return JsonResponse({
            'error': f'Для услуги «{service.name}» ({service.duration} мин) '
                     f'нужно {slots_needed} свободных слота подряд. Выберите другое время.'
        }, status=400)

    # Блокируем все нужные слоты
    for s in slots:
        s.is_available = False
        s.save()

    booking = Booking.objects.create(
        user=user,
        branch=slot.branch,
        slot=slot,  # Храним первый слот
        service=service,
        full_name=data.get('full_name', user.full_name),
        purpose=data.get('purpose', ''),
        status='active',
        confirmed_at=timezone.now(),
        slots_count=slots_needed,
    )
    return JsonResponse({'token': str(booking.token), 'booking_id': booking.id})


def _get_booking_slots(booking):
    """Возвращает все слоты бронирования (первый + consecutive)."""
    return get_consecutive_slots(booking.slot, booking.slots_count or 1) or [booking.slot]


@csrf_exempt
def cancel(request, token):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    user = require_auth(request)
    if not user:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    try:
        booking = Booking.objects.get(token=token, user=user)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Бронирование не найдено'}, status=404)

    if booking.status != 'active':
        return JsonResponse({'error': 'Нельзя отменить'}, status=400)

    slot_dt = datetime.combine(booking.slot.date, booking.slot.time)
    slot_dt = timezone.make_aware(slot_dt)
    if timezone.now() >= slot_dt - timedelta(hours=2):
        return JsonResponse({'error': 'Отмена невозможна менее чем за 2 часа до визита'}, status=400)

    booking.status = 'cancelled'
    for s in _get_booking_slots(booking):
        s.is_available = True
        s.save()
    booking.save()
    return JsonResponse({'status': 'cancelled'})


@csrf_exempt
def reschedule(request, token):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    user = require_auth(request)
    if not user:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    try:
        booking = Booking.objects.get(token=token, user=user)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Бронирование не найдено'}, status=404)

    if booking.status != 'active':
        return JsonResponse({'error': 'Нельзя перенести'}, status=400)

    slot_dt = datetime.combine(booking.slot.date, booking.slot.time)
    slot_dt = timezone.make_aware(slot_dt)
    if timezone.now() >= slot_dt - timedelta(hours=2):
        return JsonResponse({'error': 'Перенос невозможен менее чем за 2 часа'}, status=400)

    data = json.loads(request.body)
    try:
        new_slot = TimeSlot.objects.get(id=data['slot_id'], is_available=True)
    except (TimeSlot.DoesNotExist, KeyError):
        return JsonResponse({'error': 'Новый слот недоступен'}, status=400)

    slots_needed = booking.slots_count or 1
    new_slots = get_consecutive_slots(new_slot, slots_needed)
    if not new_slots:
        return JsonResponse({
            'error': f'Для этой услуги нужно {slots_needed} свободных слота подряд. Выберите другое время.'
        }, status=400)

    # Освобождаем старые, блокируем новые
    for s in _get_booking_slots(booking):
        s.is_available = True
        s.save()
    for s in new_slots:
        s.is_available = False
        s.save()

    booking.slot = new_slot
    booking.branch = new_slot.branch
    booking.save()
    return JsonResponse({'status': 'rescheduled'})


def history(request):
    user = require_auth(request)
    if not user:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    bookings = Booking.objects.filter(user=user).select_related('slot', 'branch', 'service').order_by('-slot__date', '-slot__time')
    result = []
    for b in bookings:
        slots_needed = b.slots_count or 1
        end_minutes = b.slot.time.hour * 60 + b.slot.time.minute + slots_needed * 30
        end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"
        result.append({
            'id': b.id,
            'token': str(b.token),
            'status': b.status,
            'status_label': dict(Booking.STATUS).get(b.status, b.status),
            'date': str(b.slot.date),
            'time': str(b.slot.time)[:5],
            'end_time': end_time,
            'branch': b.branch.name,
            'branch_address': b.branch.address,
            'service': b.service.name,
            'service_duration': b.service.duration,
            'purpose': b.purpose,
            'full_name': b.full_name,
            'slot_id': b.slot.id,
            'slots_count': slots_needed,
        })
    return JsonResponse(result, safe=False)
