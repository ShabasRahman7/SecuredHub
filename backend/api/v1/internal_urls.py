"""URL configuration for internal service-to-service API"""
from django.urls import path
from . import internal

app_name = 'internal'

urlpatterns = [
    path('repositories/<int:repo_id>/', internal.get_repository_info, name='repository_info'),
    
    # scan status updates
    path('scans/<int:scan_id>/status/', internal.update_scan_status, name='update_scan_status'),
    
    path('scans/<int:scan_id>/findings/', internal.submit_scan_findings, name='submit_findings'),
]
