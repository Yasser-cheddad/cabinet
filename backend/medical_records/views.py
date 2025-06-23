from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.translation import gettext_lazy as _
from .models import MedicalRecord, MedicalNote, Prescription, MedicalFile
from .serializers import (
    MedicalRecordSerializer,
    MedicalNoteSerializer,
    PrescriptionSerializer,
    MedicalFileSerializer
)
from accounts.permissions import IsDoctor, IsPatient, CanManageMedicalRecords

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [CanManageMedicalRecords]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'doctor':
            return MedicalRecord.objects.all()
        elif user.role == 'patient':
            return MedicalRecord.objects.filter(patient__user=user)
        return MedicalRecord.objects.none()

    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def print(self, request, pk=None):
        """Generate a printable version of the medical record"""
        record = self.get_object()
        # Logic to generate PDF or printable format
        return Response({
            'message': _('Print functionality to be implemented'),
            'record_id': record.id
        })

class MedicalNoteViewSet(viewsets.ModelViewSet):
    queryset = MedicalNote.objects.all()
    serializer_class = MedicalNoteSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return MedicalNote.objects.filter(
            medical_record_id=self.kwargs.get('medical_record_pk')
        )

    def perform_create(self, serializer):
        serializer.save(
            doctor=self.request.user,
            medical_record_id=self.kwargs.get('medical_record_pk')
        )

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctor]

    def get_queryset(self):
        return Prescription.objects.filter(
            medical_note_id=self.kwargs.get('medical_note_pk')
        )

    def perform_create(self, serializer):
        serializer.save(medical_note_id=self.kwargs.get('medical_note_pk'))

class MedicalFileViewSet(viewsets.ModelViewSet):
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    permission_classes = [CanManageMedicalRecords]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return MedicalFile.objects.filter(
            medical_record_id=self.kwargs.get('medical_record_pk')
        )

    def perform_create(self, serializer):
        serializer.save(
            uploaded_by=self.request.user,
            medical_record_id=self.kwargs.get('medical_record_pk')
        )
