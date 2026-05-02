from django.http import JsonResponse
from booking.models import Branch


def list_branches(request):
    branches = list(Branch.objects.values('id', 'name', 'address', 'load_level'))
    return JsonResponse(branches, safe=False)
