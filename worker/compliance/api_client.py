"""
Backend API client for worker → backend communication.

This module replaces direct database writes with HTTP API calls,
making the backend the single source of truth for all data mutations.
"""
import logging
import time
from typing import Dict, List, Optional, Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BackendAPIError(Exception):
    """Exception raised when backend API call fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class EvaluationDeletedError(BackendAPIError):
    """
    Exception raised when evaluation was deleted during processing.
    
    This is not a transient error - the worker should stop processing
    and NOT retry the task.
    """
    pass


class BackendAPIClient:
    """
    HTTP client for communicating with backend internal API.
    
    Handles authentication, retries, and error handling for
    worker → backend communication.
    """
    
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds (exponential backoff base)
    
    def __init__(self, base_url: Optional[str] = None, service_token: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Backend API base URL (default: from settings)
            service_token: Service authentication token (default: from settings)
        """
        self.base_url = (base_url or getattr(settings, 'BACKEND_API_URL', '')).rstrip('/')
        self.service_token = service_token or getattr(settings, 'INTERNAL_SERVICE_TOKEN', '')
        
        if not self.base_url:
            raise ValueError("BACKEND_API_URL not configured")
        if not self.service_token:
            raise ValueError("INTERNAL_SERVICE_TOKEN not configured")
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Service-Token': self.service_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
    
    def _request(self, method: str, path: str, data: Optional[dict] = None, 
                 retries: int = MAX_RETRIES) -> dict:
        """
        Make an HTTP request to the backend API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            path: API path (relative to base_url)
            data: Request body data
            retries: Number of retries remaining
            
        Returns:
            Response data as dict
            
        Raises:
            BackendAPIError: If request fails after all retries
        """
        url = f"{self.base_url}{path}"
        
        for attempt in range(retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT,
                )
                
                # Success responses
                if response.status_code in (200, 201):
                    return response.json()
                
                # Client errors (don't retry)
                if 400 <= response.status_code < 500:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except ValueError:
                        pass
                    
                    # 404 = evaluation was deleted, don't retry
                    if response.status_code == 404:
                        raise EvaluationDeletedError(
                            "Evaluation was deleted",
                            status_code=404,
                            response_data=error_data,
                        )
                    
                    raise BackendAPIError(
                        f"Client error: {response.status_code}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )
                
                # Server errors (retry)
                if response.status_code >= 500:
                    if attempt < retries:
                        delay = self.RETRY_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Backend API returned {response.status_code}, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{retries + 1})"
                        )
                        time.sleep(delay)
                        continue
                    raise BackendAPIError(
                        f"Server error after {retries + 1} attempts: {response.status_code}",
                        status_code=response.status_code,
                    )
                    
            except requests.exceptions.Timeout as e:
                if attempt < retries:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request timeout, retrying in {delay}s")
                    time.sleep(delay)
                    continue
                raise BackendAPIError(f"Request timeout after {retries + 1} attempts") from e
                
            except requests.exceptions.ConnectionError as e:
                if attempt < retries:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {delay}s")
                    time.sleep(delay)
                    continue
                raise BackendAPIError(f"Connection failed after {retries + 1} attempts") from e
        
        raise BackendAPIError("Request failed unexpectedly")
    
    def update_status(
        self,
        evaluation_id: int,
        status: str,
        message: str = '',
        progress: Optional[int] = None,
        commit_hash: Optional[str] = None,
        error_message: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> dict:
        """
        Update evaluation status.
        
        Args:
            evaluation_id: ID of the evaluation
            status: New status ('running', 'completed', 'failed')
            message: Progress message
            progress: Progress percentage (0-100)
            commit_hash: Git commit hash
            error_message: Error message (for failed status)
            task_id: Celery task ID
            
        Returns:
            Updated evaluation data
        """
        data = {'status': status}
        
        if message:
            data['message'] = message
        if progress is not None:
            data['progress'] = progress
        if commit_hash:
            data['commit_hash'] = commit_hash
        if error_message:
            data['error_message'] = error_message
        if task_id:
            data['task_id'] = task_id
        
        logger.info(f"Updating evaluation {evaluation_id} status to '{status}'")
        
        return self._request(
            method='PATCH',
            path=f'/evaluations/{evaluation_id}/status/',
            data=data,
        )
    
    def create_results(self, evaluation_id: int, results: List[Dict[str, Any]]) -> dict:
        """
        Bulk create rule results for an evaluation.
        
        Args:
            evaluation_id: ID of the evaluation
            results: List of result dicts with:
                - rule_id: int
                - passed: bool
                - message: str
                - evidence: dict
                - weight: int
                
        Returns:
            Response with created count
        """
        logger.info(f"Creating {len(results)} results for evaluation {evaluation_id}")
        
        return self._request(
            method='POST',
            path=f'/evaluations/{evaluation_id}/results/',
            data={'results': results},
        )
    
    def complete_evaluation(
        self,
        evaluation_id: int,
        passed_weight: int,
        total_weight: int,
        passed_count: int,
        failed_count: int,
        total_rules: int,
    ) -> dict:
        """
        Complete an evaluation and create the score.
        
        Args:
            evaluation_id: ID of the evaluation
            passed_weight: Sum of weights for passed rules
            total_weight: Sum of all rule weights
            passed_count: Number of passed rules
            failed_count: Number of failed rules
            total_rules: Total number of rules evaluated
            
        Returns:
            Completion response with final score
        """
        data = {
            'passed_weight': passed_weight,
            'total_weight': total_weight,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'total_rules': total_rules,
        }
        
        logger.info(
            f"Completing evaluation {evaluation_id}: "
            f"{passed_count}/{total_rules} rules passed"
        )
        
        return self._request(
            method='POST',
            path=f'/evaluations/{evaluation_id}/complete/',
            data=data,
        )
    
    def mark_failed(self, evaluation_id: int, error_message: str) -> dict:
        """
        Mark an evaluation as failed.
        
        Args:
            evaluation_id: ID of the evaluation
            error_message: Error description
            
        Returns:
            Updated evaluation data
        """
        logger.error(f"Marking evaluation {evaluation_id} as failed: {error_message}")
        
        return self.update_status(
            evaluation_id=evaluation_id,
            status='failed',
            error_message=error_message,
        )


# Singleton instance for convenience
_client_instance: Optional[BackendAPIClient] = None


def get_api_client() -> BackendAPIClient:
    """Get or create the singleton API client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = BackendAPIClient()
    return _client_instance
