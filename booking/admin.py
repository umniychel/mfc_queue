from django.contrib import admin
from .models import Branch, Service, TimeSlot, Booking

admin.site.register(Branch)
admin.site.register(Service)
admin.site.register(TimeSlot)
admin.site.register(Booking)