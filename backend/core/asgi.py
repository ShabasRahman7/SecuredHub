import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()

from compliance import routing as compliance_routing
from compliance.middleware import JWTAuthMiddleware
from accounts.notifications import NotificationConsumer
from django.urls import path

# WebSocket routes - compliance evaluations and notifications
websocket_urlpatterns = (
    compliance_routing.websocket_urlpatterns +
    [path('ws/notifications/', NotificationConsumer.as_asgi())]
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
