from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Patient
from .serializers import PatientSerializer
from .permissions import IsDoctorOrReadOnly
from accounts.permissions import IsDoctor, IsSecretary
from django.utils.translation import gettext_lazy as _

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_patients(request):
    """Get a simplified list of all patients for dropdowns"""
    # Only doctors and secretaries can see all patients
    if request.user.role not in ['doctor', 'secretary']:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    patients = Patient.objects.select_related('user').all()
    data = [{
        'id': patient.id,
        'name': patient.user.get_full_name(),
        'email': patient.user.email
    } for patient in patients]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_patient_profile(request):
    """Create a patient profile for the current user if they are a patient"""
    user = request.user
    
    # Check if the user is a patient
    if user.role != 'patient':
        return Response({
            'error': _('Only patients can have a patient profile')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if a patient profile already exists
    patient_exists = Patient.objects.filter(user=user).exists()
    
    if patient_exists:
        # Return the existing patient profile
        patient = Patient.objects.get(user=user)
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Create a new patient profile
    try:
        patient = Patient(user=user)
        patient.save()
        
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.select_related('user').all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by doctor if needed
        return queryset
        
    def perform_create(self, serializer):
        # If the user is a patient, create a profile for themselves
        if self.request.user.role == 'patient':
            # Check if patient already has a profile
            if Patient.objects.filter(user=self.request.user).exists():
                # We can't return a Response from perform_create, so we'll raise an exception
                from rest_framework.exceptions import ValidationError
                raise ValidationError('Patient profile already exists')
            
            # Create profile with current user
            serializer.save(user=self.request.user)
        # If doctor or secretary, allow them to create patient profiles
        elif self.request.user.role in ['doctor', 'secretary']:
            # For doctor/secretary, the user_id must be provided in the request data
            # The serializer will handle this through the user_id field which maps to 'user'
            if 'user' not in serializer.validated_data:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'user_id': 'This field is required when creating a patient as a doctor or secretary.'})
            serializer.save()
        else:
            # We can't return a Response from perform_create, so we'll raise an exception
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Not authorized to create patient profiles')