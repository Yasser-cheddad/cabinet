# Generated by Django 5.2 on 2025-06-02 20:26

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0002_alter_patient_blood_type_alter_patient_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Medication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Medication Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('dosage_form', models.CharField(max_length=100, verbose_name='Dosage Form')),
                ('strength', models.CharField(max_length=100, verbose_name='Strength')),
                ('manufacturer', models.CharField(blank=True, max_length=255, verbose_name='Manufacturer')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Medication',
                'verbose_name_plural': 'Medications',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prescription_date', models.DateField(default=django.utils.timezone.now, verbose_name='Prescription Date')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='Expiry Date')),
                ('diagnosis', models.TextField(verbose_name='Diagnosis')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('status', models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='active', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(limit_choices_to={'role': 'doctor'}, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_prescriptions', to=settings.AUTH_USER_MODEL, verbose_name='Doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Prescription',
                'verbose_name_plural': 'Prescriptions',
                'ordering': ['-prescription_date'],
            },
        ),
        migrations.CreateModel(
            name='PrescriptionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=100, verbose_name='Dosage')),
                ('frequency', models.CharField(max_length=100, verbose_name='Frequency')),
                ('duration', models.CharField(max_length=100, verbose_name='Duration')),
                ('instructions', models.TextField(verbose_name='Instructions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('medication', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='prescription_items', to='prescriptions.medication', verbose_name='Medication')),
                ('prescription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='prescriptions.prescription', verbose_name='Prescription')),
            ],
            options={
                'verbose_name': 'Prescription Item',
                'verbose_name_plural': 'Prescription Items',
            },
        ),
    ]
