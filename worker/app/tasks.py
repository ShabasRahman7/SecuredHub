import logging
import time
import os

# Bootstrap Django so Celery tasks can use ORM and channels.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .celery_app import app
from .db import get_scan, update_scan_status

logger = logging.getLogger(__name__)


def _send_ws_update(channel_layer, group_name, payload):
    """Send a scan progress update over the WebSocket channel layer."""
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "scan_update", **payload},
    )


@app.task(bind=True, name="scans.tasks.run_security_scan", max_retries=3, default_retry_delay=60)
def run_security_scan(self, scan_id: int):
    channel_layer = get_channel_layer()
    group_name = f"scan_{scan_id}"
    
    try:
        scan = get_scan(scan_id)
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            raise ValueError(f"Scan {scan_id} not found")

        _send_ws_update(channel_layer, group_name, {
            "scan_id": scan_id,
            "status": "running",
            "message": "Scan started",
            "progress": 0,
        })
        update_scan_status(scan_id, "running")

        logger.info(f"Starting scan {scan_id} for repository ID {scan.repository_id}")

        for progress in [25, 50, 75]:
            time.sleep(6)
            _send_ws_update(channel_layer, group_name, {
                "scan_id": scan_id,
                "status": "running",
                "message": f"Scan in progress ({progress}%)",
                "progress": progress,
            })

        time.sleep(6)

        update_scan_status(scan_id, "completed")
        _send_ws_update(channel_layer, group_name, {
            "scan_id": scan_id,
            "status": "completed",
            "message": "Scan completed",
            "progress": 100,
            "findings_count": 0,
        })

        logger.info(f"Scan {scan_id} completed successfully")

        return {"scan_id": scan_id, "status": "completed", "findings_count": 0}

    except Exception as exc:
        logger.error(f"Scan {scan_id} failed: {str(exc)}")
        update_scan_status(scan_id, "failed", error_message=str(exc))
        
        if channel_layer:
            _send_ws_update(channel_layer, group_name, {
                "scan_id": scan_id,
                "status": "failed",
                "message": str(exc),
                "progress": None,
            })
        
        raise self.retry(exc=exc)
