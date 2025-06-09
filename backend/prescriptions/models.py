from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from patients.models import Patient

class Medication(models.Model):
    """Model for medication information"""
    name = models.CharField(max_length=255, verbose_name=_('Medication Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    dosage_form = models.CharField(max_length=100, verbose_name=_('Dosage Form'))  # e.g., tablet, capsule, liquid
    strength = models.CharField(max_length=100, verbose_name=_('Strength'))  # e.g., 500mg, 10mg/ml
    manufacturer = models.CharField(max_length=255, blank=True, verbose_name=_('Manufacturer'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Medication')
        verbose_name_plural = _('Medications')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} {self.strength} {self.dosage_form}"

class Prescription(models.Model):
    """Model for patient prescriptions"""
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Patient')
    )
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'},
        related_name='doctor_prescriptions',
        verbose_name=_('Doctor')
    )
    
    prescription_date = models.DateField(default=timezone.now, verbose_name=_('Prescription Date'))
    expiry_date = models.DateField(blank=True, null=True, verbose_name=_('Expiry Date'))
    diagnosis = models.TextField(verbose_name=_('Diagnosis'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Status')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Prescription')
        verbose_name_plural = _('Prescriptions')
        ordering = ['-prescription_date']
    
    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.prescription_date}"
    
    def clean(self):
        # Validate that expiry_date is after prescription_date
        if self.expiry_date and self.prescription_date and self.expiry_date < self.prescription_date:
            raise ValidationError({
                'expiry_date': _('Expiry date must be after prescription date')
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class PrescriptionItem(models.Model):
    """Model for individual medication items within a prescription"""
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Prescription')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,  # Don't delete medication if it's in a prescription
        related_name='prescription_items',
        verbose_name=_('Medication')
    )
    
    dosage = models.CharField(max_length=100, verbose_name=_('Dosage'))  # e.g., 1 tablet
    frequency = models.CharField(max_length=100, verbose_name=_('Frequency'))  # e.g., twice daily
    duration = models.CharField(max_length=100, verbose_name=_('Duration'))  # e.g., 7 days
    instructions = models.TextField(verbose_name=_('Instructions'))  # e.g., take with food
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Prescription Item')
        verbose_name_plural = _('Prescription Items')
    
    def __str__(self):
        return f"{self.medication.name} - {self.dosage} - {self.frequency}"
