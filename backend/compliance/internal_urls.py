"""
URL patterns for internal API (worker and AI agent → backend communication).
"""
from django.urls import path
from compliance.views.internal import (
    UpdateEvaluationStatusView,
    BulkCreateResultsView,
    CompleteEvaluationView,
)
from compliance.views.ai_internal import (
    AIEvaluationDetailView,
    AIEvaluationFailuresView,
    AIRepositoryDetailView,
    AIStandardDetailView,
    AIScoreHistoryView,
)

urlpatterns = [
    # Worker endpoints (existing)
    path('evaluations/<int:pk>/status/', UpdateEvaluationStatusView.as_view(), name='internal-update-status'),
    path('evaluations/<int:pk>/results/', BulkCreateResultsView.as_view(), name='internal-bulk-results'),
    path('evaluations/<int:pk>/complete/', CompleteEvaluationView.as_view(), name='internal-complete'),
    
    # AI Agent endpoints (new)
    path('compliance/evaluations/<int:pk>/', AIEvaluationDetailView.as_view(), name='ai-evaluation-detail'),
    path('compliance/evaluations/<int:pk>/failures/', AIEvaluationFailuresView.as_view(), name='ai-evaluation-failures'),
    path('repositories/<int:pk>/', AIRepositoryDetailView.as_view(), name='ai-repository-detail'),
    path('standards/<int:pk>/', AIStandardDetailView.as_view(), name='ai-standard-detail'),
    path('repositories/<int:pk>/score-history/', AIScoreHistoryView.as_view(), name='ai-score-history'),
]

