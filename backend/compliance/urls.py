"""
URL patterns for compliance API.
"""
from django.urls import path
from compliance.views.evaluation import (
    EvaluationListView,
    EvaluationDetailView,
    TriggerEvaluationView,
    LatestEvaluationView,
    RepositoryScoresView,
    DeleteEvaluationView
)

urlpatterns = [
    # Trigger new evaluation
    path('evaluations/trigger/', TriggerEvaluationView.as_view(), name='trigger-evaluation'),
    
    # Evaluation details
    path('evaluations/<int:pk>/', EvaluationDetailView.as_view(), name='evaluation-detail'),
    
    # Repository evaluations
    path('repositories/<int:repository_id>/evaluations/', 
         EvaluationListView.as_view(), name='repository-evaluations'),
    path('repositories/<int:repository_id>/standards/<int:standard_id>/latest/', 
         LatestEvaluationView.as_view(), name='latest-evaluation'),
    path('repositories/<int:repository_id>/scores/', 
         RepositoryScoresView.as_view(), name='repository-scores'),
    
    # Delete evaluation (owner only)
    path('evaluations/<int:pk>/delete/', DeleteEvaluationView.as_view(), name='delete-evaluation'),
]
