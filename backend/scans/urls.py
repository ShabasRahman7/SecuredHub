from django.urls import path
from . import views

urlpatterns = [
    path("repos/<int:repo_id>/scans/trigger/", views.trigger_scan, name='trigger-scan'),
    path("repos/<int:repo_id>/scans/", views.list_scans, name='list-scans'),
]
