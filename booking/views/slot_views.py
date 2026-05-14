from django.http import JsonResponse
from booking.models import TimeSlot, Service
from datetime import timedelta, datetime
from django.utils import timezone


def get_slots(request, branch_id):
    """
    Возвращает слоты с полем 'slots_needed' = кол-во 30-мин блоков для каждой услуги.
    Фронтенд использует это чтобы показывать только доступные слоты под выбранную услугу.
    """
    today = timezone.now().date()
    end = today + timedelta(days=14)

    slots = list(TimeSlot.objects.filter(
        branch_id=branch_id,
        date__range=(today, end),
    ).order_by('date', 'time'))

    # Строим set доступных слотов для быстрой проверки
    available_ids = {s.id for s in slots if s.is_available}

    # Для каждого слота вычисляем, достаточно ли подряд идущих свободных слотов
    # для каждого количества блоков (1, 2, 3)
    # Группируем по дате для правильного определения "следующего" слота
    from collections import defaultdict
    by_date = defaultdict(list)
    for s in slots:
        by_date[s.date].append(s)

    # Для каждого слота сохраняем индекс внутри дня
    slot_day_index = {}
    for date_slots in by_date.values():
        for i, s in enumerate(date_slots):
            slot_day_index[s.id] = (date_slots, i)

    def can_fit(slot, needed_blocks):
        """Проверяет, есть ли needed_blocks подряд идущих свободных слотов начиная с данного"""
        if not slot.is_available:
            return False
        day_slots, idx = slot_day_index[slot.id]
        for k in range(needed_blocks):
            if idx + k >= len(day_slots):
                return False
            if not day_slots[idx + k].is_available:
                return False
        return True

    result = []
    for s in slots:
        result.append({
            'id': s.id,
            'date': str(s.date),
            'time': str(s.time)[:5],
            'is_available': s.is_available,
            # Для каждого кол-ва блоков (1=30мин, 2=60мин, 3=90мин) — доступен ли
            'fits': {
                '1': can_fit(s, 1),
                '2': can_fit(s, 2),
                '3': can_fit(s, 3),
            }
        })

    return JsonResponse(result, safe=False)


def list_services(request):
    services = list(Service.objects.values('id', 'name', 'category', 'duration'))
    # Добавляем кол-во блоков для каждой услуги
    for svc in services:
        import math
        svc['slots_needed'] = max(1, math.ceil(svc['duration'] / 30))
    return JsonResponse(services, safe=False)
