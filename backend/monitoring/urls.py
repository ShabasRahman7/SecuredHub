from django.urls import path
from .views import WorkerHealthView

app_name = "monitoring"

urlpatterns = [
    path("workers/health/", WorkerHealthView.as_view(), name="worker_health"),
]

