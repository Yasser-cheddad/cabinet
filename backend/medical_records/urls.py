from django.urls import path, include
from rest_framework import routers
from .views import (
    MedicalRecordViewSet,
    MedicalNoteViewSet,
    PrescriptionViewSet,
    MedicalFileViewSet
)

router = routers.SimpleRouter()
router.register(r'records', MedicalRecordViewSet, basename='medical-record')

# Flat URL patterns instead of nested routers
urlpatterns = [
    path('', include(router.urls)),
    path('records/<int:medical_record_pk>/notes/', MedicalNoteViewSet.as_view({'get': 'list', 'post': 'create'}), name='medical-note-list'),
    path('records/<int:medical_record_pk>/notes/<int:pk>/', MedicalNoteViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='medical-note-detail'),
    path('records/<int:medical_record_pk>/files/', MedicalFileViewSet.as_view({'get': 'list', 'post': 'create'}), name='medical-file-list'),
    path('records/<int:medical_record_pk>/files/<int:pk>/', MedicalFileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='medical-file-detail'),
    path('records/<int:medical_record_pk>/notes/<int:medical_note_pk>/prescriptions/', PrescriptionViewSet.as_view({'get': 'list', 'post': 'create'}), name='prescription-list'),
    path('records/<int:medical_record_pk>/notes/<int:medical_note_pk>/prescriptions/<int:pk>/', PrescriptionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='prescription-detail'),
]
