from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
import logging
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import User
from .models import Notification
from .utils import send_notification

logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Email configuration
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@cabinetmedicale.com')


def send_sms_notification(to_number, message):
    """
    Send SMS notification using Twilio
    
    Args:
        to_number (str): Recipient phone number in E.164 format (+country_code phone_number)
        message (str): SMS message content
        
    Returns:
        dict: Status and message ID if successful, error details if failed
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.error("Twilio credentials not configured")
        return {
            'success': False,
            'error': 'Twilio credentials not configured'
        }
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        logger.info(f"SMS sent successfully to {to_number}, SID: {message.sid}")
        return {
            'success': True,
            'message_id': message.sid
        }
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def send_email_notification(to_email, subject, message_content):
    """
    Send email notification using Django's email backend
    
    Args:
        to_email (str or list): Recipient email address(es)
        subject (str): Email subject
        message_content (str): Plain text content for the email
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Send email with plain text content
        send_mail(
            subject=subject,
            message=message_content,  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email] if isinstance(to_email, str) else to_email,
            fail_silently=False
        )
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_appointment_confirmation(appointment):
    """
    Send appointment confirmation via both email and SMS
    
    Args:
        appointment: Appointment instance
        
    Returns:
        dict: Status of both email and SMS notifications
    """
    # Check if patient is a Patient model or User model
    if hasattr(appointment.patient, 'user'):
        # It's a Patient model
        patient = appointment.patient.user
    else:
        # It's a User model
        patient = appointment.patient
        
    # Check if doctor is a Doctor model or User model
    if hasattr(appointment.doctor, 'user'):
        # It's a Doctor model
        doctor = appointment.doctor.user
    else:
        # It's a User model
        doctor = appointment.doctor
    
    # Context for email template
    context = {
        'patient_name': patient.get_full_name(),
        'doctor_name': doctor.get_full_name(),
        'appointment_date': appointment.date,
        'appointment_time': appointment.time,
        'appointment_type': appointment.get_appointment_type_display(),
        'clinic_address': settings.CLINIC_ADDRESS,
        'clinic_phone': settings.CLINIC_PHONE,
    }
    
    # Prepare email content
    email_content = _(
        f"Hello {patient.get_full_name()},\n\n"
        f"Your appointment with Dr. {doctor.get_full_name()} is confirmed for {appointment.date} at {appointment.time}.\n"
        f"Appointment type: {appointment.get_appointment_type_display()}\n\n"
        f"Clinic address: {settings.CLINIC_ADDRESS}\n"
        f"Clinic phone: {settings.CLINIC_PHONE}\n\n"
        f"Thank you for choosing our medical cabinet.\n"
    )
    
    # Send email notification
    email_status = send_email_notification(
        to_email=patient.email,
        subject=_("Appointment Confirmation"),
        message_content=email_content
    )
    
    # Send SMS notification if phone number is available
    sms_status = None
    if patient.phone_number:
        # Format phone number to E.164 format if not already
        phone = patient.phone_number
        if not phone.startswith('+'):
            # Add country code (adjust as needed)
            phone = f"+212{phone}" if phone.startswith('0') else f"+212{phone}"
        
        # SMS message
        sms_message = _(
            f"Hello {patient.get_full_name()}, "
            f"Your appointment with Dr. {doctor.get_full_name()} "
            f"is confirmed for {appointment.date} at {appointment.time}. "
            f"Please call {settings.CLINIC_PHONE} if you need to reschedule."
        )
        
        sms_status = send_sms_notification(phone, sms_message)
    
    return {
        'email': email_status,
        'sms': sms_status
    }


def send_appointment_reminder(appointment):
    """
    Send appointment reminder via both email and SMS
    
    Args:
        appointment: Appointment instance
        
    Returns:
        dict: Status of both email and SMS notifications
    """
    # Check if patient is a Patient model or User model
    if hasattr(appointment.patient, 'user'):
        # It's a Patient model
        patient = appointment.patient.user
    else:
        # It's a User model
        patient = appointment.patient
        
    # Check if doctor is a Doctor model or User model
    if hasattr(appointment.doctor, 'user'):
        # It's a Doctor model
        doctor = appointment.doctor.user
    else:
        # It's a User model
        doctor = appointment.doctor
    
    # Context for email template
    context = {
        'patient_name': patient.get_full_name(),
        'doctor_name': doctor.get_full_name(),
        'appointment_date': appointment.date,
        'appointment_time': appointment.time,
        'appointment_type': appointment.get_appointment_type_display(),
        'clinic_address': settings.CLINIC_ADDRESS,
        'clinic_phone': settings.CLINIC_PHONE,
    }
    
    # Prepare email content
    email_content = _(
        f"Hello {patient.get_full_name()},\n\n"
        f"This is a reminder for your appointment with Dr. {doctor.get_full_name()} tomorrow at {appointment.time}.\n"
        f"Appointment type: {appointment.get_appointment_type_display()}\n\n"
        f"Clinic address: {settings.CLINIC_ADDRESS}\n"
        f"Clinic phone: {settings.CLINIC_PHONE}\n\n"
        f"Please call us if you need to reschedule.\n"
    )
    
    # Send email notification
    email_status = send_email_notification(
        to_email=patient.email,
        subject=_("Appointment Reminder"),
        message_content=email_content
    )
    
    # Send SMS notification if phone number is available
    sms_status = None
    if patient.phone_number:
        # Format phone number to E.164 format if not already
        phone = patient.phone_number
        if not phone.startswith('+'):
            # Add country code (adjust as needed)
            phone = f"+212{phone}" if phone.startswith('0') else f"+212{phone}"
        
        # SMS message
        sms_message = _(
            f"Reminder: Your appointment with Dr. {doctor.get_full_name()} "
            f"is tomorrow at {appointment.time}. "
            f"Please call {settings.CLINIC_PHONE} if you need to reschedule."
        )
        
        sms_status = send_sms_notification(phone, sms_message)
    
    return {
        'email': email_status,
        'sms': sms_status
    }

def send_notification_service(recipient_id, message, notification_type):
    """
    Service to handle the creation and sending of a custom notification.
    """
    try:
        recipient = User.objects.get(id=recipient_id)
    except ObjectDoesNotExist:
        raise ValueError("Recipient not found.")

    # Create the notification instance
    notification = Notification.objects.create(
        user=recipient,
        title="New Message from Staff",
        message=message,
        notification_type='message' # Or derive from a parameter if needed
    )

    # Use the existing utility to send the notification
    send_notification(
        user_id=recipient.id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type,
        # Pass notification_id to be used in WebSocket message
        extra_data={'notification_id': notification.id}
    )

    return notification
