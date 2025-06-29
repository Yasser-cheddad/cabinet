from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification endpoints
    path('', views.get_notifications, name='notification-list'),
    path('<int:notification_id>/mark-read/', views.mark_notification_read, name='mark-notification-read'),
    path('mark-all-read/', views.mark_notification_read, name='mark-all-notifications-read'),
    path('create/', views.create_notification, name='create-notification'),
    path('send/', views.send_custom_notification, name='send-custom-notification'),
    
    # Notification settings endpoints
    path('settings/', views.notification_settings, name='notification-settings'),
]
