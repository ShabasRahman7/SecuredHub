"""Main Celery tasks for scanning repositories"""
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict

from celery_app import app
from scanners import BanditScanner, SecretScanner
from utils import clone_repository, get_latest_commit_hash, get_commit_info, WorkspaceManager

API_BASE_URL = os.getenv('BACKEND_API_URL', 'http://api:8001')
INTERNAL_TOKEN = os.getenv('INTERNAL_SERVICE_TOKEN', '')

def _make_internal_request(method: str, endpoint: str, data: dict = None):
    # making authenticated request to internal API
    url = f"{API_BASE_URL}{endpoint}"
    headers = {'X-Internal-Token': INTERNAL_TOKEN}
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        raise

@app.task(bind=True, max_retries=3)
def scan_repository_task(self, repo_id: int, scan_id: int):
    """Execute security scan on repository and submit findings to backend."""
    workspace_mgr = WorkspaceManager()
    workspace_path = None
    
    def _update_progress(progress: int, message: str = ''):
        """Helper to send progress updates via internal API."""
        try:
            _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
                'status': 'running',
                'progress': progress,
                'message': message
            })
        except Exception as e:
            print(f"Progress update failed: {e}")
    
    try:
        # getting repository info from API
        repo_info = _make_internal_request('GET', f'/api/v1/internal/repositories/{repo_id}/')
        
        print(f"Starting scan for repository: {repo_info['name']} (ID: {repo_id})")
        
        # updating scan status to running (10% - starting)
        _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'progress': 10,
            'message': 'Initializing scan...'
        })
        
        workspace_path = workspace_mgr.create_workspace(repo_id)
        
        access_token = repo_info.get('access_token')
        
        # 25% - Cloning repository
        _update_progress(25, 'Cloning repository...')
        clone_repository(repo_info['url'], workspace_path, access_token)
        
        # getting commit information
        commit_info = get_commit_info(workspace_path)
        latest_commit = commit_info['hash']
        
        # no deduplication check here - backend already checked before queuing
        # worker just scans what it's told to scan
        
        all_findings = []
        print("Running security scanners...")
        
        from scanners.bandit_scanner import BanditScanner
        from scanners.secret_scanner import SecretScanner
        
        # 50% - Running Bandit for Python security issues
        _update_progress(50, 'Running Python security scanner (Bandit)...')
        bandit = BanditScanner()
        bandit_findings = bandit.scan(workspace_path)
        all_findings.extend(bandit_findings)
        print(f"Bandit: {len(bandit_findings)} findings")
        
        # 75% - Running secret scanner
        _update_progress(75, 'Scanning for exposed secrets...')
        secret_scanner = SecretScanner()
        secret_findings = secret_scanner.scan(workspace_path)
        all_findings.extend(secret_findings)
        print(f"Secret Scanner: {len(secret_findings)} findings")
        
        print(f"Total findings: {len(all_findings)}")
        
        # 90% - Submitting findings
        _update_progress(90, 'Saving scan results...')
        
        filtered_findings = all_findings

        
        # submit filtered findings via internal API
        result = _make_internal_request(
            'POST',
            f'/api/v1/internal/scans/{scan_id}/findings/',
            data={
                'findings': filtered_findings,
                'commit_hash': latest_commit,
                'update_repo_commit': True
            }
        )
        findings_count = result.get('findings_count', 0)
        print(f"Submitted {findings_count} findings to API")
        
        # 100% - mark scan as completed
        _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'commit_hash': latest_commit,
            'progress': 100,
            'message': 'Scan completed'
        })
        
        print(f"Scan completed successfully. {findings_count} findings saved.")
        
        return {
            'status': 'success',
            'commit': latest_commit[:7],
            'findings_count': findings_count,
            'scanners_run': ['bandit', 'secret_scanner']
        }
        
    except Exception as e:
        error_msg = f"Scan failed: {str(e)}"
        print(error_msg)
        
        # try to mark scan as failed
        try:
            _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
                'status': 'failed',
                'error_message': error_msg,
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
        except Exception as api_error:
            print(f"Failed to update scan status: {api_error}")
        
        # retrying on transient errors
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            raise self.retry(exc=e, countdown=60)
        raise
        
    finally:
        # always cleanup workspace
        if workspace_path:
            workspace_mgr.cleanup_workspace(workspace_path)
