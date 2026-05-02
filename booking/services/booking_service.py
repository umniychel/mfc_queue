from booking.models import Booking, TimeSlot
from booking.services.slot_service import lock_slot
from django.utils import timezone


def create_booking(user, slot, service):
    if not lock_slot(slot.id):
        return {"error": "Слот занят"}

    booking = Booking.objects.create(
        user=user,
        branch=slot.branch,
        slot=slot,
        service=service,
        status='pending'
    )

    return {"token": booking.token}


def confirm_booking(booking):
    booking.status = 'active'
    booking.confirmed_at = timezone.now()

    booking.slot.is_available = False
    booking.slot.save()
    booking.save()

    return {"status": "confirmed"}


def cancel_booking(booking):
    booking.status = 'cancelled'
    booking.slot.is_available = True

    booking.save()
    booking.slot.save()

    return {"status": "cancelled"}


def reschedule_booking(booking, new_slot):
    booking.slot.is_available = True
    new_slot.is_available = False

    booking.slot = new_slot
    booking.save()
    new_slot.save()

    return {"status": "rescheduled"}