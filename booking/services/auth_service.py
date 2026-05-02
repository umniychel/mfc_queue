import random
from django.core.cache import cache
from booking.models import User


def send_code(phone):
    code = str(random.randint(1000, 9999))
    cache.set(f"code_{phone}", code, 300)
    print("SMS:", code)


def verify_code(phone, code):
    real = cache.get(f"code_{phone}")

    if real != code:
        return None

    user, _ = User.objects.get_or_create(phone=phone)
    user.is_verified = True
    user.save()

    return user