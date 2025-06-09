from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, TimeSlot
from accounts.models import User
from patients.models import Patient
from notifications.services import send_appointment_confirmation, send_appointment_reminder
from accounts.permissions import IsDoctor, IsSecretary, IsPatient, CanManageAppointments
from datetime import datetime, timedelta, date, time, time
from django.core.exceptions import ValidationError
from .calendar import generate_ical

# TimeSlot views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_time_slots(request):
    """Get available time slots for a specific doctor and date range"""
    # Debug: Print the query parameters
    print(f"DEBUG - Time slots query params: {request.query_params}")
    
    # Get parameters from request
    doctor_id = request.query_params.get('doctor_id')
    start_date_str = request.query_params.get('start_date') or request.query_params.get('date')
    end_date_str = request.query_params.get('end_date') or start_date_str
    include_unavailable = request.query_params.get('include_unavailable', 'false').lower() == 'true'
    
    # Validate required fields
    if not doctor_id or not start_date_str:
        return Response({
            'error': _('Please provide doctor_id and date or start_date')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = User.objects.get(id=doctor_id, role='doctor')
    except User.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Parse dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        print(f"DEBUG - Date parsing error: {e}")
        return Response({
            'error': _('Invalid date format. Use YYYY-MM-DD')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Build query for time slots
    query = {
        'doctor': doctor,
        'date__gte': start_date,
        'date__lte': end_date
    }
    
    # Only include available slots if specified
    if not include_unavailable:
        query['is_available'] = True
    
    # Get time slots
    time_slots = TimeSlot.objects.filter(**query).order_by('date', 'start_time')
    
    # Serialize the time slots
    time_slots_data = []
    for slot in time_slots:
        time_slots_data.append({
            'id': slot.id,
            'doctor_id': slot.doctor.id,
            'doctor_name': f"{slot.doctor.first_name} {slot.doctor.last_name}",
            'date': slot.date.strftime('%Y-%m-%d'),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_available': slot.is_available
        })
    
    print(f"DEBUG - Found {len(time_slots_data)} time slots")
    return Response(time_slots_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def create_time_slot(request):
    """Create a new time slot"""
    user = request.user
    
    # Only doctors and secretaries can create time slots
    if user.role not in ['doctor', 'secretary']:
        return Response({
            'error': _('Only doctors and secretaries can create time slots')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get data from request
    doctor_id = request.data.get('doctor_id')
    date_str = request.data.get('date')
    start_time_str = request.data.get('start_time')
    end_time_str = request.data.get('end_time')
    
    # Validate required fields
    if not all([doctor_id, date_str, start_time_str, end_time_str]):
        return Response({
            'error': _('Please provide all required fields')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = User.objects.get(id=doctor_id, role='doctor')
    except User.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Parse date and times
    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        return Response({
            'error': _('Invalid date or time format')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the time slot
    time_slot = TimeSlot(
        doctor=doctor,
        date=slot_date,
        start_time=start_time,
        end_time=end_time,
        is_available=True
    )
    time_slot.save()
    
    return Response({
        'success': _('Time slot created successfully'),
        'id': time_slot.id
    }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def time_slot_detail(request, time_slot_id):
    """Get, update or delete a time slot"""
    user = request.user
    
    # Only doctors and secretaries can manage time slots
    if user.role not in ['doctor', 'secretary']:
        return Response({
            'error': _('Only doctors and secretaries can manage time slots')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get the time slot
    try:
        time_slot = TimeSlot.objects.get(id=time_slot_id)
    except TimeSlot.DoesNotExist:
        return Response({
            'error': _('Time slot not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # GET request - return the time slot details
    if request.method == 'GET':
        time_slot_data = {
            'id': time_slot.id,
            'doctor_id': time_slot.doctor.id,
            'doctor_name': f"{time_slot.doctor.first_name} {time_slot.doctor.last_name}",
            'date': time_slot.date.strftime('%Y-%m-%d'),
            'start_time': time_slot.start_time.strftime('%H:%M'),
            'end_time': time_slot.end_time.strftime('%H:%M'),
            'is_available': time_slot.is_available
        }
        return Response(time_slot_data, status=status.HTTP_200_OK)
    
    # PUT request - update the time slot
    elif request.method == 'PUT':
        # Get data from request
        is_available = request.data.get('is_available')
        
        # Update the time slot
        if is_available is not None:
            time_slot.is_available = is_available
            time_slot.save()
        
        return Response({
            'success': _('Time slot updated successfully')
        }, status=status.HTTP_200_OK)
    
    # DELETE request - delete the time slot
    elif request.method == 'DELETE':
        time_slot.delete()
        return Response({
            'success': _('Time slot deleted successfully')
        }, status=status.HTTP_200_OK)

# Appointment views

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def create_appointment(request):
    """
    Create an appointment
    """
    try:
        # Debug: Print the request data
        print(f"DEBUG - Request data: {request.data}")
        
        # Get data from request
        specific_time = request.data.get('specific_time')
        time_slot_id = request.data.get('time_slot_id')
        date_str = request.data.get('date')
        doctor_id = request.data.get('doctor_id')
        patient_id = request.data.get('patient_id')
        reason = request.data.get('reason')
        notes = request.data.get('notes')
        
        # Debug: Print the extracted data
        print(f"DEBUG - specific_time: {specific_time}, type: {type(specific_time)}")
        print(f"DEBUG - time_slot_id: {time_slot_id}")
        print(f"DEBUG - date_str: {date_str}")
        print(f"DEBUG - doctor_id: {doctor_id}")
        print(f"DEBUG - patient_id: {patient_id}")
        
        # Validate required fields
        if not all([doctor_id, patient_id, reason]) or (not time_slot_id and not specific_time):
            return Response({
                'error': _('Please provide all required fields including either time slot or specific time')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the doctor
        try:
            doctor = User.objects.get(id=doctor_id, role='doctor')
        except User.DoesNotExist:
            return Response({
                'error': _('Doctor not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the patient
        try:
            # First get the user
            patient_user = User.objects.get(id=patient_id, role='patient')
            # Then get the associated Patient object or create it if it doesn't exist
            patient, created = Patient.objects.get_or_create(user=patient_user)
            if created:
                print(f"DEBUG - Created new Patient profile for user {patient_user.id}")
        except User.DoesNotExist:
            return Response({
                'error': _('Patient not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the time slot if provided and valid
        time_slot = None
        if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
            try:
                # Check if this is a default time slot (not from the database)
                if str(time_slot_id).startswith('default-'):
                    print(f"DEBUG - Using default time slot: {time_slot_id}")
                    # For default time slots, we'll rely on specific_time instead
                    # No need to fetch from database or validate
                    pass
                else:
                    # This is a real time slot from the database
                    time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
                    # Verify doctor matches the time slot's doctor
                    if int(doctor_id) != time_slot.doctor.id:
                        return Response({
                            'error': _('Doctor does not match the time slot')
                        }, status=status.HTTP_400_BAD_REQUEST)
            except (TimeSlot.DoesNotExist, ValueError, TypeError) as e:
                print(f"DEBUG - Error fetching time slot: {e}")
                # Only return an error if specific_time is not provided
                if not specific_time:
                    return Response({
                        'error': _('Time slot not found or not available')
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # Create appointment data dictionary
        appointment_data = {
            'patient': patient,
            'doctor': doctor,
            'reason': reason,
            'notes': notes,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time:
            # Ensure specific_time is a string and properly formatted
            specific_time_str = str(specific_time).strip()
            
            try:
                # Check if the time format is valid (HH:MM)
                if ':' not in specific_time_str:
                    return Response({
                        'error': _('Time must be in HH:MM format')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                parts = specific_time_str.split(':')
                if len(parts) != 2:
                    return Response({
                        'error': _('Invalid time format')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                # Parse hour and minute
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                except ValueError:
                    return Response({
                        'error': _('Hour and minute must be numbers')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                # Validate hour and minute ranges
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return Response({
                        'error': _('Invalid hour or minute values')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
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
                    time(hour=hour, minute=minute)
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

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPatient])
def create_appointment_patient(request):
    """
    Create a new appointment specifically for patients
    """
    try:
        # Debug: Print the request data
        print(f"DEBUG - Patient appointment request data: {request.data}")
        
        # Get data from request
        specific_time = request.data.get('specific_time')
        time_slot_id = request.data.get('time_slot_id')
        date_str = request.data.get('date')
        doctor_id = request.data.get('doctor_id')
        reason = request.data.get('reason')
        notes = request.data.get('notes', '')
        
        # Debug: Print the extracted data
        print(f"DEBUG - specific_time: {specific_time}, type: {type(specific_time)}")
        print(f"DEBUG - time_slot_id: {time_slot_id}")
        print(f"DEBUG - date_str: {date_str}")
        print(f"DEBUG - doctor_id: {doctor_id}")
        
        # For patients, use their own ID
        patient_id = request.user.id
        
        # Validate required fields
        if not all([doctor_id, reason]) or (not time_slot_id and not specific_time):
            return Response({
                'error': _('Please provide all required fields including either time slot or specific time')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the doctor
        try:
            doctor = User.objects.get(id=doctor_id, role='doctor')
        except User.DoesNotExist:
            return Response({
                'error': _('Doctor not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the patient (current user)
        try:
            patient = User.objects.get(id=patient_id, role='patient')
        except User.DoesNotExist:
            return Response({
                'error': _('Patient profile not found')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the time slot if provided and valid
        time_slot = None
        if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
            try:
                # Check if this is a default time slot (not from the database)
                if str(time_slot_id).startswith('default-'):
                    print(f"DEBUG - Using default time slot: {time_slot_id}")
                    # For default time slots, we'll rely on specific_time instead
                    # No need to fetch from database or validate
                    pass
                else:
                    # This is a real time slot from the database
                    time_slot = TimeSlot.objects.get(id=time_slot_id, is_available=True)
                    # Verify doctor matches the time slot's doctor
                    if int(doctor_id) != time_slot.doctor.id:
                        return Response({
                            'error': _('Doctor does not match the time slot')
                        }, status=status.HTTP_400_BAD_REQUEST)
            except (TimeSlot.DoesNotExist, ValueError, TypeError) as e:
                print(f"DEBUG - Error fetching time slot: {e}")
                # Only return an error if specific_time is not provided
                if not specific_time:
                    return Response({
                        'error': _('Time slot not found or not available')
                    }, status=status.HTTP_404_NOT_FOUND)
        
        # Create appointment data dictionary
        appointment_data = {
            'patient': patient,
            'doctor': doctor,
            'reason': reason,
            'notes': notes,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time:
            # Ensure specific_time is a string and properly formatted
            specific_time_str = str(specific_time).strip()
            print(f"DEBUG - specific_time_str after conversion: {specific_time_str}")
            
            try:
                # Check if the time format is valid (HH:MM)
                if ':' not in specific_time_str:
                    return Response({
                        'error': _('Time must be in HH:MM format')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                parts = specific_time_str.split(':')
                if len(parts) != 2:
                    return Response({
                        'error': _('Invalid time format')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                # Parse hour and minute
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    print(f"DEBUG - parsed hour: {hour}, minute: {minute}")
                except ValueError as e:
                    print(f"DEBUG - ValueError parsing hour/minute: {e}")
                    return Response({
                        'error': _('Hour and minute must be numbers')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                # Validate hour and minute ranges
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    return Response({
                        'error': _('Invalid hour or minute values')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get the date - either from time_slot or from request data
                if time_slot:
                    appointment_date = time_slot.date
                    print(f"DEBUG - Using time_slot date: {appointment_date}")
                else:
                    # If no time slot, we need the date from the request
                    if not date_str:
                        print("DEBUG - No date_str provided with specific_time")
                        return Response({
                            'error': _('Date is required when using specific time without a time slot')
                        }, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        print(f"DEBUG - Parsed date: {appointment_date}")
                    except ValueError as e:
                        print(f"DEBUG - ValueError parsing date: {e}")
                        return Response({
                            'error': _('Invalid date format. Use YYYY-MM-DD')
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create datetime objects with the specific time
                specific_start_time = datetime.combine(
                    appointment_date, 
                    time(hour=hour, minute=minute)
                )
                print(f"DEBUG - specific_start_time: {specific_start_time}")
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                # Use the specific time
                appointment_data['start_time'] = specific_start_time
                appointment_data['end_time'] = specific_end_time
            except (ValueError, TypeError) as e:
                print(f"DEBUG - Error in specific_time processing: {e}")
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
        
        # Create the appointment
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
        print(f"DEBUG - ValidationError: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"DEBUG - Unexpected exception: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_appointments(request):
    """Get all appointments"""
    user = request.user
    
    # Filter appointments based on user role
    if user.role == 'doctor':
        # Doctors see their own appointments
        appointments = Appointment.objects.filter(doctor=user)
    elif user.role == 'patient':
        # Patients see their own appointments
        appointments = Appointment.objects.filter(patient=user)
    elif user.role == 'secretary':
        # Secretaries see all appointments
        appointments = Appointment.objects.all()
    else:
        return Response({
            'error': _('Invalid user role')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Additional filtering
    doctor_id = request.query_params.get('doctor_id')
    patient_id = request.query_params.get('patient_id')
    date_str = request.query_params.get('date')
    
    if doctor_id:
        try:
            doctor = User.objects.get(id=doctor_id, role='doctor')
            appointments = appointments.filter(doctor=doctor)
        except User.DoesNotExist:
            return Response({
                'error': _('Doctor not found')
            }, status=status.HTTP_404_NOT_FOUND)
    
    if patient_id:
        try:
            patient = User.objects.get(id=patient_id, role='patient')
            appointments = appointments.filter(patient=patient)
        except User.DoesNotExist:
            return Response({
                'error': _('Patient not found')
            }, status=status.HTTP_404_NOT_FOUND)
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(start_time__date=selected_date)
        except ValueError:
            return Response({
                'error': _('Invalid date format. Use YYYY-MM-DD')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Serialize the appointments
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'id': appointment.id,
            'doctor_id': appointment.doctor.id,
            'doctor_name': f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}" if appointment.patient else appointment.patient_name,
            'start_time': appointment.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': appointment.end_time.strftime('%Y-%m-%d %H:%M'),
            'reason': appointment.reason,
            'notes': appointment.notes,
            'status': appointment.status
        })
    
    return Response(appointments_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_appointments(request):
    """Get appointments in calendar format"""
    user = request.user
    
    # Filter appointments based on user role
    if user.role == 'doctor':
        # Doctors see their own appointments
        appointments = Appointment.objects.filter(doctor=user)
    elif user.role == 'patient':
        # Patients see their own appointments
        appointments = Appointment.objects.filter(patient=user)
    elif user.role == 'secretary':
        # Secretaries see all appointments
        appointments = Appointment.objects.all()
    else:
        return Response({
            'error': _('Invalid user role')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Format appointments for calendar
    calendar_events = []
    for appointment in appointments:
        patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else appointment.patient_name
        doctor_name = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
        
        calendar_events.append({
            'id': appointment.id,
            'title': f"{patient_name} - {appointment.reason}",
            'start': appointment.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': appointment.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'extendedProps': {
                'doctor_id': appointment.doctor.id,
                'doctor_name': doctor_name,
                'patient_id': appointment.patient.id if appointment.patient else None,
                'patient_name': patient_name,
                'reason': appointment.reason,
                'notes': appointment.notes,
                'status': appointment.status
            }
        })
    
    return Response(calendar_events, status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def appointment_detail(request, appointment_id):
    """Get, update or delete an appointment"""
    user = request.user
    
    # Get the appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return Response({
            'error': _('Appointment not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions based on user role
    if user.role == 'doctor' and appointment.doctor.id != user.id:
        return Response({
            'error': _('You can only access your own appointments')
        }, status=status.HTTP_403_FORBIDDEN)
    elif user.role == 'patient' and (not appointment.patient or appointment.patient.id != user.id):
        return Response({
            'error': _('You can only access your own appointments')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # GET request - return the appointment details
    if request.method == 'GET':
        appointment_data = {
            'id': appointment.id,
            'doctor_id': appointment.doctor.id,
            'doctor_name': f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}" if appointment.patient else appointment.patient_name,
            'start_time': appointment.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': appointment.end_time.strftime('%Y-%m-%d %H:%M'),
            'reason': appointment.reason,
            'notes': appointment.notes,
            'status': appointment.status
        }
        return Response(appointment_data, status=status.HTTP_200_OK)
    
    # PUT request - update the appointment
    elif request.method == 'PUT':
        # Only doctors and secretaries can update appointments
        if user.role not in ['doctor', 'secretary']:
            return Response({
                'error': _('Only doctors and secretaries can update appointments')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get data from request
        status_value = request.data.get('status')
        notes = request.data.get('notes')
        
        # Update the appointment
        if status_value:
            appointment.status = status_value
        if notes:
            appointment.notes = notes
        
        appointment.save()
        
        return Response({
            'success': _('Appointment updated successfully')
        }, status=status.HTTP_200_OK)
    
    # DELETE request - delete the appointment
    elif request.method == 'DELETE':
        # Only doctors and secretaries can delete appointments
        if user.role not in ['doctor', 'secretary']:
            return Response({
                'error': _('Only doctors and secretaries can delete appointments')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # If there's a time slot associated with this appointment, mark it as available again
        if hasattr(appointment, 'time_slot') and appointment.time_slot:
            time_slot = appointment.time_slot
            time_slot.is_available = True
            time_slot.save()
        
        appointment.delete()
        
        return Response({
            'success': _('Appointment deleted successfully')
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_appointment_ical(request, appointment_id):
    """Download appointment as iCalendar file"""
    user = request.user
    
    # Get the appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return Response({
            'error': _('Appointment not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions based on user role
    if user.role == 'doctor' and appointment.doctor.id != user.id:
        return Response({
            'error': _('You can only access your own appointments')
        }, status=status.HTTP_403_FORBIDDEN)
    elif user.role == 'patient' and (not appointment.patient or appointment.patient.id != user.id):
        return Response({
            'error': _('You can only access your own appointments')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Generate iCalendar file
    ical_content = generate_ical(appointment)
    
    # Create response with iCalendar file
    response = HttpResponse(ical_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.ics"'
    
    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def create_appointment(request):
    """Create a new appointment (for all user roles)"""
    user = request.user
    
    # Debug logging
    print(f"DEBUG - Request data: {request.data}")
    
    # Get data from request
    specific_time = request.data.get('specific_time')
    time_slot_id = request.data.get('time_slot_id')
    date_str = request.data.get('date')
    doctor_id = request.data.get('doctor_id')
    patient_id = request.data.get('patient_id')
    reason = request.data.get('reason')
    notes = request.data.get('notes', '')
    
    print(f"DEBUG - specific_time: {specific_time}, type: {type(specific_time)}")
    print(f"DEBUG - time_slot_id: {time_slot_id}")
    print(f"DEBUG - date_str: {date_str}")
    print(f"DEBUG - doctor_id: {doctor_id}")
    print(f"DEBUG - patient_id: {patient_id}")
    
    # Validate required fields
    if not all([doctor_id, reason]) or (not time_slot_id and not specific_time):
        return Response({
            'error': _('Please provide doctor, time slot or specific time, and reason')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = User.objects.get(id=doctor_id, role='doctor')
    except User.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the patient
    try:
        # First get the user
        patient_user = User.objects.get(id=patient_id, role='patient')
        # Then get the associated Patient object or create it if it doesn't exist
        patient, created = Patient.objects.get_or_create(user=patient_user)
        if created:
            print(f"DEBUG - Created new Patient profile for user {patient_user.id}")
    except User.DoesNotExist:
        return Response({
            'error': _('Patient not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the time slot if provided
    time_slot = None
    if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
        # Handle default time slots (client-side generated)
        if isinstance(time_slot_id, str) and time_slot_id.startswith('default-'):
            # This is a client-side generated time slot, not stored in the database
            # We'll use specific_time and date instead
            pass
        else:
            try:
                time_slot = TimeSlot.objects.get(id=time_slot_id)
                if not time_slot.is_available:
                    return Response({
                        'error': _('Time slot is no longer available')
                    }, status=status.HTTP_400_BAD_REQUEST)
            except TimeSlot.DoesNotExist:
                return Response({
                    'error': _('Time slot not found')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the appointment
    try:
        # Create appointment data
        appointment_data = {
            'doctor': doctor,
            'patient': patient,
            'reason': reason,
            'notes': notes,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time:
            try:
                # Parse the specific time (HH:MM)
                specific_time_str = str(specific_time)
                
                # Validate time format
                if ':' not in specific_time_str:
                    return Response({
                        'error': _('Invalid time format. Use HH:MM')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                parts = specific_time_str.split(':')
                if len(parts) != 2:
                    return Response({
                        'error': _('Invalid time format. Use HH:MM')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                except ValueError:
                    return Response({
                        'error': _('Invalid time format. Hours and minutes must be numbers')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validate hour and minute
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    return Response({
                        'error': _('Invalid time. Hours must be 0-23 and minutes 0-59')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get the date
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
                specific_start_time = datetime.combine(appointment_date, time(hour=hour, minute=minute))
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                # Use the specific time
                appointment_data['start_time'] = specific_start_time
                appointment_data['end_time'] = specific_end_time
                
            except Exception as e:
                print(f"Error parsing specific time: {str(e)}")
                return Response({
                    'error': _('Error processing time: ') + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        elif time_slot:
            # Use the time slot's time
            appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
            appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
        else:
            return Response({
                'error': _('Either time slot or specific time with date must be provided')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and save the appointment
        appointment = Appointment(**appointment_data)
        appointment.save()
        
        # Mark time slot as unavailable if we used one from the database
        if time_slot and not isinstance(time_slot_id, str):
            time_slot.is_available = False
            time_slot.save()
        
        # Send appointment confirmation
        try:
            notification_result = send_appointment_confirmation(appointment)
        except Exception as e:
            notification_result = {'error': str(e)}
            print(f"Error sending notification: {str(e)}")
        
        return Response({
            'success': _('Appointment scheduled successfully'),
            'id': appointment.id,
            'notifications': notification_result
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Error creating appointment: {str(e)}")
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
    specific_time = request.data.get('specific_time')
    date_str = request.data.get('date')
    reason = request.data.get('reason')
    notes = request.data.get('notes', '')
    
    # Validate required fields
    if not all([doctor_id, reason]) or (not time_slot_id and not specific_time):
        return Response({
            'error': _('Please provide doctor, time slot or specific time, and reason')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the doctor
    try:
        doctor = User.objects.get(id=doctor_id, role='doctor')
    except User.DoesNotExist:
        return Response({
            'error': _('Doctor not found')
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get the patient (the current user)
    patient_user = request.user
    # Get the associated Patient object or create it if it doesn't exist
    patient, created = Patient.objects.get_or_create(user=patient_user)
    if created:
        print(f"DEBUG - Created new Patient profile for user {patient_user.id}")
    
    # Get the time slot if provided
    time_slot = None
    if time_slot_id and str(time_slot_id).lower() not in ['null', 'nan', 'undefined', '']:
        # Handle default time slots (client-side generated)
        if isinstance(time_slot_id, str) and time_slot_id.startswith('default-'):
            # This is a client-side generated time slot, not stored in the database
            # We'll use specific_time and date instead
            pass
        else:
            try:
                time_slot = TimeSlot.objects.get(id=time_slot_id)
                if not time_slot.is_available:
                    return Response({
                        'error': _('Time slot is no longer available')
                    }, status=status.HTTP_400_BAD_REQUEST)
            except TimeSlot.DoesNotExist:
                return Response({
                    'error': _('Time slot not found')
                }, status=status.HTTP_404_NOT_FOUND)
    
    # Create the appointment using the same logic as create_appointment
    try:
        # Create appointment data
        appointment_data = {
            'doctor': doctor,
            'patient': patient,
            'reason': reason,
            'notes': notes,
            'status': 'scheduled'
        }
        
        # Handle time based on what was provided
        if specific_time:
            try:
                # Parse the specific time (HH:MM)
                specific_time_str = str(specific_time)
                
                # Validate time format
                if ':' not in specific_time_str:
                    return Response({
                        'error': _('Invalid time format. Use HH:MM')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                parts = specific_time_str.split(':')
                if len(parts) != 2:
                    return Response({
                        'error': _('Invalid time format. Use HH:MM')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    hour = int(parts[0])
                    minute = int(parts[1])
                except ValueError:
                    return Response({
                        'error': _('Invalid time format. Hours and minutes must be numbers')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validate hour and minute
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    return Response({
                        'error': _('Invalid time. Hours must be 0-23 and minutes 0-59')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get the date
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
                specific_start_time = datetime.combine(appointment_date, time(hour=hour, minute=minute))
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                # Use the specific time
                appointment_data['start_time'] = specific_start_time
                appointment_data['end_time'] = specific_end_time
                
            except Exception as e:
                print(f"Error parsing specific time: {str(e)}")
                return Response({
                    'error': _('Error processing time: ') + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        elif time_slot:
            # Use the time slot's time
            appointment_data['start_time'] = datetime.combine(time_slot.date, time_slot.start_time)
            appointment_data['end_time'] = datetime.combine(time_slot.date, time_slot.end_time)
        else:
            return Response({
                'error': _('Either time slot or specific time with date must be provided')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and save the appointment
        appointment = Appointment(**appointment_data)
        appointment.save()
        
        # Mark time slot as unavailable if we used one from the database
        if time_slot and not isinstance(time_slot_id, str):
            time_slot.is_available = False
            time_slot.save()
        
        # Send appointment confirmation
        try:
            notification_result = send_appointment_confirmation(appointment)
        except Exception as e:
            notification_result = {'error': str(e)}
            print(f"Error sending notification: {str(e)}")
        
        return Response({
            'success': _('Appointment scheduled successfully'),
            'id': appointment.id,
            'notifications': notification_result
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"Error creating appointment: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
