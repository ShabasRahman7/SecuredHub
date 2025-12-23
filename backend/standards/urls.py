"""
URL patterns for standards API.
"""
from django.urls import path
from standards.views.standard import (
    StandardListView,
    StandardDetailView,
    StandardRulesView,
    RepositoryStandardsView,
    RepositoryStandardDeleteView,
    CreateStandardView,
    UpdateStandardView,
    DeleteStandardView,
    CreateRuleView,
    UpdateRuleView,
    DeleteRuleView
)

urlpatterns = [
    # Standards - List and Create
    path('', StandardListView.as_view(), name='standard-list'),
    path('create/', CreateStandardView.as_view(), name='standard-create'),
    
    # Standard Detail/Update/Delete
    path('<slug:slug>/', StandardDetailView.as_view(), name='standard-detail'),
    path('<slug:slug>/update/', UpdateStandardView.as_view(), name='standard-update'),
    path('<slug:slug>/delete/', DeleteStandardView.as_view(), name='standard-delete'),
    
    # Rules - List and Create
    path('<slug:slug>/rules/', StandardRulesView.as_view(), name='standard-rules'),
    path('<slug:slug>/rules/create/', CreateRuleView.as_view(), name='rule-create'),
    
    # Rule Update/Delete
    path('<slug:slug>/rules/<int:rule_id>/update/', UpdateRuleView.as_view(), name='rule-update'),
    path('<slug:slug>/rules/<int:rule_id>/delete/', DeleteRuleView.as_view(), name='rule-delete'),
    
    # Repository-Standard assignments
    path('repositories/<int:repository_id>/', 
         RepositoryStandardsView.as_view(), name='repository-standards'),
    path('repositories/<int:repository_id>/<int:standard_id>/', 
         RepositoryStandardDeleteView.as_view(), name='repository-standard-delete'),
]

