"""
URL patterns for AI Agent proxy endpoints.
"""
from django.urls import path
from compliance.views.ai import (
    AIAnalyzeProxyView,
    AIAgentProxyView,
    AIEvaluationRecommendationsView,
    AIHealthView,
)

urlpatterns = [
    path('analyze/', AIAnalyzeProxyView.as_view(), name='ai-analyze'),
    path('agent/', AIAgentProxyView.as_view(), name='ai-agent'),
    path('evaluations/<int:pk>/recommendations/', AIEvaluationRecommendationsView.as_view(), name='ai-recommendations'),
    path('health/', AIHealthView.as_view(), name='ai-health'),
]
