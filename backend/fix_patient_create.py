# This script will fix the patient profile issue in views.py
import re

# Path to the views.py file
views_path = 'appointments/views.py'

# Read the file content
with open(views_path, 'r') as f:
    content = f.read()

# Fix the patient assignment in create_appointment to create a Patient if it doesn't exist
old_code = """        # Get the patient
        try:
            # First get the user
            patient_user = User.objects.get(id=patient_id, role='patient')
            # Then get the associated Patient object
            try:
                patient = Patient.objects.get(user=patient_user)
            except Patient.DoesNotExist:
                return Response({
                    'error': _('Patient profile not found')
                }, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({
                'error': _('Patient not found')
            }, status=status.HTTP_404_NOT_FOUND)"""

new_code = """        # Get the patient
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
            }, status=status.HTTP_404_NOT_FOUND)"""

content = content.replace(old_code, new_code)

# Fix the patient assignment in create_appointment_patient to create a Patient if it doesn't exist
old_code_patient = """        # Get the patient (the current user)
        patient_user = request.user
        # Get the associated Patient object
        try:
            patient = Patient.objects.get(user=patient_user)
        except Patient.DoesNotExist:
            return Response({
                'error': _('Patient profile not found')
            }, status=status.HTTP_404_NOT_FOUND)"""

new_code_patient = """        # Get the patient (the current user)
        patient_user = request.user
        # Get the associated Patient object or create it if it doesn't exist
        patient, created = Patient.objects.get_or_create(user=patient_user)
        if created:
            print(f"DEBUG - Created new Patient profile for user {patient_user.id}")"""

content = content.replace(old_code_patient, new_code_patient)

# Write the updated content back to the file
with open(views_path, 'w') as f:
    f.write(content)

print("Fixed patient profile creation in views.py")
