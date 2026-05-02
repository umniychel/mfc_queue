import json
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

    slot.is_available = False
    slot.save()

    booking = Booking.objects.create(
        user=user,
        branch=slot.branch,
        slot=slot,
        service=service,
        full_name=data.get('full_name', user.full_name),
        purpose=data.get('purpose', ''),
        status='active',
        confirmed_at=timezone.now(),
    )
    return JsonResponse({'token': str(booking.token), 'booking_id': booking.id})


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

    # Нельзя отменить менее чем за 2 часа
    slot_dt = datetime.combine(booking.slot.date, booking.slot.time)
    slot_dt = timezone.make_aware(slot_dt)
    if timezone.now() >= slot_dt - timedelta(hours=2):
        return JsonResponse({'error': 'Отмена невозможна менее чем за 2 часа до визита'}, status=400)

    booking.status = 'cancelled'
    booking.slot.is_available = True
    booking.slot.save()
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

    booking.slot.is_available = True
    booking.slot.save()
    new_slot.is_available = False
    new_slot.save()
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
        result.append({
            'id': b.id,
            'token': str(b.token),
            'status': b.status,
            'status_label': dict(Booking.STATUS).get(b.status, b.status),
            'date': str(b.slot.date),
            'time': str(b.slot.time)[:5],
            'branch': b.branch.name,
            'branch_address': b.branch.address,
            'service': b.service.name,
            'purpose': b.purpose,
            'full_name': b.full_name,
            'slot_id': b.slot.id,
        })
    return JsonResponse(result, safe=False)
