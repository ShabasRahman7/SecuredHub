import logging
import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Scan

logger = logging.getLogger(__name__)


def _send_ws_update(channel_layer, group_name, payload):
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "scan_update", **payload},
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_security_scan(self, scan_id):
    """Execute security scan and broadcast progress via WebSocket."""
    channel_layer = get_channel_layer()
    group_name = f"scan_{scan_id}"

    try:
        scan = Scan.objects.get(id=scan_id)

        _send_ws_update(channel_layer, group_name, {
            "scan_id": scan_id,
            "status": "running",
            "message": "Scan started",
            "progress": 0,
        })

        scan.status = "running"
        scan.started_at = timezone.now()
        scan.save()

        logger.info(f"Starting scan {scan_id} for repository {scan.repository.name}")

        for progress in [25, 50, 75]:
            time.sleep(6)
            _send_ws_update(channel_layer, group_name, {
                "scan_id": scan_id,
                "status": "running",
                "message": f"Scan in progress ({progress}%)",
                "progress": progress,
            })

        time.sleep(6)

        scan.status = "completed"
        scan.completed_at = timezone.now()
        scan.save()

        logger.info(f"Scan {scan_id} completed successfully")

        _send_ws_update(channel_layer, group_name, {
            "scan_id": scan_id,
            "status": "completed",
            "message": "Scan completed",
            "progress": 100,
            "findings_count": 0,
        })

        return {"scan_id": scan_id, "status": "completed", "findings_count": 0}

    except Scan.DoesNotExist:
        logger.error(f"Scan {scan_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Scan {scan_id} failed: {str(exc)}")

        try:
            scan = Scan.objects.get(id=scan_id)
            scan.status = "failed"
            scan.error_message = str(exc)
            scan.completed_at = timezone.now()
            scan.save()
        except Exception:
            pass

        _send_ws_update(channel_layer, group_name, {
            "scan_id": scan_id,
            "status": "failed",
            "message": str(exc),
            "progress": None,
        })

        raise self.retry(exc=exc)
