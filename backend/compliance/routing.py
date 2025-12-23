"""
WebSocket routing for compliance evaluations.
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/evaluations/<int:evaluation_id>/', consumers.EvaluationConsumer.as_asgi()),
]
