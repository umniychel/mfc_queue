from django.http import JsonResponse
from booking.models import TimeSlot
from datetime import timedelta
from django.utils import timezone


def get_slots(request, branch_id):
    today = timezone.now().date()
    end = today + timedelta(days=14)
    slots = TimeSlot.objects.filter(
        branch_id=branch_id,
        date__range=(today, end),
    ).order_by('date', 'time')
    result = []
    for s in slots:
        result.append({
            'id': s.id,
            'date': str(s.date),
            'time': str(s.time)[:5],
            'is_available': s.is_available,
        })
    return JsonResponse(result, safe=False)


def list_services(request):
    from booking.models import Service
    services = list(Service.objects.values('id', 'name', 'category', 'duration'))
    return JsonResponse(services, safe=False)
