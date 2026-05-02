"""
Запусти: python seed.py
Создаёт тестовые данные: филиалы, услуги, слоты на 14 дней.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfc_queue.settings')
django.setup()

from booking.models import Branch, Service, TimeSlot, User
from datetime import date, timedelta, time

# Очистка
TimeSlot.objects.all().delete()
Service.objects.all().delete()
Branch.objects.all().delete()

# Филиалы
branches = [
    Branch.objects.create(name='МФЦ Центральный', address='ул. Ленина, 1', load_level='high'),
    Branch.objects.create(name='МФЦ Северный', address='пр. Мира, 45', load_level='medium'),
    Branch.objects.create(name='МФЦ Западный', address='ул. Садовая, 12', load_level='low'),
]

# Услуги
services = [
    Service.objects.create(name='Оформление паспорта', category='ФМС', duration=30),
    Service.objects.create(name='Регистрация по месту жительства', category='ФМС', duration=20),
    Service.objects.create(name='Регистрация недвижимости', category='Росреестр', duration=45),
    Service.objects.create(name='Справка о составе семьи', category='ЗАГС', duration=15),
    Service.objects.create(name='Оформление пособия', category='Соцзащита', duration=30),
    Service.objects.create(name='Выписка из ЕГРН', category='Росреестр', duration=20),
]

# Слоты
today = date.today()
slot_times = [time(9, 0), time(9, 30), time(10, 0), time(10, 30),
              time(11, 0), time(11, 30), time(12, 0), time(14, 0),
              time(14, 30), time(15, 0), time(15, 30), time(16, 0)]

for branch in branches:
    for i in range(14):
        d = today + timedelta(days=i)
        if d.weekday() < 5:  # пн-пт
            for t in slot_times:
                TimeSlot.objects.create(branch=branch, date=d, time=t, is_available=True)

print(f"Создано: {Branch.objects.count()} филиалов, {Service.objects.count()} услуг, {TimeSlot.objects.count()} слотов")
