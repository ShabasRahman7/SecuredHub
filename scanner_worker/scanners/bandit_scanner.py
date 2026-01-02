"""Bandit scanner for Python SAST"""
import subprocess
import json
import os
from typing import List, Dict
from .base import BaseScanner

class BanditScanner(BaseScanner):
    
    def scan(self, workspace_path: str) -> List[Dict]:
        findings = []
        
        # debug: listing Python files in workspace
        print(f"DEBUG: Scanning workspace: {workspace_path}")
        python_files = []
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        print(f"DEBUG: Found {len(python_files)} Python files")
        for pf in python_files[:10]:  # Show first 10
            print(f"  - {pf}")
        
        try:
            # running Bandit with JSON output
            cmd = ['bandit', '-r', workspace_path, '-f', 'json', '--quiet']
            print(f"DEBUG: Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            print(f"DEBUG: Bandit exit code: {result.returncode}")
            print(f"DEBUG: Bandit stdout length: {len(result.stdout)}")
            print(f"DEBUG: Bandit stderr: {result.stderr[:500]}")
            
            # parsing JSON output
            if result.stdout:
                data = json.loads(result.stdout)
                results_count = len(data.get('results', []))
                print(f"DEBUG: Bandit found {results_count} issues in JSON")
                
                # processing each finding
                for issue in data.get('results', []):
                    findings.append(self._normalize_finding(issue, workspace_path))
                    
        except subprocess.TimeoutExpired:
            print(f"Bandit scan timed out for {workspace_path}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Bandit output: {e}")
        except Exception as e:
            print(f"Bandit scan error: {e}")
        
        return findings
    
    def _normalize_finding(self, issue: Dict, workspace_path: str) -> Dict:
        # getting relative file path
        file_path = issue.get('filename', '')
        if file_path.startswith(workspace_path):
            file_path = os.path.relpath(file_path, workspace_path)
        
        # mapping Bandit severity to our standard
        severity_map = {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high'
        }
        severity = severity_map.get(
            issue.get('issue_severity', 'MEDIUM').upper(), 
            'medium'
        )
        
        return {
            'tool': 'bandit',
            'rule_id': issue.get('test_id', 'UNKNOWN'),
            'title': issue.get('test_name', 'Security Issue'),
            'description': issue.get('issue_text', 'No description provided'),
            'severity': severity,
            'file_path': file_path,
            'line_number': issue.get('line_number'),
            'raw_output': issue
        }
