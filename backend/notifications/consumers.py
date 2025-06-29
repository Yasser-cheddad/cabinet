import json
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import logging
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Parse query string
            query_string = parse_qs(self.scope['query_string'].decode())
            token = query_string.get('token', [None])[0]
            
            if not token:
                logger.warning("No token provided")
                await self.close()
                return
                
            logger.info(f"Token received: {token[:10]}...")
            
            # Validate token
            try:
                validated_token = await sync_to_async(AccessToken)(token)
                user_id = validated_token['user_id']
                
                # Get user
                self.user = await sync_to_async(User.objects.get)(id=user_id)
                logger.info(f"Authenticated user: {self.user.id}")
                
                # Accept connection
                await self.accept()
                
                # Add to user's notification group
                await self.channel_layer.group_add(
                    f'notifications_{user_id}',
                    self.channel_name
                )
                
                # Send connection confirmation
                await self.send(text_data=json.dumps({
                    'type': 'connection',
                    'message': 'WebSocket authenticated successfully',
                    'user_id': user_id
                }))
                
            except TokenError as e:
                logger.error(f"Token validation failed: {str(e)}")
                await self.close(code=4001)
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close(code=4000)

    async def receive(self, text_data):
        if text_data == 'ping':
            await self.send('pong')
        else:
            logger.info(f"Received message: {text_data}")
            
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['data']))
        
    async def send_heartbeat(self, event):
        await self.send(text_data=json.dumps({
            'type': 'heartbeat',
            'message': 'connection_active'
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user:
            await self.channel_layer.group_discard(
                f'notifications_{self.user.id}',
                self.channel_name
            )
