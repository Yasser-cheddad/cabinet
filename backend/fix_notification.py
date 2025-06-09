# This script will fix the notification service issue
import re

# Path to the services.py file
services_path = 'notifications/services.py'

# Read the file content
with open(services_path, 'r') as f:
    content = f.read()

# Fix the patient and doctor access in send_appointment_confirmation
old_code = """    patient = appointment.patient.user
    doctor = appointment.doctor.user"""

new_code = """    # Check if patient is a Patient model or User model
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
        doctor = appointment.doctor"""

content = content.replace(old_code, new_code)

# Write the updated content back to the file
with open(services_path, 'w') as f:
    f.write(content)

print("Fixed notification service issue")
