import os

# Initialise Django using the worker's settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from scans.models import Scan
from django.utils import timezone


def get_scan(scan_id: int):
    """Fetch a scan with its repository or return None if it does not exist."""
    try:
        return Scan.objects.select_related('repository').get(id=scan_id)
    except Scan.DoesNotExist:
        return None


def update_scan_status(scan_id: int, status: str, error_message: str = None):
    """Update the stored status and timestamps for a scan."""
    try:
        scan = Scan.objects.get(id=scan_id)
        scan.status = status
        
        if status == "running" and not scan.started_at:
            scan.started_at = timezone.now()
        elif status in ("completed", "failed"):
            scan.completed_at = timezone.now()
            if error_message:
                scan.error_message = error_message
        
        scan.save()
    except Scan.DoesNotExist:
        pass
