
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict

from celery_app import app
from scanners import SemgrepScanner, GitleaksScanner, TrivyScanner
from utils import clone_repository, get_latest_commit_hash, get_commit_info, WorkspaceManager
from utils.s3_uploader import S3Uploader

API_BASE_URL = os.getenv('BACKEND_API_URL', 'http://api:8001')
INTERNAL_TOKEN = os.getenv('INTERNAL_SERVICE_TOKEN', '')


def _make_internal_request(method: str, endpoint: str, data: dict = None):
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
    workspace_mgr = WorkspaceManager()
    workspace_path = None
    
    def _update_progress(progress: int, message: str = ''):
        try:
            _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
                'status': 'running',
                'progress': progress,
                'message': message
            })
        except Exception as e:
            print(f"Progress update failed: {e}")
    
    try:
        repo_info = _make_internal_request('GET', f'/api/v1/internal/repositories/{repo_id}/')
        
        print(f"Starting scan for repository: {repo_info['name']} (ID: {repo_id})")
        
        _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'progress': 10,
            'message': 'Initializing scan...'
        })
        
        workspace_path = workspace_mgr.create_workspace(repo_id)
        
        access_token = repo_info.get('access_token')
        
        _update_progress(25, 'Cloning repository...')
        clone_repository(repo_info['url'], workspace_path, access_token)
        
        commit_info = get_commit_info(workspace_path)
        latest_commit = commit_info['hash']
        
        # I rely on the backend to check for duplicates before queuing
        
        all_findings = []
        print("Running security scanners...")
        
        from scanners.semgrep_scanner import SemgrepScanner
        from scanners.gitleaks_scanner import GitleaksScanner
        from scanners.trivy_scanner import TrivyScanner
        
        _update_progress(50, 'Running code security scanner (Semgrep)...')
        semgrep = SemgrepScanner()
        sast_findings = semgrep.scan(workspace_path)
        all_findings.extend(sast_findings)
        print(f"Semgrep: {len(sast_findings)} findings")
        
        _update_progress(65, 'Scanning for secrets (Gitleaks)...')
        gitleaks = GitleaksScanner()
        secret_findings = gitleaks.scan(workspace_path)
        all_findings.extend(secret_findings)
        print(f"Gitleaks: {len(secret_findings)} findings")
        
        _update_progress(80, 'Scanning dependencies (Trivy)...')
        trivy = TrivyScanner()
        dependency_findings = trivy.scan(workspace_path)
        all_findings.extend(dependency_findings)
        print(f"Trivy: {len(dependency_findings)} findings")
        
        print(f"Total findings: {len(all_findings)}")
        
        _update_progress(95, 'Saving scan results...')
        
        filtered_findings = all_findings

        
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
        
        _make_internal_request('POST', f'/api/v1/internal/scans/{scan_id}/status/', {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'commit_hash': latest_commit,
            'progress': 100,
            'message': 'Scan completed'
        })
        
        s3 = S3Uploader()
        s3.upload_scan_results(scan_id, repo_id, filtered_findings, {
            'commit_hash': latest_commit,
            'repo_name': repo_info['name'],
            'scanners': ['semgrep', 'gitleaks', 'trivy']
        })
        s3.upload_status(scan_id, repo_id, 'completed', f'{findings_count} findings')
        
        print(f"Scan completed successfully. {findings_count} findings saved.")
        
        return {
            'status': 'success',
            'commit': latest_commit[:7],
            'findings_count': findings_count,
            'scanners_run': ['semgrep', 'gitleaks', 'trivy']
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
