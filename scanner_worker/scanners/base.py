from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScanner(ABC):
    
    @abstractmethod
    def scan(self, workspace_path: str) -> List[Dict]:
        pass
    
    def _map_severity(self, original_severity: str) -> str:
        severity_map = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'critical': 'critical',
        }
        return severity_map.get(original_severity.lower(), 'medium')
