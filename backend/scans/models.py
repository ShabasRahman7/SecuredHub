from django.db import models
from repositories.models import Repository

class Scan(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name="scans"
    )

    triggered_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="queued"
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    commit_hash = models.CharField(max_length=255, null=True, blank=True)
    branch = models.CharField(max_length=100, default="main")

    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} → Repo {self.repository.name}"


class ScanFinding(models.Model):
    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="findings"
    )
    file_path = models.CharField(max_length=500)
    line = models.IntegerField(null=True, blank=True)
    severity = models.CharField(max_length=20)
    rule_id = models.CharField(max_length=100)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
