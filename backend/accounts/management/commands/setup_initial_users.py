from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import User
from django.db import transaction
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Sets up initial doctor and secretary users for the system'

    def add_arguments(self, parser):
        parser.add_argument('--doctor-email', type=str, help='Email for the doctor account')
        parser.add_argument('--doctor-password', type=str, help='Password for the doctor account')
        parser.add_argument('--secretary-email', type=str, help='Email for the secretary account')
        parser.add_argument('--secretary-password', type=str, help='Password for the secretary account')
        parser.add_argument('--admin-email', type=str, help='Email for the admin account')
        parser.add_argument('--admin-password', type=str, help='Password for the admin account')

    def handle(self, *args, **options):
        with transaction.atomic():
            # Check if a doctor already exists
            doctor_exists = User.objects.filter(role='doctor').exists()
            if doctor_exists:
                self.stdout.write(self.style.WARNING('A doctor account already exists. Skipping doctor creation.'))
            else:
                # Create doctor
                doctor_email = options.get('doctor_email') or 'doctor@cabinetmedicale.com'
                doctor_password = options.get('doctor_password') or 'DoctorPassword123!'
                
                doctor = User.objects.create(
                    email=doctor_email,
                    password=make_password(doctor_password),
                    first_name='Doctor',
                    last_name='Name',
                    role='doctor',
                    is_active=True,
                    is_staff=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created doctor account: {doctor_email}'))
            
            # Check if a secretary already exists
            secretary_exists = User.objects.filter(role='secretary').exists()
            if secretary_exists:
                self.stdout.write(self.style.WARNING('A secretary account already exists. Skipping secretary creation.'))
            else:
                # Create secretary
                secretary_email = options.get('secretary_email') or 'secretary@cabinetmedicale.com'
                secretary_password = options.get('secretary_password') or 'SecretaryPassword123!'
                
                secretary = User.objects.create(
                    email=secretary_email,
                    password=make_password(secretary_password),
                    first_name='Secretary',
                    last_name='Name',
                    role='secretary',
                    is_active=True,
                    is_staff=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created secretary account: {secretary_email}'))
            
            # Check if an admin already exists
            admin_exists = User.objects.filter(is_superuser=True).exists()
            if admin_exists:
                self.stdout.write(self.style.WARNING('An admin account already exists. Skipping admin creation.'))
            else:
                # Create admin
                admin_email = options.get('admin_email') or 'admin@cabinetmedicale.com'
                admin_password = options.get('admin_password') or 'AdminPassword123!'
                
                admin = User.objects.create(
                    email=admin_email,
                    password=make_password(admin_password),
                    first_name='Admin',
                    last_name='User',
                    role='admin',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created admin account: {admin_email}'))
            
            self.stdout.write(self.style.SUCCESS('Initial user setup complete.'))
