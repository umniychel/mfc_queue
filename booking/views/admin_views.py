import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from booking.models import User, Branch, Service, TimeSlot, Booking


def require_admin(request):
    if not request.session.get('is_admin'):
        return False
    return True


# ─── AUTH ───────────────────────────────────────────────
@csrf_exempt
def admin_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    if data.get('username') == 'admin' and data.get('password') == 'admin123':
        request.session['is_admin'] = True
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Неверный логин или пароль'}, status=400)


def admin_logout(request):
    request.session.pop('is_admin', None)
    return JsonResponse({'status': 'ok'})


def admin_check(request):
    return JsonResponse({'is_admin': bool(request.session.get('is_admin'))})


# ─── STATS ──────────────────────────────────────────────
def admin_stats(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    return JsonResponse({
        'users': User.objects.count(),
        'branches': Branch.objects.count(),
        'services': Service.objects.count(),
        'slots_total': TimeSlot.objects.count(),
        'slots_free': TimeSlot.objects.filter(is_available=True).count(),
        'bookings_active': Booking.objects.filter(status='active').count(),
        'bookings_cancelled': Booking.objects.filter(status='cancelled').count(),
        'bookings_total': Booking.objects.count(),
    })


# ─── BOOKINGS ───────────────────────────────────────────
def admin_bookings(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    bookings = Booking.objects.select_related('user', 'branch', 'service', 'slot').order_by('-created_at')
    result = []
    for b in bookings:
        result.append({
            'id': b.id,
            'token': str(b.token),
            'status': b.status,
            'status_label': dict(Booking.STATUS).get(b.status, b.status),
            'user': b.user.username,
            'full_name': b.full_name,
            'branch': b.branch.name,
            'service': b.service.name,
            'date': str(b.slot.date),
            'time': str(b.slot.time)[:5],
            'purpose': b.purpose,
            'created_at': b.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    return JsonResponse(result, safe=False)


@csrf_exempt
def admin_cancel_booking(request, booking_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Не найдено'}, status=404)
    booking.status = 'cancelled'
    booking.slot.is_available = True
    booking.slot.save()
    booking.save()
    return JsonResponse({'status': 'ok'})


# ─── BRANCHES ───────────────────────────────────────────
def admin_branches(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    return JsonResponse(list(Branch.objects.values()), safe=False)


@csrf_exempt
def admin_branch_create(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    data = json.loads(request.body)
    b = Branch.objects.create(
        name=data['name'],
        address=data['address'],
        load_level=data.get('load_level', 'low')
    )
    return JsonResponse({'id': b.id, 'name': b.name})


@csrf_exempt
def admin_branch_delete(request, branch_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    Branch.objects.filter(id=branch_id).delete()
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def admin_branch_update(request, branch_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    data = json.loads(request.body)
    Branch.objects.filter(id=branch_id).update(
        name=data.get('name'),
        address=data.get('address'),
        load_level=data.get('load_level', 'low')
    )
    return JsonResponse({'status': 'ok'})


# ─── SERVICES ───────────────────────────────────────────
def admin_services(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    return JsonResponse(list(Service.objects.values()), safe=False)


@csrf_exempt
def admin_service_create(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    data = json.loads(request.body)
    s = Service.objects.create(
        name=data['name'],
        category=data['category'],
        duration=int(data.get('duration', 30))
    )
    return JsonResponse({'id': s.id, 'name': s.name})


@csrf_exempt
def admin_service_delete(request, service_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    Service.objects.filter(id=service_id).delete()
    return JsonResponse({'status': 'ok'})


# ─── SLOTS ──────────────────────────────────────────────
def admin_slots(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    branch_id = request.GET.get('branch_id')
    qs = TimeSlot.objects.select_related('branch').order_by('date', 'time')
    if branch_id:
        qs = qs.filter(branch_id=branch_id)
    result = [{'id': s.id, 'branch': s.branch.name, 'branch_id': s.branch_id,
               'date': str(s.date), 'time': str(s.time)[:5], 'is_available': s.is_available}
              for s in qs[:200]]
    return JsonResponse(result, safe=False)


@csrf_exempt
def admin_slot_create(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    data = json.loads(request.body)
    from datetime import date, time, timedelta
    branch = Branch.objects.get(id=data['branch_id'])
    # Generate slots for date range
    start = date.fromisoformat(data['date_from'])
    end = date.fromisoformat(data['date_to'])
    times = [time(h, m) for h in range(9, 17) for m in (0, 30)]
    created = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            for t in times:
                _, made = TimeSlot.objects.get_or_create(branch=branch, date=d, time=t,
                                                          defaults={'is_available': True})
                if made:
                    created += 1
        d += timedelta(days=1)
    return JsonResponse({'created': created})


@csrf_exempt
def admin_slot_delete(request, slot_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    TimeSlot.objects.filter(id=slot_id).delete()
    return JsonResponse({'status': 'ok'})


# ─── USERS ──────────────────────────────────────────────
def admin_users(request):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    users = list(User.objects.values('id', 'username', 'full_name', 'phone'))
    for u in users:
        u['bookings'] = Booking.objects.filter(user_id=u['id']).count()
    return JsonResponse(users, safe=False)


@csrf_exempt
def admin_user_delete(request, user_id):
    if not require_admin(request):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    User.objects.filter(id=user_id).delete()
    return JsonResponse({'status': 'ok'})
