"""
Pattern matching rule implementation.

Checks for files matching glob patterns (e.g., test files, forbidden patterns).
"""
from fnmatch import fnmatch
import logging

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
