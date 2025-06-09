from icalendar import Calendar, Event
from datetime import datetime
import uuid

def generate_ical(appointment):
    cal = Calendar()
    # Set required properties for iCalendar
    cal.add('prodid', '-//Cabinet Medical//Appointment Calendar//FR')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    
    event = Event()
    
    # Create a unique identifier for this event
    event['uid'] = str(uuid.uuid4())
    
    # Add appointment details
    patient_name = appointment.patient.user.get_full_name()
    doctor_name = appointment.doctor.get_full_name()
    
    # Set summary/title with patient and doctor names
    event.add('summary', f'Rendez-vous médical avec Dr. {doctor_name}')
    
    # Add start and end times
    event.add('dtstart', appointment.start_time)
    event.add('dtend', appointment.end_time)
    
    # Add creation timestamp
    event.add('dtstamp', datetime.now())
    
    # Add location if available (using clinic name or address)
    event.add('location', 'Cabinet Médical')
    
    # Add description with appointment details
    description = f"""Rendez-vous médical
    
Patient: {patient_name}
Médecin: Dr. {doctor_name}
"""
    
    if appointment.reason:
        description += f"\nMotif: {appointment.reason}"
    
    if appointment.notes:
        description += f"\nNotes: {appointment.notes}"
    
    event.add('description', description)
    
    # Add status based on appointment status
    status_map = {
        'scheduled': 'TENTATIVE',
        'confirmed': 'CONFIRMED',
        'completed': 'CONFIRMED',
        'cancelled': 'CANCELLED',
        'no_show': 'CANCELLED'
    }
    event.add('status', status_map.get(appointment.status, 'TENTATIVE'))
    
    # Add a reminder/alarm (15 minutes before)
    from icalendar import vCalAddress, vText, Alarm
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', f'Rappel: Rendez-vous avec Dr. {doctor_name} dans 15 minutes')
    alarm.add('trigger', '-PT15M')  # 15 minutes before
    event.add_component(alarm)
    
    # Add the event to the calendar
    cal.add_component(event)
    
    return cal.to_ical()