
import subprocess
import json
import os
import tempfile
from typing import List, Dict

from .base import BaseScanner


class GitleaksScanner(BaseScanner):

    
    def scan(self, workspace_path: str) -> List[Dict]:
        findings = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as report_file:
            report_path = report_file.name
        
        try:
            cmd = [
                'gitleaks', 'detect',
                '--source', workspace_path,
                '--report-format', 'json',
                '--report-path', report_path,
                '--no-git',
                '--exit-code', '0'
            ]
            

            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            

            

            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for issue in data:
                        findings.append(self._normalize_finding(issue, workspace_path))
                        
        except subprocess.TimeoutExpired:
            print(f"Gitleaks scan timed out for {workspace_path}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gitleaks output: {e}")
        except Exception as e:
            print(f"Gitleaks scan error: {e}")
        finally:

            if os.path.exists(report_path):
                os.unlink(report_path)
        
        return findings
    
    def _normalize_finding(self, issue: Dict, workspace_path: str) -> Dict:
        file_path = issue.get('File', '')
        if file_path.startswith(workspace_path):
            file_path = os.path.relpath(file_path, workspace_path)
        
        rule_id = issue.get('RuleID', 'unknown-secret')
        description = issue.get('Description', 'Secret detected')
        
        severity = self._determine_severity(rule_id, description)
        
        match_preview = issue.get('Match', '')[:20] + '...' if len(issue.get('Match', '')) > 20 else issue.get('Match', '')
        
        secret_line = issue.get('Secret', '')
        if len(secret_line) > 8:
            masked = secret_line[:4] + '*' * (len(secret_line) - 8) + secret_line[-4:]
        else:
            masked = '*' * len(secret_line)
        
        return {
            'tool': 'gitleaks',
            'rule_id': rule_id,
            'title': f'Secret Detected: {description}',
            'description': f'{description}. Found pattern matching {rule_id} in file.',
            'severity': severity,
            'file_path': file_path,
            'line_number': issue.get('StartLine'),
            'raw_output': {
                'code': masked,
                'rule_id': rule_id,
                'description': description,
                'file': file_path,
                'start_line': issue.get('StartLine'),
                'end_line': issue.get('EndLine'),
                'entropy': issue.get('Entropy'),
                'author': issue.get('Author'),
                'commit': issue.get('Commit'),
            }
        }
    

    def _determine_severity(self, rule_id: str, description: str) -> str:
        rule_lower = rule_id.lower()
        desc_lower = description.lower()

        critical_patterns = [
            'aws', 'private-key', 'private_key', 'rsa', 'ssh',
            'github', 'gitlab', 'stripe', 'twilio', 'sendgrid',
            'slack', 'discord', 'telegram', 'oauth', 'jwt'
        ]
        
        for pattern in critical_patterns:
            if pattern in rule_lower or pattern in desc_lower:
                return 'critical'
        
        high_patterns = ['api', 'key', 'token', 'secret', 'password', 'credential']
        
        for pattern in high_patterns:
            if pattern in rule_lower or pattern in desc_lower:
                return 'high'
        

        return 'high'
