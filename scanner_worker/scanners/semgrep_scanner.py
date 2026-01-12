
import subprocess
import json
import os
from typing import List, Dict

from .base import BaseScanner


class SemgrepScanner(BaseScanner):

    
    def scan(self, workspace_path: str) -> List[Dict]:
        findings = []
        
        try:
            # explicit rulesets avoid --config auto which requires metrics
            cmd = [
                'semgrep', 'scan',
                '--config', 'p/security-audit',
                '--config', 'p/secrets',
                '--json',
                '--quiet',
                '--no-git-ignore',
                workspace_path
            ]
            

            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            


            
            if result.stdout:
                data = json.loads(result.stdout)
                findings = self._parse_results(data, workspace_path)
                
        except subprocess.TimeoutExpired:
            print(f"Semgrep scan timed out for {workspace_path}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Semgrep output: {e}")
        except Exception as e:
            print(f"Semgrep scan error: {e}")
        
        return findings
    
    def _parse_results(self, data: Dict, workspace_path: str) -> List[Dict]:
        findings = []
        
        for result in data.get('results', []):
            findings.append(self._normalize_finding(result, workspace_path))
        
        return findings
    
    def _normalize_finding(self, result: Dict, workspace_path: str) -> Dict:
        file_path = result.get('path', '')
        if file_path.startswith(workspace_path):
            file_path = os.path.relpath(file_path, workspace_path)
        
        check_id = result.get('check_id', 'unknown-rule')
        extra = result.get('extra', {})
        
        message = extra.get('message', 'Security issue detected')
        metadata = extra.get('metadata', {})
        
        description = metadata.get('description', message)
        
        severity = self._map_severity(extra.get('severity', 'WARNING'))
        

        
        cwe = metadata.get('cwe', [])
        owasp = metadata.get('owasp', [])
        references = metadata.get('references', [])
        code_snippet = extra.get('lines', '')
        
        return {
            'tool': 'semgrep',
            'rule_id': check_id,
            'title': message,
            'description': description,
            'severity': severity,
            'file_path': file_path,
            'line_number': result.get('start', {}).get('line'),
            'raw_output': {
                'code': code_snippet,
                'check_id': check_id,
                'message': message,
                'severity': extra.get('severity'),
                'start_line': result.get('start', {}).get('line'),
                'end_line': result.get('end', {}).get('line'),
                'cwe': cwe[:3] if isinstance(cwe, list) else [cwe] if cwe else [],
                'owasp': owasp[:3] if isinstance(owasp, list) else [owasp] if owasp else [],
                'references': references[:3],
                'category': metadata.get('category'),
                'technology': metadata.get('technology', [])
            }
        }
    
    def _map_severity(self, semgrep_severity: str) -> str:
        severity_map = {
            'ERROR': 'critical',
            'WARNING': 'high',
            'INFO': 'medium'
        }
        return severity_map.get(semgrep_severity.upper(), 'medium')
