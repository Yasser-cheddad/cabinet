from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PatientViewSet)

urlpatterns = [
    path('list/', views.list_patients, name='list_patients'),
    path('create-profile/', views.create_patient_profile, name='create_patient_profile'),
    path('', include(router.urls)),
]
