from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification, NotificationSetting

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get notifications for the current user"""
    user = request.user
    
    # Get query parameters
    is_read = request.query_params.get('is_read')
    notification_type = request.query_params.get('type')
    limit = int(request.query_params.get('limit', 20))  # Default to 20 notifications
    
    # Base query: only notifications for this user
    queryset = Notification.objects.filter(user=user)
    
    # Filter by read status if specified
    if is_read is not None:
        is_read_bool = is_read.lower() == 'true'
        queryset = queryset.filter(is_read=is_read_bool)
    
    # Filter by notification type if specified
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    
    # Order by created_at (newest first) and limit results
    notifications = queryset.order_by('-created_at')[:limit]
    
    # Count unread notifications
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    # Format response data
    data = {
        'notifications': [{
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at,
            'related_object_id': notification.related_object_id,
            'related_object_type': notification.related_object_type
        } for notification in notifications],
        'unread_count': unread_count
    }
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id=None):
    """Mark a notification as read, or mark all as read if no ID provided"""
    user = request.user
    
    if notification_id:
        # Mark specific notification as read
        try:
            notification = get_object_or_404(Notification, id=notification_id, user=user)
            notification.mark_as_read()
            return Response({
                'success': _('Notification marked as read')
            }, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({
                'error': _('Notification not found')
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # Mark all notifications as read
        notifications = Notification.objects.filter(user=user, is_read=False)
        for notification in notifications:
            notification.mark_as_read()
        
        return Response({
            'success': _('All notifications marked as read'),
            'count': notifications.count()
        }, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_settings(request):
    """Get or update notification settings for the current user"""
    user = request.user
    
    # Get or create notification settings for the user
    settings, created = NotificationSetting.objects.get_or_create(user=user)
    
    if request.method == 'GET':
        # Return current settings
        data = {
            'email_settings': {
                'appointment_reminders': settings.email_appointment_reminders,
                'prescription_updates': settings.email_prescription_updates,
                'messages': settings.email_messages,
                'system_updates': settings.email_system_updates
            },
            'sms_settings': {
                'appointment_reminders': settings.sms_appointment_reminders,
                'prescription_updates': settings.sms_prescription_updates,
                'messages': settings.sms_messages
            },
            'push_settings': {
                'appointment_reminders': settings.push_appointment_reminders,
                'prescription_updates': settings.push_prescription_updates,
                'messages': settings.push_messages,
                'system_updates': settings.push_system_updates
            },
            'appointment_reminder_time': settings.appointment_reminder_time
        }
        return Response(data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        # Update settings
        try:
            # Email settings
            if 'email_settings' in request.data:
                email_settings = request.data['email_settings']
                if 'appointment_reminders' in email_settings:
                    settings.email_appointment_reminders = email_settings['appointment_reminders']
                if 'prescription_updates' in email_settings:
                    settings.email_prescription_updates = email_settings['prescription_updates']
                if 'messages' in email_settings:
                    settings.email_messages = email_settings['messages']
                if 'system_updates' in email_settings:
                    settings.email_system_updates = email_settings['system_updates']
            
            # SMS settings
            if 'sms_settings' in request.data:
                sms_settings = request.data['sms_settings']
                if 'appointment_reminders' in sms_settings:
                    settings.sms_appointment_reminders = sms_settings['appointment_reminders']
                if 'prescription_updates' in sms_settings:
                    settings.sms_prescription_updates = sms_settings['prescription_updates']
                if 'messages' in sms_settings:
                    settings.sms_messages = sms_settings['messages']
            
            # Push settings
            if 'push_settings' in request.data:
                push_settings = request.data['push_settings']
                if 'appointment_reminders' in push_settings:
                    settings.push_appointment_reminders = push_settings['appointment_reminders']
                if 'prescription_updates' in push_settings:
                    settings.push_prescription_updates = push_settings['prescription_updates']
                if 'messages' in push_settings:
                    settings.push_messages = push_settings['messages']
                if 'system_updates' in push_settings:
                    settings.push_system_updates = push_settings['system_updates']
            
            # Appointment reminder time
            if 'appointment_reminder_time' in request.data:
                settings.appointment_reminder_time = request.data['appointment_reminder_time']
            
            # Save changes
            settings.save()
            
            return Response({
                'success': _('Notification settings updated successfully')
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_notification(request):
    """Create a new notification (admin or system use)"""
    user = request.user
    
    # Check permissions: only staff or system can create notifications for others
    if not user.is_staff and request.data.get('user_id') and int(request.data.get('user_id')) != user.id:
        return Response({
            'error': _('You do not have permission to create notifications for other users')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get data from request
    target_user_id = request.data.get('user_id', user.id)
    title = request.data.get('title')
    message = request.data.get('message')
    notification_type = request.data.get('type', 'system')
    related_object_id = request.data.get('related_object_id')
    related_object_type = request.data.get('related_object_type')
    scheduled_time = request.data.get('scheduled_time', timezone.now())
    
    # Validate required fields
    if not all([title, message]):
        return Response({
            'error': _('Please provide all required fields')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the notification
    try:
        from accounts.models import User
        target_user = User.objects.get(id=target_user_id)
        
        notification = Notification(
            user=target_user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            scheduled_time=scheduled_time,
            is_sent=True  # Mark as sent since we're creating it directly
        )
        notification.save()
        
        return Response({
            'success': _('Notification created successfully'),
            'id': notification.id
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({
            'error': _('User not found')
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
