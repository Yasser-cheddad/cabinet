from django.core.management.base import BaseCommand
from appointments.models import DoctorAvailability, TimeSlot
from accounts.models import Doctor
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates sample time slots for doctors'

    def handle(self, *args, **options):
        # Get or create sample doctors
        doctors = Doctor.objects.all()
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('No doctors found. Create doctors first.'))
            return

        # Clear existing data
        DoctorAvailability.objects.all().delete()
        TimeSlot.objects.all().delete()

        # Create sample availability for next 7 days
        for doctor in doctors:
            for day in range(7):
                date = datetime.now().date() + timedelta(days=day)
                
                # Create doctor availability
                availability = DoctorAvailability.objects.create(
                    doctor=doctor,
                    date=date,
                    start_time='09:00',
                    end_time='17:00',
                    is_available=True
                )

                # Create 15-minute time slots
                start = datetime.combine(date, datetime.strptime('09:00', '%H:%M').time())
                end = datetime.combine(date, datetime.strptime('17:00', '%H:%M').time())
                
                current = start
                while current < end:
                    TimeSlot.objects.create(
                        availability=availability,
                        start_time=current.time(),
                        end_time=(current + timedelta(minutes=15)).time(),
                        is_booked=random.choice([True, False])
                    )
                    current += timedelta(minutes=15)

        self.stdout.write(self.style.SUCCESS('Successfully created sample time slots'))