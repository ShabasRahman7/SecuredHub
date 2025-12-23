"""
URL patterns for internal API (worker → backend communication).
"""
from django.urls import path
from compliance.views.internal import (
    UpdateEvaluationStatusView,
    BulkCreateResultsView,
    CompleteEvaluationView,
)

urlpatterns = [
    path('evaluations/<int:pk>/status/', UpdateEvaluationStatusView.as_view(), name='internal-update-status'),
    path('evaluations/<int:pk>/results/', BulkCreateResultsView.as_view(), name='internal-bulk-results'),
    path('evaluations/<int:pk>/complete/', CompleteEvaluationView.as_view(), name='internal-complete'),
]
