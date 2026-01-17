#!/usr/bin/env python3
import os
import json
import subprocess
import tempfile
import shutil
import requests
import boto3
from datetime import datetime

SCAN_ID = os.environ.get('SCAN_ID')
REPO_URL = os.environ.get('REPO_URL')
COMMIT_SHA = os.environ.get('COMMIT_SHA', 'HEAD')
BACKEND_API_URL = os.environ.get('BACKEND_API_URL')
INTERNAL_SERVICE_TOKEN = os.environ.get('INTERNAL_SERVICE_TOKEN')
S3_BUCKET = os.environ.get('S3_SCAN_BUCKET')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

def clone_repo(repo_url, target_dir):
    print(f"Cloning {repo_url}...")
    subprocess.run(['git', 'clone', '--depth', '1', repo_url, target_dir], check=True)
    
    # get actual commit hash
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=target_dir, capture_output=True, text=True
    )
    commit_hash = result.stdout.strip() if result.returncode == 0 else None
    return target_dir, commit_hash

def run_semgrep(repo_dir):
    print("Running Semgrep...")
    result = subprocess.run(
        ['semgrep', 'scan', '--config', 'auto', '--json', repo_dir],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout) if result.stdout else {'results': []}
    except:
        return {'results': [], 'error': result.stderr}

def run_gitleaks(repo_dir):
    print("Running Gitleaks...")
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        output_file = f.name
    
    subprocess.run(
        ['gitleaks', 'detect', '--source', repo_dir, '--report-format', 'json', '--report-path', output_file],
        capture_output=True
    )
    
    try:
        with open(output_file, 'r') as f:
            return json.load(f)
    except:
        return []

def run_trivy(repo_dir):
    print("Running Trivy...")
    result = subprocess.run(
        ['trivy', 'fs', '--format', 'json', repo_dir],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout) if result.stdout else {'Results': []}
    except:
        return {'Results': [], 'error': result.stderr}

def upload_to_s3(scan_id, results):
    print(f"Uploading results to S3...")
    s3 = boto3.client('s3', region_name=AWS_REGION)
    key = f"scans/{scan_id}/results.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(results, indent=2),
        ContentType='application/json'
    )
    return f"s3://{S3_BUCKET}/{key}"

def update_progress(scan_id, message, progress=0, status='running'):
    """Send progress update to backend for real-time WebSocket updates"""
    url = f"{BACKEND_API_URL}/api/v1/internal/scans/{scan_id}/status/"
    headers = {
        'X-Internal-Token': INTERNAL_SERVICE_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
        'status': status,
        'message': message,
        'progress': progress
    }
    if status == 'running' and progress == 0:
        payload['started_at'] = datetime.utcnow().isoformat()
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except:
        pass  # Non-critical, don't fail scan if progress update fails

def callback_to_backend(scan_id, findings, status='completed', commit_hash=None):
    print(f"Calling back to backend...")
    url = f"{BACKEND_API_URL}/api/v1/internal/scans/{scan_id}/status/"
    headers = {
        'X-Internal-Token': INTERNAL_SERVICE_TOKEN,
        'Content-Type': 'application/json'
    }
    
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for f in findings:
        sev = f.get('severity', 'low').lower()
        if sev in severity_counts:
            severity_counts[sev] += 1
    
    payload = {
        'status': status,
        'findings_count': len(findings),
        'severity_breakdown': severity_counts,
        'completed_at': datetime.utcnow().isoformat(),
        'progress': 100 if status == 'completed' else 0,
        'message': f'Scan {status} - {len(findings)} findings' if status == 'completed' else 'Scan failed'
    }
    
    if commit_hash:
        payload['commit_hash'] = commit_hash
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"Callback response: {response.status_code}")
    return response.status_code == 200

def normalize_findings(semgrep, gitleaks, trivy):
    findings = []
    
    for r in semgrep.get('results', []):
        findings.append({
            'tool': 'semgrep',
            'severity': r.get('extra', {}).get('severity', 'medium'),
            'title': r.get('check_id', 'Unknown'),
            'file': r.get('path', ''),
            'line': r.get('start', {}).get('line', 0),
            'message': r.get('extra', {}).get('message', '')
        })
    
    for leak in gitleaks if isinstance(gitleaks, list) else []:
        findings.append({
            'tool': 'gitleaks',
            'severity': 'high',
            'title': f"Secret: {leak.get('RuleID', 'Unknown')}",
            'file': leak.get('File', ''),
            'line': leak.get('StartLine', 0),
            'message': leak.get('Description', '')
        })
    
    for result in trivy.get('Results', []):
        for vuln in result.get('Vulnerabilities', []):
            findings.append({
                'tool': 'trivy',
                'severity': vuln.get('Severity', 'medium').lower(),
                'title': vuln.get('VulnerabilityID', 'Unknown'),
                'file': result.get('Target', ''),
                'line': 0,
                'message': vuln.get('Title', '')
            })
    
    return findings

def main():
    print(f"=== K8s Scanner Job ===")
    print(f"Scan ID: {SCAN_ID}")
    print(f"Repo: {REPO_URL}")
    
    if not all([SCAN_ID, REPO_URL, BACKEND_API_URL, INTERNAL_SERVICE_TOKEN]):
        print("ERROR: Missing required environment variables")
        return 1
    
    work_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(work_dir, 'repo')
    
    try:
        update_progress(SCAN_ID, 'Starting scan...', 0, 'running')
        
        update_progress(SCAN_ID, 'Cloning repository...', 10)
        _, actual_commit = clone_repo(REPO_URL, repo_dir)
        
        update_progress(SCAN_ID, 'Running Semgrep (SAST)...', 25)
        semgrep_results = run_semgrep(repo_dir)
        
        update_progress(SCAN_ID, 'Running Gitleaks (secrets)...', 50)
        gitleaks_results = run_gitleaks(repo_dir)
        
        update_progress(SCAN_ID, 'Running Trivy (dependencies)...', 70)
        trivy_results = run_trivy(repo_dir)
        
        update_progress(SCAN_ID, 'Processing results...', 85)
        findings = normalize_findings(semgrep_results, gitleaks_results, trivy_results)
        
        results = {
            'scan_id': SCAN_ID,
            'repo_url': REPO_URL,
            'commit_sha': actual_commit or COMMIT_SHA,
            'timestamp': datetime.utcnow().isoformat(),
            'findings': findings,
            'raw': {
                'semgrep': semgrep_results,
                'gitleaks': gitleaks_results,
                'trivy': trivy_results
            }
        }
        
        update_progress(SCAN_ID, 'Uploading to S3...', 95)
        s3_path = upload_to_s3(SCAN_ID, results)
        print(f"Results uploaded to: {s3_path}")
        
        callback_to_backend(SCAN_ID, findings, commit_hash=actual_commit)
        
        print(f"=== Scan Complete: {len(findings)} findings ===")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        callback_to_backend(SCAN_ID, [], status='failed')
        return 1
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == '__main__':
    exit(main())
