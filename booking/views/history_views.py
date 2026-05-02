from rest_framework.decorators import api_view
from rest_framework.response import Response
from booking.models import Booking


@api_view(['GET'])
def list_history(request, user_id):
    bookings = Booking.objects.filter(user_id=user_id).select_related('slot', 'branch', 'service')
    result = []
    for b in bookings:
        result.append({
            'token': str(b.token),
            'status': b.status,
            'date': str(b.slot.date),
            'time': str(b.slot.time),
            'branch': b.branch.name,
            'service': b.service.name,
        })
    return Response(result)
