"""
Folder-related compliance rules.

Rules for checking folder/directory existence.
"""
from typing import Dict, Any, List
from .base import BaseRule, RuleResult, RuleRegistry, RepositorySnapshot


@RuleRegistry.register('folder_exists')
class FolderExistsRule(BaseRule):
    """
    Rule to check if a required folder exists.
    
    Config options:
        path: Primary folder path to check (e.g., ".github/workflows")
        alternatives: Optional list of alternative paths (e.g., ["test", "tests", "spec"])
    """
    
    rule_type = 'folder_exists'
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        primary_path = self.config.get('path', '')
        alternatives = self.config.get('alternatives', [])
        
        all_paths = [primary_path] + alternatives
        
        # Check all possible paths
        for path in all_paths:
            if not path:
                continue
            if snapshot.folder_exists(path):
                return RuleResult(
                    passed=True,
                    message=f"Required folder '{path}' exists.",
                    evidence={
                        'path': path,
                        'exists': True,
                        'checked_paths': all_paths,
                    }
                )
        
        # None found
        paths_str = f"'{primary_path}'" + (f" (or alternatives: {alternatives})" if alternatives else "")
        return RuleResult(
            passed=False,
            message=f"Required folder {paths_str} not found.",
            evidence={
                'path': primary_path,
                'alternatives': alternatives,
                'exists': False,
                'checked_paths': all_paths,
            }
        )
