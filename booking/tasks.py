from celery import shared_task
from booking.models import Booking
from django.utils import timezone


@shared_task
def send_reminders():
    now = timezone.now()

    bookings = Booking.objects.filter(status='active')

    for b in bookings:
        print(f"Напоминание {b.user.phone}")