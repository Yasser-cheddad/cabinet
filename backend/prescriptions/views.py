from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Prescription, PrescriptionItem, Medication
from accounts.models import User
from patients.models import Patient

# Medication views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medication_list(request):
    """Get a list of all medications"""
    # Get query parameters
    search_query = request.query_params.get('search', '')
    
    # Filter medications by search query
    if search_query:
        medications = Medication.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(dosage_form__icontains=search_query)
        ).order_by('name')
    else:
        medications = Medication.objects.all().order_by('name')
    
    # Format response data
    data = [{
        'id': med.id,
        'name': med.name,
        'description': med.description,
        'dosage_form': med.dosage_form,
        'strength': med.strength,
        'manufacturer': med.manufacturer
    } for med in medications]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_medication(request):
    """Create a new medication (only for doctors or staff)"""
    user = request.user
    
    # Check permissions: only doctors or secretaries can create medications
    if user.role not in ['doctor', 'secretary']:
        return Response({
            'error': _('Only doctors or secretaries can create medications')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get data from request
    name = request.data.get('name')
    description = request.data.get('description', '')
    dosage_form = request.data.get('dosage_form')
    strength = request.data.get('strength')
    manufacturer = request.data.get('manufacturer', '')
    
    # Validate required fields
    if not all([name, dosage_form, strength]):
        return Response({
            'error': _('Please provide all required fields')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the medication
    try:
        medication = Medication(
            name=name,
            description=description,
            dosage_form=dosage_form,
            strength=strength,
            manufacturer=manufacturer
        )
        medication.save()
        
        return Response({
            'success': _('Medication created successfully'),
            'id': medication.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Prescription views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prescription_list(request):
    """Get prescriptions based on user role"""
    user = request.user
    
    # Filter parameters
    status_filter = request.query_params.get('status')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Base query depends on user role
    if user.role == 'doctor':
        queryset = Prescription.objects.filter(doctor=user)
    elif user.role == 'patient':
        try:
            patient = Patient.objects.get(user=user)
            queryset = Prescription.objects.filter(patient=patient)
        except Patient.DoesNotExist:
            return Response({
                'error': _('Patient profile not found')
            }, status=status.HTTP_404_NOT_FOUND)
    elif user.role == 'secretary':
        # Secretaries can see all prescriptions
        queryset = Prescription.objects.all()
    else:
        return Response({
            'error': _('Unauthorized')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if start_date:
        queryset = queryset.filter(prescription_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(prescription_date__lte=end_date)
    
    # Order by date
    prescriptions = queryset.order_by('-prescription_date')
    
    # Format response data
    data = [{
        'id': prescription.id,
        'patient': {
            'id': prescription.patient.id,
            'name': prescription.patient.user.get_full_name()
        },
        'doctor': {
            'id': prescription.doctor.id,
            'name': prescription.doctor.get_full_name()
        },
        'prescription_date': prescription.prescription_date,
        'expiry_date': prescription.expiry_date,
        'diagnosis': prescription.diagnosis,
        'status': prescription.status
    } for prescription in prescriptions]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription(request):
    """Create a new prescription (only for doctors)"""
    user = request.user
    
    # Check permissions: only doctors can create prescriptions
    if user.role != 'doctor':
        return Response({
            'error': _('Only doctors can create prescriptions')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get data from request
    patient_id = request.data.get('patient_id')
    prescription_date = request.data.get('prescription_date', timezone.now().date())
    expiry_date = request.data.get('expiry_date')
    diagnosis = request.data.get('diagnosis')
    notes = request.data.get('notes', '')
    items = request.data.get('items', [])
    
    # Validate required fields
    if not all([patient_id, diagnosis]) or not items:
        return Response({
            'error': _('Please provide all required fields including at least one medication')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the patient
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return Response({
            'error': _('Patient not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the prescription
    try:
        prescription = Prescription(
            patient=patient,
            doctor=user,
            prescription_date=prescription_date,
            expiry_date=expiry_date,
            diagnosis=diagnosis,
            notes=notes,
            status='active'
        )
        prescription.save()
        
        # Create prescription items
        for item_data in items:
            medication_id = item_data.get('medication_id')
            dosage = item_data.get('dosage')
            frequency = item_data.get('frequency')
            duration = item_data.get('duration')
            instructions = item_data.get('instructions')
            
            # Validate required fields for each item
            if not all([medication_id, dosage, frequency, duration, instructions]):
                # Delete the prescription if item validation fails
                prescription.delete()
                return Response({
                    'error': _('Please provide all required fields for each medication')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the medication
            try:
                medication = Medication.objects.get(id=medication_id)
            except Medication.DoesNotExist:
                # Delete the prescription if medication not found
                prescription.delete()
                return Response({
                    'error': _('Medication not found')
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create the prescription item
            prescription_item = PrescriptionItem(
                prescription=prescription,
                medication=medication,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                instructions=instructions
            )
            prescription_item.save()
        
        return Response({
            'success': _('Prescription created successfully'),
            'id': prescription.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def prescription_detail(request, prescription_id):
    """Get or update a specific prescription"""
    user = request.user
    
    # Get the prescription
    try:
        prescription = get_object_or_404(Prescription, id=prescription_id)
    except Prescription.DoesNotExist:
        return Response({
            'error': _('Prescription not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions based on user role
    if user.role == 'patient':
        try:
            patient = Patient.objects.get(user=user)
            if prescription.patient.id != patient.id:
                return Response({
                    'error': _('You do not have permission to access this prescription')
                }, status=status.HTTP_403_FORBIDDEN)
        except Patient.DoesNotExist:
            return Response({
                'error': _('Patient profile not found')
            }, status=status.HTTP_404_NOT_FOUND)
    elif user.role == 'doctor' and prescription.doctor.id != user.id:
        return Response({
            'error': _('You do not have permission to access this prescription')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Handle GET request
    if request.method == 'GET':
        # Get prescription items
        items = PrescriptionItem.objects.filter(prescription=prescription)
        
        # Format prescription items
        items_data = [{
            'id': item.id,
            'medication': {
                'id': item.medication.id,
                'name': item.medication.name,
                'dosage_form': item.medication.dosage_form,
                'strength': item.medication.strength
            },
            'dosage': item.dosage,
            'frequency': item.frequency,
            'duration': item.duration,
            'instructions': item.instructions
        } for item in items]
        
        # Format prescription data
        data = {
            'id': prescription.id,
            'patient': {
                'id': prescription.patient.id,
                'name': prescription.patient.user.get_full_name()
            },
            'doctor': {
                'id': prescription.doctor.id,
                'name': prescription.doctor.get_full_name()
            },
            'prescription_date': prescription.prescription_date,
            'expiry_date': prescription.expiry_date,
            'diagnosis': prescription.diagnosis,
            'notes': prescription.notes,
            'status': prescription.status,
            'items': items_data,
            'created_at': prescription.created_at,
            'updated_at': prescription.updated_at
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
    # Handle PUT request
    elif request.method == 'PUT':
        # Only doctors who created the prescription can update it
        if user.role != 'doctor' or prescription.doctor.id != user.id:
            return Response({
                'error': _('Only the prescribing doctor can update this prescription')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only allow updates if prescription is active
        if prescription.status != 'active':
            return Response({
                'error': _('Cannot update a completed, cancelled, or expired prescription')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update fields based on request data
        if 'status' in request.data:
            prescription.status = request.data['status']
        
        if 'notes' in request.data:
            prescription.notes = request.data['notes']
        
        if 'expiry_date' in request.data:
            prescription.expiry_date = request.data['expiry_date']
        
        # Save the prescription
        try:
            prescription.save()
            return Response({
                'success': _('Prescription updated successfully')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PrescriptionPDFView(APIView):
    def get(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)
        pdf = generate_pdf('prescriptions/prescription.html', {
            'prescription': prescription
        })
        return Response(pdf, content_type='application/pdf')