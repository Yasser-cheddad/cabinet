# This script will add the create_appointment function to views.py
import re

# Path to the views.py file
views_path = 'appointments/views.py'

# Read the file content
with open(views_path, 'r') as f:
    content = f.read()

# Create the create_appointment function with our fixes
create_appointment_function = """
@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageAppointments])
def create_appointment(request):
    \"\"\"Create a new appointment (for all user roles)\"\"\"
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
    \"\"\"Create a new appointment specifically for patients\"\"\"
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
"""

# Add the create_appointment function to the views.py file
content += create_appointment_function

# Write the updated content back to the file
with open(views_path, 'w') as f:
    f.write(content)

print("Added create_appointment function to views.py")
