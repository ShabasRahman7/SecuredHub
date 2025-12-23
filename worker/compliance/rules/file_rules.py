"""
File-related compliance rules.

Rules for checking file existence and forbidden files.
"""
from typing import Dict, Any, List
from .base import BaseRule, RuleResult, RuleRegistry, RepositorySnapshot


@RuleRegistry.register('file_exists')
class FileExistsRule(BaseRule):
    """
    Rule to check if a required file exists.
    
    Config options:
        path: Primary file path to check (e.g., "README.md")
        alternatives: Optional list of alternative paths (e.g., ["readme.md", "Readme.md"])
    """
    
    rule_type = 'file_exists'
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        # Get primary path and alternatives
        primary_path = self.config.get('path', '')
        alternatives = self.config.get('alternatives', [])
        
        all_paths = [primary_path] + alternatives
        
        # Check all possible paths
        for path in all_paths:
            if not path:
                continue
            if snapshot.file_exists(path):
                return RuleResult(
                    passed=True,
                    message=f"Required file '{path}' exists.",
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
            message=f"Required file {paths_str} not found.",
            evidence={
                'path': primary_path,
                'alternatives': alternatives,
                'exists': False,
                'checked_paths': all_paths,
            }
        )


@RuleRegistry.register('file_forbidden')
class FileForbiddenRule(BaseRule):
    """
    Rule to check that a forbidden file does NOT exist.
    
    Config options:
        path: Primary file path that should not exist (e.g., ".env")
        patterns: Optional list of glob patterns to check (e.g., ["*.key", "secrets/*"])
    """
    
    rule_type = 'file_forbidden'
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        primary_path = self.config.get('path', '')
        patterns = self.config.get('patterns', [])
        
        found_files = []
        
        # Check primary path
        if primary_path and snapshot.file_exists(primary_path):
            found_files.append(primary_path)
        
        # Check patterns
        if patterns:
            matches = snapshot.has_any_file_matching(patterns)
            found_files.extend(matches)
        
        # Remove duplicates
        found_files = list(set(found_files))
        
        if found_files:
            files_str = ', '.join(f"'{f}'" for f in found_files[:5])
            if len(found_files) > 5:
                files_str += f" and {len(found_files) - 5} more"
            
            return RuleResult(
                passed=False,
                message=f"Forbidden file(s) found: {files_str}. These should not be committed.",
                evidence={
                    'path': primary_path,
                    'patterns': patterns,
                    'found_files': found_files,
                    'exists': True,
                }
            )
        
        return RuleResult(
            passed=True,
            message=f"No forbidden files found (checked: '{primary_path}'" + 
                    (f" and patterns {patterns}" if patterns else "") + ").",
            evidence={
                'path': primary_path,
                'patterns': patterns,
                'found_files': [],
                'exists': False,
            }
        )
