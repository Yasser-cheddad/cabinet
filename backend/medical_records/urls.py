from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    MedicalRecordViewSet,
    MedicalNoteViewSet,
    PrescriptionViewSet,
    MedicalFileViewSet
)

router = routers.SimpleRouter()
router.register(r'records', MedicalRecordViewSet, basename='medical-record')

records_router = routers.NestedSimpleRouter(router, r'records', lookup='medical_record')
records_router.register(r'notes', MedicalNoteViewSet, basename='medical-note')
records_router.register(r'files', MedicalFileViewSet, basename='medical-file')

notes_router = routers.NestedSimpleRouter(records_router, r'notes', lookup='medical_note')
notes_router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(records_router.urls)),
    path('', include(notes_router.urls)),
]
