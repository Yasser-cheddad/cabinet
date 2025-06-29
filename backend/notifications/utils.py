from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(user_id, message):
    """
    Send a WebSocket notification to a specific user
    :param user_id: ID of the recipient user
    :param message: Dictionary containing notification data
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'send_notification',
            'data': message
        }
    )
