from django.urls import path, include

from . import views
from accounts.urls import tenant_urlpatterns
from repositories.views.oauth import github_oauth_callback

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("auth/", include("accounts.urls")),
    path("notifications/", include("notifications.urls")),
    path("auth/github/callback/", github_oauth_callback, name="github_oauth_callback"),
    path("admin/", include("monitoring.urls")),

    # ====================================================================
    # tenant Endpoints
    # ====================================================================
    path("", include((tenant_urlpatterns, "tenants"))),
    path("tenants/<int:tenant_id>/repositories/", include("repositories.urls")),
    path("scans/", include("scans.urls")),
    path("chat/", include("chat.urls")),
    path("internal/", include("api.v1.internal_urls")),
]
