
import subprocess
import json
import os
from typing import List, Dict

from .base import BaseScanner


class TrivyScanner(BaseScanner):

    
    def scan(self, workspace_path: str) -> List[Dict]:
        findings = []
        
        try:
            cmd = [
                'trivy', 'fs',
                '--scanners', 'vuln',
                '--format', 'json',
                '--quiet',
                workspace_path
            ]
            

            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for large projects
            )
            

            
            if result.stdout:
                data = json.loads(result.stdout)
                findings = self._parse_results(data, workspace_path)
                
        except subprocess.TimeoutExpired:
            print(f"Trivy scan timed out for {workspace_path}")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Trivy output: {e}")
        except Exception as e:
            print(f"Trivy scan error: {e}")
        
        return findings
    
    def _parse_results(self, data: Dict, workspace_path: str) -> List[Dict]:
        findings = []
        

        for result in data.get('Results', []):
            target = result.get('Target', '')
            

            if target.startswith(workspace_path):
                target = os.path.relpath(target, workspace_path)
            
            for vuln in result.get('Vulnerabilities', []) or []:
                findings.append(self._normalize_finding(vuln, target))
        
        return findings
    
    def _normalize_finding(self, vuln: Dict, file_path: str) -> Dict:
        vuln_id = vuln.get('VulnerabilityID', 'UNKNOWN')
        pkg_name = vuln.get('PkgName', 'unknown-package')
        installed_version = vuln.get('InstalledVersion', 'unknown')
        fixed_version = vuln.get('FixedVersion', '')
        
        title = vuln.get('Title', f'{vuln_id} in {pkg_name}')
        

        description_parts = [
            vuln.get('Description', 'No description available.'),
            f"\nAffected package: {pkg_name}@{installed_version}"
        ]
        if fixed_version:
            description_parts.append(f"Fixed in: {fixed_version}")
        
        description = ' '.join(description_parts)
        
        severity = self._map_severity(vuln.get('Severity', 'UNKNOWN'))
        

        code_snippet = f"{pkg_name}=={installed_version}"
        if fixed_version:
            code_snippet += f"  # Upgrade to {fixed_version}"
        
        return {
            'tool': 'trivy',
            'rule_id': vuln_id,
            'title': title,
            'description': description,
            'severity': severity,
            'file_path': file_path,
            'line_number': None,
            'raw_output': {
                'code': code_snippet,
                'vuln_id': vuln_id,
                'package_name': pkg_name,
                'installed_version': installed_version,
                'fixed_version': fixed_version,
                'severity': vuln.get('Severity'),
                'cvss_score': vuln.get('CVSS', {}).get('nvd', {}).get('V3Score') if vuln.get('CVSS') else None,
                'references': vuln.get('References', [])[:5],
                'published_date': vuln.get('PublishedDate'),
                'last_modified': vuln.get('LastModifiedDate')
            }
        }
    
    def _map_severity(self, trivy_severity: str) -> str:
        severity_map = {
            'CRITICAL': 'critical',
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low',
            'UNKNOWN': 'medium'
        }
        return severity_map.get(trivy_severity.upper(), 'medium')
