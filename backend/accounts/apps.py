from pathlib import Path

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts & Tenants"
    # Set an explicit path so Django finds the app correctly inside Docker images.
    path = str(Path(__file__).resolve().parent)


