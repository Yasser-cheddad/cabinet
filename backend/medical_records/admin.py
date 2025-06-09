from django.contrib import admin
from .models import MedicalRecord, MedicalNote, Prescription, MedicalFile

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_type', 'created_at', 'updated_at', 'last_updated_by')
    list_filter = ('blood_type', 'created_at', 'updated_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'allergies')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MedicalNote)
class MedicalNoteAdmin(admin.ModelAdmin):
    list_display = ('medical_record', 'doctor', 'date', 'created_at')
    list_filter = ('date', 'created_at', 'doctor')
    search_fields = ('medical_record__patient__user__first_name', 'medical_record__patient__user__last_name', 'symptoms', 'diagnosis')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medication_name', 'medical_note', 'dosage', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('medication_name', 'medical_note__medical_record__patient__user__first_name')
    readonly_fields = ('created_at',)

@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = ('medical_record', 'file_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('medical_record__patient__user__first_name', 'description')
    readonly_fields = ('uploaded_at',)
