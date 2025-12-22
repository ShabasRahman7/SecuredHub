from django.urls import path
from . import consumers
from accounts.notifications import NotificationConsumer

websocket_urlpatterns = [
    path('ws/scans/<int:scan_id>/', consumers.ScanConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
