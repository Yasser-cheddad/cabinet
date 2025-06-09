from django.urls import path
from . import views

urlpatterns = [
    # TimeSlot endpoints
    path('timeslots/', views.available_time_slots, name='available_time_slots'),
    path('timeslots/create/', views.create_time_slot, name='create_time_slot'),
    path('timeslots/<int:time_slot_id>/', views.time_slot_detail, name='time_slot_detail'),
    
    # Appointment endpoints
    path('', views.get_appointments, name='get_all_appointments'),  # Root endpoint for all appointments
    path('create/', views.create_appointment, name='create_appointment'),
    path('create-patient/', views.create_appointment_patient, name='create_appointment_patient'),
    path('list/', views.get_appointments, name='get_appointments'),
    path('calendar/', views.get_calendar_appointments, name='get_calendar_appointments'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('<int:appointment_id>/ical/', views.download_appointment_ical, name='download_appointment_ical'),
]
