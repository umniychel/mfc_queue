import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from booking.models import User


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()

    if not username or not password:
        return JsonResponse({'error': 'Логин и пароль обязательны'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Пользователь уже существует'}, status=400)

    user = User(username=username, full_name=full_name, phone=phone)
    user.set_password(password)
    user.save()

    request.session['user_id'] = user.id
    return JsonResponse({'user_id': user.id, 'username': user.username, 'full_name': user.full_name})


@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Неверный логин или пароль'}, status=400)

    if not user.check_password(password):
        return JsonResponse({'error': 'Неверный логин или пароль'}, status=400)

    request.session['user_id'] = user.id
    return JsonResponse({'user_id': user.id, 'username': user.username, 'full_name': user.full_name})


@csrf_exempt
def logout(request):
    request.session.flush()
    return JsonResponse({'status': 'ok'})


def me(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'user_id': user.id, 'username': user.username, 'full_name': user.full_name, 'phone': user.phone})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Не авторизован'}, status=401)
