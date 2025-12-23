"""
Additional rule implementations for pattern matching, config checks, and hygiene.
"""
from fnmatch import fnmatch
import json
import logging
from typing import Any, Dict

from .base import BaseRule, RuleRegistry, RuleResult, RepositorySnapshot

logger = logging.getLogger(__name__)


@RuleRegistry.register('pattern_match')
class PatternMatchRule(BaseRule):
    """
    Rule to check for files or content matching a pattern.
    
    Config options:
        pattern: Glob pattern to match files (e.g., "*.test.js", "src/**/*.py")
        should_exist: If True (default), at least one file must match.
                      If False, no files should match.
    """
    
    rule_type = 'pattern_match'
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        pattern = self.config.get('pattern', '*')
        should_exist = self.config.get('should_exist', True)
        
        # Find matching files
        matching_files = []
        for file_path in snapshot.files:
            # Match against filename or full path
            if fnmatch(file_path, pattern) or fnmatch(file_path.split('/')[-1], pattern):
                matching_files.append(file_path)
        
        has_matches = len(matching_files) > 0
        
        if should_exist:
            if has_matches:
                return RuleResult(
                    passed=True,
                    message=f"Found {len(matching_files)} file(s) matching pattern '{pattern}'.",
                    evidence={
                        'pattern': pattern,
                        'should_exist': should_exist,
                        'matching_files': matching_files[:10],  # Limit to first 10
                        'match_count': len(matching_files),
                    }
                )
            else:
                return RuleResult(
                    passed=False,
                    message=f"No files found matching pattern '{pattern}'.",
                    evidence={
                        'pattern': pattern,
                        'should_exist': should_exist,
                        'matching_files': [],
                        'match_count': 0,
                    }
                )
        else:
            # Pattern should NOT exist
            if has_matches:
                return RuleResult(
                    passed=False,
                    message=f"Found {len(matching_files)} file(s) matching forbidden pattern '{pattern}'.",
                    evidence={
                        'pattern': pattern,
                        'should_exist': should_exist,
                        'matching_files': matching_files[:10],
                        'match_count': len(matching_files),
                    }
                )
            else:
                return RuleResult(
                    passed=True,
                    message=f"No files match forbidden pattern '{pattern}'.",
                    evidence={
                        'pattern': pattern,
                        'should_exist': should_exist,
                        'matching_files': [],
                        'match_count': 0,
                    }
                )


@RuleRegistry.register('config_check')
class ConfigCheckRule(BaseRule):
    """
    Rule to check configuration files for specific keys/values.
    
    Config options:
        file: Config file path (e.g., "package.json")
        key: Key to check (dot notation for nested, e.g., "scripts.test")
        expected_value: Optional expected value. If not provided, just checks key exists.
    """
    
    rule_type = 'config_check'
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        file_path = self.config.get('file', '')
        key = self.config.get('key', '')
        expected_value = self.config.get('expected_value')
        
        if not file_path:
            return RuleResult(
                passed=False,
                message="No config file specified.",
                evidence={'error': 'missing_file_config'}
            )
        
        # Check if file exists
        if not snapshot.file_exists(file_path):
            return RuleResult(
                passed=False,
                message=f"Config file '{file_path}' not found.",
                evidence={
                    'file': file_path,
                    'key': key,
                    'file_exists': False,
                }
            )
        
        # Try to parse the file content
        content = snapshot.get_file_content(file_path)
        if content is None:
            return RuleResult(
                passed=False,
                message=f"Could not read config file '{file_path}'.",
                evidence={
                    'file': file_path,
                    'key': key,
                    'readable': False,
                }
            )
        
        # Try to parse as JSON (most common config format)
        try:
            if file_path.endswith('.json'):
                config_data = json.loads(content)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                # Basic YAML support - just check if key string exists
                if key and key in content:
                    return RuleResult(
                        passed=True,
                        message=f"Key '{key}' found in '{file_path}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'found': True,
                        }
                    )
                else:
                    return RuleResult(
                        passed=False,
                        message=f"Key '{key}' not found in '{file_path}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'found': False,
                        }
                    )
            else:
                # For other files, just check if content contains key
                if key and key in content:
                    return RuleResult(
                        passed=True,
                        message=f"Key '{key}' found in '{file_path}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'found': True,
                        }
                    )
                return RuleResult(
                    passed=False,
                    message=f"Key '{key}' not found in '{file_path}'.",
                    evidence={
                        'file': file_path,
                        'key': key,
                        'found': False,
                    }
                )
        except json.JSONDecodeError:
            return RuleResult(
                passed=False,
                message=f"Could not parse '{file_path}' as JSON.",
                evidence={
                    'file': file_path,
                    'parse_error': True,
                }
            )
        
        # Navigate to the key using dot notation
        if key:
            value = config_data
            key_parts = key.split('.')
            for part in key_parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return RuleResult(
                        passed=False,
                        message=f"Key '{key}' not found in '{file_path}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'found': False,
                        }
                    )
            
            # Key exists, check value if expected_value provided
            if expected_value is not None:
                if str(value) == str(expected_value):
                    return RuleResult(
                        passed=True,
                        message=f"Key '{key}' has expected value '{expected_value}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'actual_value': value,
                            'expected_value': expected_value,
                            'match': True,
                        }
                    )
                else:
                    return RuleResult(
                        passed=False,
                        message=f"Key '{key}' has value '{value}', expected '{expected_value}'.",
                        evidence={
                            'file': file_path,
                            'key': key,
                            'actual_value': value,
                            'expected_value': expected_value,
                            'match': False,
                        }
                    )
            else:
                return RuleResult(
                    passed=True,
                    message=f"Key '{key}' exists in '{file_path}'.",
                    evidence={
                        'file': file_path,
                        'key': key,
                        'found': True,
                        'value': value,
                    }
                )
        else:
            # No key specified, just check file exists and is valid
            return RuleResult(
                passed=True,
                message=f"Config file '{file_path}' exists and is valid.",
                evidence={
                    'file': file_path,
                    'valid': True,
                }
            )


@RuleRegistry.register('hygiene')
class HygieneRule(BaseRule):
    """
    Rule to check repository hygiene practices.
    
    Config options:
        check_type: Type of hygiene check to perform:
            - 'branch_protection': Check for branch protection indicators
            - 'code_owners': Check for CODEOWNERS file
            - 'ci_config': Check for CI/CD configuration
            - 'gitignore': Check for .gitignore file
    """
    
    rule_type = 'hygiene'
    
    CI_CONFIG_PATHS = [
        '.github/workflows',
        '.gitlab-ci.yml',
        '.circleci/config.yml',
        '.travis.yml',
        'Jenkinsfile',
        'azure-pipelines.yml',
        '.drone.yml',
    ]
    
    CODEOWNERS_PATHS = [
        'CODEOWNERS',
        '.github/CODEOWNERS',
        'docs/CODEOWNERS',
    ]
    
    def check(self, snapshot: RepositorySnapshot) -> RuleResult:
        check_type = self.config.get('check_type', 'gitignore')
        
        if check_type == 'gitignore':
            return self._check_gitignore(snapshot)
        elif check_type == 'ci_config':
            return self._check_ci_config(snapshot)
        elif check_type == 'code_owners':
            return self._check_code_owners(snapshot)
        elif check_type == 'branch_protection':
            return self._check_branch_protection(snapshot)
        else:
            return RuleResult(
                passed=False,
                message=f"Unknown hygiene check type: '{check_type}'.",
                evidence={'check_type': check_type, 'error': 'unknown_check_type'}
            )
    
    def _check_gitignore(self, snapshot: RepositorySnapshot) -> RuleResult:
        if snapshot.file_exists('.gitignore'):
            return RuleResult(
                passed=True,
                message=".gitignore file exists.",
                evidence={'file': '.gitignore', 'exists': True}
            )
        return RuleResult(
            passed=False,
            message=".gitignore file not found.",
            evidence={'file': '.gitignore', 'exists': False}
        )
    
    def _check_ci_config(self, snapshot: RepositorySnapshot) -> RuleResult:
        for path in self.CI_CONFIG_PATHS:
            if snapshot.file_exists(path) or snapshot.folder_exists(path):
                return RuleResult(
                    passed=True,
                    message=f"CI/CD configuration found: {path}",
                    evidence={
                        'ci_config': path,
                        'exists': True,
                        'checked_paths': self.CI_CONFIG_PATHS,
                    }
                )
        return RuleResult(
            passed=False,
            message="No CI/CD configuration found.",
            evidence={
                'ci_config': None,
                'exists': False,
                'checked_paths': self.CI_CONFIG_PATHS,
            }
        )
    
    def _check_code_owners(self, snapshot: RepositorySnapshot) -> RuleResult:
        for path in self.CODEOWNERS_PATHS:
            if snapshot.file_exists(path):
                return RuleResult(
                    passed=True,
                    message=f"CODEOWNERS file found: {path}",
                    evidence={
                        'codeowners': path,
                        'exists': True,
                        'checked_paths': self.CODEOWNERS_PATHS,
                    }
                )
        return RuleResult(
            passed=False,
            message="CODEOWNERS file not found.",
            evidence={
                'codeowners': None,
                'exists': False,
                'checked_paths': self.CODEOWNERS_PATHS,
            }
        )
    
    def _check_branch_protection(self, snapshot: RepositorySnapshot) -> RuleResult:
        # Branch protection is typically configured via GitHub API, not files.
        # We can only check for indicators like CODEOWNERS or protected branch config files.
        has_codeowners = any(snapshot.file_exists(p) for p in self.CODEOWNERS_PATHS)
        has_branch_ruleset = snapshot.folder_exists('.github/rulesets') or snapshot.file_exists('.github/branch-protection.json')
        
        if has_codeowners or has_branch_ruleset:
            indicators = []
            if has_codeowners:
                indicators.append('CODEOWNERS')
            if has_branch_ruleset:
                indicators.append('branch-protection config')
            
            return RuleResult(
                passed=True,
                message=f"Branch protection indicators found: {', '.join(indicators)}",
                evidence={
                    'indicators': indicators,
                    'has_codeowners': has_codeowners,
                    'has_ruleset': has_branch_ruleset,
                }
            )
        return RuleResult(
            passed=False,
            message="No branch protection indicators found. Consider adding CODEOWNERS.",
            evidence={
                'indicators': [],
                'has_codeowners': False,
                'has_ruleset': False,
            }
        )
