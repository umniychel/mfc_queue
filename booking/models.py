from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)


class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    load_level = models.CharField(max_length=20, default='low')


class Service(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    duration = models.IntegerField(default=30)


class TimeSlot(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)


class Booking(models.Model):
    STATUS = [
        ('pending', 'Ожидает'),
        ('active', 'Активно'),
        ('cancelled', 'Отменено'),
        ('expired', 'Просрочено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True)
    purpose = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    slots_count = models.IntegerField(default=1)  # кол-во 30-мин блоков
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
