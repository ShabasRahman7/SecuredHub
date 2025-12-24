"""
Repository hygiene rule implementation.

Checks for best practices like .gitignore, CI/CD config, CODEOWNERS, etc.
"""
import logging

from .base import BaseRule, RuleRegistry, RuleResult, RepositorySnapshot

logger = logging.getLogger(__name__)


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
