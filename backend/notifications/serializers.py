from rest_framework import serializers
from .models import Notification
from accounts.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user_details', 'title', 'message', 'notification_type',
            'is_read', 'is_sent', 'created_at', 'scheduled_time'
        ]
        read_only_fields = ['created_at']
