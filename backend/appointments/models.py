from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from patients.models import Patient

class TimeSlot(models.Model):
    """Model for defining available time slots for appointments"""
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='time_slots',
        verbose_name=_('Doctor')
    )
    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Start Time'))
    end_time = models.TimeField(verbose_name=_('End Time'))
    is_available = models.BooleanField(default=True, verbose_name=_('Available'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Time Slot')
        verbose_name_plural = _('Time Slots')
        ordering = ['date', 'start_time']
        unique_together = ('doctor', 'date', 'start_time')
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"
    
    def clean(self):
        # Validate that end_time is after start_time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': _('End time must be after start time')
            })
        
        # Validate that date is not in the past
        # Allow creating time slots for today
        if self.date and self.date < timezone.now().date():
            raise ValidationError({
                'date': _('Cannot create time slots in the past')
            })
    
    def save(self, *args, **kwargs):
        # We don't call self.clean() here because it's already called in the view
        # and it would cause double validation
        super().save(*args, **kwargs)

class Appointment(models.Model):
    """Model for patient appointments"""
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
        ('CANCELLED', 'Cancelled')
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Patient Name'))
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Reason'))