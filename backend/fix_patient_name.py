# This script will fix the patient name access in views.py
import re

# Path to the views.py file
views_path = 'appointments/views.py'

# Read the file content
with open(views_path, 'r') as f:
    content = f.read()

# Fix the patient name access in get_appointments
old_code = """            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else appointment.patient_name,"""

new_code = """            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}" if appointment.patient else appointment.patient_name,"""

content = content.replace(old_code, new_code)

# Fix the same issue in appointment_detail function
old_code_detail = """            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else appointment.patient_name,"""

new_code_detail = """            'patient_id': appointment.patient.id if appointment.patient else None,
            'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}" if appointment.patient else appointment.patient_name,"""

content = content.replace(old_code_detail, new_code_detail)

# Write the updated content back to the file
with open(views_path, 'w') as f:
    f.write(content)

print("Fixed patient name access in views.py")
