from django.urls import path
from booking.views import auth_views, booking_views, branch_views, slot_views, admin_views

urlpatterns = [
    # Auth
    path('auth/register/', auth_views.register),
    path('auth/login/', auth_views.login),
    path('auth/logout/', auth_views.logout),
    path('auth/me/', auth_views.me),

    # Data
    path('branches/', branch_views.list_branches),
    path('services/', slot_views.list_services),
    path('slots/<int:branch_id>/', slot_views.get_slots),

    # Bookings
    path('booking/create/', booking_views.create),
    path('booking/<uuid:token>/cancel/', booking_views.cancel),
    path('booking/<uuid:token>/reschedule/', booking_views.reschedule),
    path('booking/history/', booking_views.history),

    # Admin
    path('admin-api/login/', admin_views.admin_login),
    path('admin-api/logout/', admin_views.admin_logout),
    path('admin-api/check/', admin_views.admin_check),
    path('admin-api/stats/', admin_views.admin_stats),
    path('admin-api/bookings/', admin_views.admin_bookings),
    path('admin-api/bookings/<int:booking_id>/cancel/', admin_views.admin_cancel_booking),
    path('admin-api/branches/', admin_views.admin_branches),
    path('admin-api/branches/create/', admin_views.admin_branch_create),
    path('admin-api/branches/<int:branch_id>/delete/', admin_views.admin_branch_delete),
    path('admin-api/branches/<int:branch_id>/update/', admin_views.admin_branch_update),
    path('admin-api/services/', admin_views.admin_services),
    path('admin-api/services/create/', admin_views.admin_service_create),
    path('admin-api/services/<int:service_id>/delete/', admin_views.admin_service_delete),
    path('admin-api/slots/', admin_views.admin_slots),
    path('admin-api/slots/create/', admin_views.admin_slot_create),
    path('admin-api/slots/<int:slot_id>/delete/', admin_views.admin_slot_delete),
    path('admin-api/users/', admin_views.admin_users),
    path('admin-api/users/<int:user_id>/delete/', admin_views.admin_user_delete),
]
