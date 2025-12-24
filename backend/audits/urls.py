"""
URL configuration for audits app.
"""
from django.urls import path
from .views import AuditLogListView, AuditLogDetailView

urlpatterns = [
    path('', AuditLogListView.as_view(), name='audit_list'),
    path('<int:pk>/', AuditLogDetailView.as_view(), name='audit_detail'),
]
