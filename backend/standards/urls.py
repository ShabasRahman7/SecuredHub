"""
URL patterns for standards API.
"""
from django.urls import path
from standards.views.standard import (
    StandardListView,
    StandardDetailView,
    StandardRulesView,
    RepositoryStandardsView,
    RepositoryStandardDeleteView
)

urlpatterns = [
    # Standards
    path('', StandardListView.as_view(), name='standard-list'),
    path('<slug:slug>/', StandardDetailView.as_view(), name='standard-detail'),
    path('<slug:slug>/rules/', StandardRulesView.as_view(), name='standard-rules'),
    
    # Repository-Standard assignments (will be accessed via nested route)
    path('repositories/<int:repository_id>/', 
         RepositoryStandardsView.as_view(), name='repository-standards'),
    path('repositories/<int:repository_id>/<int:standard_id>/', 
         RepositoryStandardDeleteView.as_view(), name='repository-standard-delete'),
]
