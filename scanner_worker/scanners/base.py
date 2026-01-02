"""Base scanner class for all scanner implementations"""
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScanner(ABC):
    
    @abstractmethod
    def scan(self, workspace_path: str) -> List[Dict]:
        # scan the workspace and return findings
        pass
    
    def _map_severity(self, original_severity: str) -> str:
        severity_map = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'critical': 'critical',
        }
        return severity_map.get(original_severity.lower(), 'medium')
