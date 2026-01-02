"""URL configuration for scans app"""
from django.urls import path
from . import views

app_name = 'scans'

urlpatterns = [
    path('trigger/<int:repo_id>/', views.trigger_scan, name='trigger_scan'),
    path('<int:scan_id>/', views.get_scan_detail, name='scan_detail'),
    path('<int:scan_id>/delete/', views.delete_scan, name='delete_scan'),
    path('<int:scan_id>/findings/', views.get_scan_findings, name='scan_findings'),
    path('repository/<int:repo_id>/', views.get_repository_scans, name='repository_scans'),
]

