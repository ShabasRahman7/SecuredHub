from django.urls import path, include

from . import views
from accounts.urls import tenant_urlpatterns
from repositories.views.oauth import github_oauth_callback


urlpatterns = [
    # Basic API health endpoint
    path("health/", views.health_check, name="health_check"),

    # Authentication and account management
    path("auth/", include("accounts.urls")),
    path("auth/github/callback/", github_oauth_callback, name="github_oauth_callback"),

    # Admin and platform monitoring endpoints
    path("admin/", include("monitoring.urls")),

    # Tenant endpoints and nested tenant resources
    path("", include((tenant_urlpatterns, "tenants"))),
    path("tenants/<int:tenant_id>/repositories/", include("repositories.urls")),

    # Scan-related endpoints
    path("", include("scans.urls")),
]
