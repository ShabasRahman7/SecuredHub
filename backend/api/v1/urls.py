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
    
    # Compliance platform endpoints
    path("standards/", include("standards.urls")),
    path("compliance/", include("compliance.urls")),
    
    # Audit logs (read-only)
    path("audits/", include("audits.urls")),
    
    # Internal API for worker → backend communication
    path("internal/", include("compliance.internal_urls")),
    
    # AI Agent proxy endpoints
    path("ai/", include("compliance.ai_urls")),
]

