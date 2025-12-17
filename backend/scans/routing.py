from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/scans/<int:scan_id>/', consumers.ScanConsumer.as_asgi()),
]

