"""
Configuration check rule implementation.

Evaluates config files (JSON, YAML) for required keys and values.
"""
import json
import logging

from .base import BaseRule, RuleRegistry, RuleResult, RepositorySnapshot

logger = logging.getLogger(__name__)


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
