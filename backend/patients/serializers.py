from rest_framework import serializers
from .models import Patient
from accounts.serializers import UserSerializer
from accounts.models import User

class PatientSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Patient
        fields = ['id', 'user_details', 'user_id', 'blood_type', 'allergies', 'created_at']
        read_only_fields = ['created_at']
