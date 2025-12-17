from celery import shared_task
from django.utils import timezone
from .models import Scan
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_security_scan(self, scan_id):
    """
    Execute security scan for a repository.
    
    Args:
        scan_id: ID of the Scan model instance
    
    Returns:
        dict: Scan results summary
    """
    try:
        scan = Scan.objects.get(id=scan_id)
        
        # Update status to running
        scan.status = 'running'
        scan.started_at = timezone.now()
        scan.save()
        
        logger.info(f"Starting scan {scan_id} for repository {scan.repository.name}")

        import time
        time.sleep(2)  # Simulate work
        
        # Update status to completed
        scan.status = 'completed'
        scan.completed_at = timezone.now()
        scan.save()
        
        logger.info(f"Scan {scan_id} completed successfully")
        
        return {
            'scan_id': scan_id,
            'status': 'completed',
            'findings_count': 0
        }
        
    except Scan.DoesNotExist:
        logger.error(f"Scan {scan_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Scan {scan_id} failed: {str(exc)}")
        
        # Update scan status to failed
        try:
            scan = Scan.objects.get(id=scan_id)
            scan.status = 'failed'
            scan.error_message = str(exc)
            scan.completed_at = timezone.now()
            scan.save()
        except:
            pass
        
        # Retry the task
        raise self.retry(exc=exc)

