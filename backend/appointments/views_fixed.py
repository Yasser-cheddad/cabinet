from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone

from accounts.models import Doctor, Patient
from appointments.models import Appointment, TimeSlot
from appointments.permissions import CanManageAppointments
from notifications.utils import send_appointment_confirmation

# Import other required modules and functions here...

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def create_appointment(request):
    """Create a new appointment (for all user roles)"""
    user = request.user
    
    # Get data from request
    doctor_id = request.data.get('doctor_id')
    time_slot_id = request.data.get('time_slot_id')
    reason = request.data.get('reason')
    specific_time = request.data.get('specific_time')  # Get specific time from frontend
    date_str = request.data.get('date')  # Get date from frontend when using specific time
    
    # Handle patient_id differently based on user role
    if user.role == 'patient':
        # For patients, use their own ID
        patient_id = user.id
        patient_name = None
        
        # Try to get the patient profile
        try:
            patient = Patient.objects.get(user_id=patient_id)
        except Patient.DoesNotExist:
            return Response({
                'error': _('Patient profile not found')
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # For doctors and secretaries, get patient_id from request
        patient_id = request.data.get('patient_id')
        patient_name = request.data.get('patient_name')
    
    # Validate required fields
    # If secretary is creating with patient_name, don't require patient_id
    # Make time_slot_id optional if specific_time is provided
    if user.role == 'secretary' and patient_name:
        if not all([doctor_id, reason]) or (not time_slot_id and not specific_time):
            return Response({
                'error': _('Please provide doctor, time slot or specific time, and reason')
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        if not all([patient_id, doctor_id, reason]) or (not time_slot_id and not specific_time):
            return Response({
                'error': _('Please provide all required fields including either time slot or specific time')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the time slot if provided and valid
    time_slot = None
    if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
        try:
            time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
            # Verify doctor matches the time slot's doctor
            if int(doctor_id) != time_slot.doctor.id:
                return Response({
                    'error': _('Doctor does not match the time slot')
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TimeSlot.DoesNotExist, ValueError, TypeError):
            # Only return an error if specific_time is not provided
            if not specific_time:
                return Response({
                    'error': _('Time slot not found or not available')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the patient if patient_id is provided
    patient = None
    if patient_id:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({
                'error': _('Patient not found')
            }, status=status.HTTP_404_NOT_FOUND)
    # For secretary creating with patient_name, we don't need a Patient object
    
    # Create the appointment
    try:
        # Create appointment data
        appointment_data = {
            'doctor': doctor,
            'reason': reason,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time and len(specific_time.split(':')) == 2:
            try:
                # Parse the specific time (HH:MM)
                hour, minute = map(int, specific_time.split(':'))
                
                # Get the date - either from time_slot or from request data
                if time_slot:
                    appointment_date = time_slot.date
                else:
                    # If no time slot, we need the date from the request
                    if not date_str:
                        return Response({
                            'error': _('Date is required when using specific time without a time slot')
                        }, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return Response({
                            'error': _('Invalid date format. Use YYYY-MM-DD')
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create datetime objects with the specific time
                specific_start_time = datetime.combine(
                    appointment_date, 
                    timezone.datetime.time(hour=hour, minute=minute)
                )
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                # Use the specific time
                appointment_data['start_time'] = specific_start_time
                appointment_data['end_time'] = specific_end_time
            except (ValueError, TypeError) as e:
                print(f"Error parsing specific time: {e}")
                if time_slot:
                    # Fall back to time slot's time if there's an error and we have a time slot
                    appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
                    appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
                else:
                    return Response({
                        'error': _('Invalid time format')
                    }, status=status.HTTP_400_BAD_REQUEST)
        elif time_slot:
            # Use the time slot's time if no specific time is provided but we have a time slot
            appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
            appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
        else:
            return Response({
                'error': _('Either time slot or specific time with date must be provided')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add patient or patient_name based on what was provided
        if patient:
            appointment_data['patient'] = patient
        if patient_name and user.role == 'secretary':
            appointment_data['patient_name'] = patient_name
            
        # If secretary is creating with patient_name only, we need a patient
        if not patient and patient_name and user.role == 'secretary':
            # This is a simplified approach - in a real app, you might want to
            # create a new patient record or handle this differently
            return Response({
                'error': _('Patient selection is required')
            }, status=status.HTTP_400_BAD_REQUEST)
            
        appointment = Appointment(**appointment_data)
        appointment.save()
        
        # Mark time slot as unavailable if we used one
        if time_slot:
            time_slot.is_available = False
            time_slot.save()
        
        # Send appointment confirmation via SMS and email
        notification_result = send_appointment_confirmation(appointment)
        
        return Response({
            'success': _('Appointment scheduled successfully'),
            'id': appointment.id,
            'notifications': {
                'email_sent': notification_result.get('email', False),
                'sms_sent': notification_result.get('sms', {}).get('success', False) if notification_result.get('sms') else False
            }
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment_patient(request):
    """Create a new appointment specifically for patients"""
    user = request.user
    
    # Ensure the user is a patient
    if user.role != 'patient':
        return Response({
            'error': _('This endpoint is only for patients')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get data from request
    doctor_id = request.data.get('doctor_id')
    time_slot_id = request.data.get('time_slot_id')
    reason = request.data.get('reason')
    notes = request.data.get('notes', '')
    specific_time = request.data.get('specific_time')  # Get specific time from frontend
    date_str = request.data.get('date')  # Get date from frontend when using specific time
    
    # Get the patient profile
    try:
        patient = Patient.objects.get(user=user)
    except Patient.DoesNotExist:
        return Response({
            'error': _('Patient profile not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate required fields
    # Make time_slot_id optional if specific_time is provided
    if not all([doctor_id, reason]) or (not time_slot_id and not specific_time):
        return Response({
            'error': _('Please provide doctor, time slot or specific time, and reason')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the time slot if provided and valid
    time_slot = None
    if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
        try:
            time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
            # Verify doctor matches the time slot's doctor
            if int(doctor_id) != time_slot.doctor.id:
                return Response({
                    'error': _('Doctor does not match the time slot')
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TimeSlot.DoesNotExist, ValueError, TypeError):
            # Only return an error if specific_time is not provided
            if not specific_time:
                return Response({
                    'error': _('Time slot not found or not available')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the appointment
    try:
        # Create appointment data
        appointment_data = {
            'patient': patient,
            'doctor': doctor,
            'reason': reason,
            'notes': notes,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time and len(specific_time.split(':')) == 2:
            try:
                # Parse the specific time (HH:MM)
                hour, minute = map(int, specific_time.split(':'))
                
                # Get the date - either from time_slot or from request data
                if time_slot:
                    appointment_date = time_slot.date
                else:
                    # If no time slot, we need the date from the request
                    if not date_str:
                        return Response({
                            'error': _('Date is required when using specific time without a time slot')
                        }, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return Response({
                            'error': _('Invalid date format. Use YYYY-MM-DD')
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create datetime objects with the specific time
                specific_start_time = datetime.combine(
                    appointment_date, 
                    timezone.datetime.time(hour=hour, minute=minute)
                )
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                # Use the specific time
                appointment_data['start_time'] = specific_start_time
                appointment_data['end_time'] = specific_end_time
            except (ValueError, TypeError) as e:
                print(f"Error parsing specific time: {e}")
                if time_slot:
                    # Fall back to time slot's time if there's an error and we have a time slot
                    appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
                    appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
                else:
                    return Response({
                        'error': _('Invalid time format')
                    }, status=status.HTTP_400_BAD_REQUEST)
        elif time_slot:
            # Use the time slot's time if no specific time is provided but we have a time slot
            appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
            appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
        else:
            return Response({
                'error': _('Either time slot or specific time with date must be provided')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment = Appointment(**appointment_data)
        appointment.save()
        
        # Mark time slot as unavailable if we used one
        if time_slot:
            time_slot.is_available = False
            time_slot.save()
        
        # Send appointment confirmation via SMS and email
        notification_result = send_appointment_confirmation(appointment)
        
        return Response({
            'success': _('Appointment scheduled successfully'),
            'id': appointment.id,
            'notifications': {
                'email_sent': notification_result.get('email', False),
                'sms_sent': notification_result.get('sms', {}).get('success', False) if notification_result.get('sms') else False
            }
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Keep all other existing functions from the original views.py file
