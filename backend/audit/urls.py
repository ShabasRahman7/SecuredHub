from django.urls import path
from audit import views

urlpatterns = [
    path('', views.list_audit_logs, name='audit-logs-list'),
    path('stats/', views.get_audit_stats, name='audit-logs-stats'),
]
