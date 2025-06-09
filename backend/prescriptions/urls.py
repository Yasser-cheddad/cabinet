from django.urls import path
from . import views

urlpatterns = [
    # Medication endpoints
    path('medications/', views.medication_list, name='medication_list'),
    path('medications/create/', views.create_medication, name='create_medication'),
    
    # Prescription endpoints
    path('', views.prescription_list, name='prescription_list'),
    path('create/', views.create_prescription, name='create_prescription'),
    path('<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('<int:pk>/pdf/', views.PrescriptionPDFView.as_view(), name='prescription_pdf'),
]
