"""
Celery tasks for compliance evaluation.

Main task: run_compliance_evaluation
Uses Backend API callbacks instead of direct database writes.
Backend is the single source of truth for all data mutations.
"""
import logging
import os

# Bootstrap Django for Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from cryptography.fernet import Fernet
import base64

from core.celery_app import app
from compliance_models.models import (
    ComplianceEvaluation, ComplianceRule, TenantCredential
)
from compliance.collectors.github import GitHubCollector
from compliance.evaluator import Evaluator
from compliance.api_client import get_api_client, BackendAPIError, EvaluationDeletedError

logger = logging.getLogger(__name__)


def _get_decryption_key():
    """Get encryption key for decrypting access tokens."""
    key = os.getenv('REPOSITORY_ENCRYPTION_KEY')
    if not key:
        raise ValueError("REPOSITORY_ENCRYPTION_KEY environment variable is required")
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key


def _decrypt_token(encrypted_token: str) -> str:
    """Decrypt an access token."""
    if not encrypted_token:
        return None
    try:
        fernet = Fernet(_get_decryption_key())
        encrypted_bytes = base64.b64decode(encrypted_token.encode())
        return fernet.decrypt(encrypted_bytes).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt token: {e}")
        return None


@app.task(bind=True, name="compliance.tasks.run_compliance_evaluation", max_retries=3, default_retry_delay=60)
def run_compliance_evaluation(self, evaluation_id: int):
    """
    Run a compliance evaluation for a repository against a standard.
    
    This task:
    1. Fetches the evaluation, repository, and standard from DB (read-only)
    2. Calls Backend API to update status to 'running'
    3. Collects repository structure from GitHub
    4. Executes all rules against the repository
    5. Calls Backend API to store results
    6. Calls Backend API to complete evaluation with score
    
    All writes go through Backend API - worker does NOT write directly to DB.
    Backend handles WebSocket updates.
    """
    api_client = None
    
    try:
        # Get API client
        api_client = get_api_client()
        
        # Fetch evaluation with related objects (READ-ONLY)
        evaluation = ComplianceEvaluation.objects.select_related(
            'repository', 'standard', 'repository__tenant'
        ).get(id=evaluation_id)
        
        repository = evaluation.repository
        standard = evaluation.standard
        
        logger.info(f"Starting evaluation #{evaluation_id} for {repository.name} against {standard.name}")
        
        # Update status to running via API (Backend sends WebSocket update)
        api_client.update_status(
            evaluation_id=evaluation_id,
            status='running',
            message='Evaluation started',
            progress=0,
            task_id=self.request.id,
        )
        
        # Get credential for repository access (READ-ONLY)
        credential = TenantCredential.objects.filter(
            tenant=repository.tenant,
            is_active=True,
            provider='github'
        ).first()
        
        if not credential:
            raise ValueError(f"No active GitHub credential found for tenant {repository.tenant.id}")
        
        access_token = _decrypt_token(credential.encrypted_access_token)
        if not access_token:
            raise ValueError("Could not decrypt access token")
        
        # Progress update via API
        api_client.update_status(
            evaluation_id=evaluation_id,
            status='running',
            message='Collecting repository structure...',
            progress=10,
        )
        
        # Collect repository snapshot
        collector = GitHubCollector.from_repository_url(
            url=repository.url,
            access_token=access_token,
            branch=repository.default_branch
        )
        snapshot = collector.collect()
        
        # Update with commit hash
        if snapshot.commit_hash:
            api_client.update_status(
                evaluation_id=evaluation_id,
                status='running',
                message=f'Collected {len(snapshot.files)} files. Evaluating rules...',
                progress=25,
                commit_hash=snapshot.commit_hash,
            )
        else:
            api_client.update_status(
                evaluation_id=evaluation_id,
                status='running',
                message=f'Collected {len(snapshot.files)} files. Evaluating rules...',
                progress=25,
            )
        
        # Get active rules for the standard (READ-ONLY)
        rules = list(ComplianceRule.objects.filter(
            standard=standard,
            is_active=True
        ).order_by('order', 'name').values(
            'id', 'name', 'rule_type', 'check_config', 'weight', 'severity'
        ))
        
        if not rules:
            raise ValueError(f"No active rules found for standard {standard.name}")
        
        logger.info(f"Evaluating {len(rules)} rules for repository {repository.name}")
        
        # Progress callback for rule evaluation
        def progress_callback(current, total, message):
            progress = 25 + int((current / total) * 60)  # 25-85% for rule evaluation
            try:
                api_client.update_status(
                    evaluation_id=evaluation_id,
                    status='running',
                    message=message,
                    progress=progress,
                )
            except BackendAPIError as e:
                # Don't fail the evaluation for progress update failures
                logger.warning(f"Progress update failed: {e}")
        
        # Run the evaluator
        evaluator = Evaluator(rules)
        result = evaluator.evaluate(snapshot, progress_callback=progress_callback)
        
        # Progress update before storing results
        api_client.update_status(
            evaluation_id=evaluation_id,
            status='running',
            message='Storing results...',
            progress=90,
        )
        
        # Store rule results via API (Backend does the INSERT)
        results_data = [
            {
                'rule_id': r['rule_id'],
                'passed': r['passed'],
                'message': r.get('message', ''),
                'evidence': r.get('evidence', {}),
                'weight': r['weight'],
            }
            for r in result.rule_results
        ]
        
        api_client.create_results(
            evaluation_id=evaluation_id,
            results=results_data,
        )
        
        # Complete evaluation via API (Backend calculates score, sends final WS update)
        completion_response = api_client.complete_evaluation(
            evaluation_id=evaluation_id,
            passed_weight=result.passed_weight,
            total_weight=result.total_weight,
            passed_count=result.passed_count,
            failed_count=result.failed_count,
            total_rules=result.total_count,
        )
        
        final_score = completion_response.get('score', result.score)
        
        logger.info(
            f"Evaluation #{evaluation_id} completed: {final_score}% "
            f"({result.passed_count}/{result.total_count} rules passed)"
        )
        
        return {
            'evaluation_id': evaluation_id,
            'status': 'completed',
            'score': float(final_score),
            'passed_count': result.passed_count,
            'failed_count': result.failed_count,
            'total_rules': result.total_count,
        }
        
    except ComplianceEvaluation.DoesNotExist:
        logger.error(f"Evaluation {evaluation_id} not found")
        raise ValueError(f"Evaluation {evaluation_id} not found")
    
    except EvaluationDeletedError:
        # Evaluation was deleted by user - stop processing gracefully
        logger.warning(
            f"Evaluation {evaluation_id} was deleted during processing. "
            "Terminating task gracefully."
        )
        return {
            'evaluation_id': evaluation_id,
            'status': 'deleted',
            'message': 'Evaluation was deleted during processing',
        }
        
    except BackendAPIError as exc:
        logger.error(f"Backend API error for evaluation {evaluation_id}: {exc}", exc_info=True)
        
        # Try to mark as failed via API
        if api_client:
            try:
                api_client.mark_failed(evaluation_id, str(exc))
            except EvaluationDeletedError:
                # Also deleted - just stop
                logger.warning(f"Evaluation {evaluation_id} was deleted, cannot mark as failed")
                return {
                    'evaluation_id': evaluation_id,
                    'status': 'deleted',
                    'message': 'Evaluation was deleted',
                }
            except Exception as e:
                logger.error(f"Could not mark evaluation as failed: {e}")
        
        raise self.retry(exc=exc)
        
    except Exception as exc:
        logger.error(f"Evaluation {evaluation_id} failed: {str(exc)}", exc_info=True)
        
        # Try to mark as failed via API
        if api_client:
            try:
                api_client.mark_failed(evaluation_id, str(exc))
            except EvaluationDeletedError:
                # Also deleted - just stop
                logger.warning(f"Evaluation {evaluation_id} was deleted, cannot mark as failed")
                return {
                    'evaluation_id': evaluation_id,
                    'status': 'deleted',
                    'message': 'Evaluation was deleted',
                }
            except BackendAPIError as e:
                logger.error(f"Could not mark evaluation as failed via API: {e}")
        
        raise self.retry(exc=exc)
