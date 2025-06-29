"""
ASGI config for cabinet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
import logging
from django.core.asgi import get_asgi_application

logger = logging.getLogger(__name__)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabinet.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import notifications.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns
        )
    ),
})

logger.info('ASGI application configured with WebSocket support')
