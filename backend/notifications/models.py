from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.models import User

class Notification(models.Model):
    """Model for user notifications"""
    TYPE_CHOICES = [
        ('appointment', _('Appointment')),
        ('prescription', _('Prescription')),
        ('message', _('Message')),
        ('system', _('System')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User')
    )
    
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    message = models.TextField(verbose_name=_('Message'))
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system',
        verbose_name=_('Notification Type')
    )
    
    # Optional reference to related objects
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Status fields
    is_read = models.BooleanField(default=False, verbose_name=_('Read'))
    is_sent = models.BooleanField(default=False, verbose_name=_('Sent'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_time = models.DateTimeField(default=timezone.now, verbose_name=_('Scheduled Time'))
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title} ({self.created_at})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read', 'updated_at'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = True
        self.save(update_fields=['is_sent', 'updated_at'])

class NotificationSetting(models.Model):
    """Model for user notification preferences"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name=_('User')
    )
    
    # Email notification settings
    email_appointment_reminders = models.BooleanField(default=True, verbose_name=_('Email Appointment Reminders'))
    email_prescription_updates = models.BooleanField(default=True, verbose_name=_('Email Prescription Updates'))
    email_messages = models.BooleanField(default=True, verbose_name=_('Email Messages'))
    email_system_updates = models.BooleanField(default=True, verbose_name=_('Email System Updates'))
    
    # SMS notification settings
    sms_appointment_reminders = models.BooleanField(default=False, verbose_name=_('SMS Appointment Reminders'))
    sms_prescription_updates = models.BooleanField(default=False, verbose_name=_('SMS Prescription Updates'))
    sms_messages = models.BooleanField(default=False, verbose_name=_('SMS Messages'))
    
    # Push notification settings
    push_appointment_reminders = models.BooleanField(default=True, verbose_name=_('Push Appointment Reminders'))
    push_prescription_updates = models.BooleanField(default=True, verbose_name=_('Push Prescription Updates'))
    push_messages = models.BooleanField(default=True, verbose_name=_('Push Messages'))
    push_system_updates = models.BooleanField(default=True, verbose_name=_('Push System Updates'))
    
    # Reminder timing preferences (in hours before appointment)
    appointment_reminder_time = models.PositiveIntegerField(default=24, verbose_name=_('Appointment Reminder Time (hours)'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Notification Setting')
        verbose_name_plural = _('Notification Settings')
    
    def __str__(self):
        return f"Notification Settings for {self.user.get_full_name()}"
