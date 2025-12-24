"""
Tests for hygiene rule implementation.

Tests:
- HygieneRule: Checks for gitignore, CI config, code owners, branch protection
"""
import pytest
from compliance.rules.hygiene_rules import HygieneRule
from compliance.rules.base import RepositorySnapshot, RuleRegistry


class TestHygieneRuleGitignore:
    """Tests for the gitignore hygiene check."""
    
    def test_gitignore_passes_when_present(self, sample_snapshot):
        """Test gitignore check passes when .gitignore exists."""
        rule = HygieneRule(
            name="Gitignore Check",
            config={'check_type': 'gitignore'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['exists'] is True
    
    def test_gitignore_fails_when_missing(self, empty_snapshot):
        """Test gitignore check fails when .gitignore is missing."""
        rule = HygieneRule(
            name="Gitignore Check",
            config={'check_type': 'gitignore'},
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False


class TestHygieneRuleCIConfig:
    """Tests for the CI/CD config hygiene check."""
    
    def test_ci_config_passes_with_github_workflows(self, sample_snapshot):
        """Test CI config check passes with GitHub workflows folder."""
        rule = HygieneRule(
            name="CI Config Check",
            config={'check_type': 'ci_config'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert '.github/workflows' in result.evidence['ci_config']
    
    def test_ci_config_passes_with_gitlab_ci(self):
        """Test CI config check passes with .gitlab-ci.yml."""
        snapshot = RepositorySnapshot(
            files=['README.md', '.gitlab-ci.yml'],
            folders=[],
            file_contents={}
        )
        
        rule = HygieneRule(
            name="CI Config Check",
            config={'check_type': 'ci_config'},
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
    
    def test_ci_config_fails_when_missing(self, minimal_snapshot):
        """Test CI config check fails when no CI config exists."""
        rule = HygieneRule(
            name="CI Config Check",
            config={'check_type': 'ci_config'},
            weight=5
        )
        
        result = rule.check(minimal_snapshot)
        
        assert result.passed is False


class TestHygieneRuleCodeOwners:
    """Tests for the CODEOWNERS hygiene check."""
    
    def test_code_owners_passes_when_present(self, sample_snapshot):
        """Test code owners check passes when CODEOWNERS exists."""
        rule = HygieneRule(
            name="Code Owners Check",
            config={'check_type': 'code_owners'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_code_owners_fails_when_missing(self, minimal_snapshot):
        """Test code owners check fails when CODEOWNERS is missing."""
        rule = HygieneRule(
            name="Code Owners Check",
            config={'check_type': 'code_owners'},
            weight=5
        )
        
        result = rule.check(minimal_snapshot)
        
        assert result.passed is False


class TestHygieneRuleBranchProtection:
    """Tests for the branch protection hygiene check."""
    
    def test_branch_protection_passes_with_codeowners(self, sample_snapshot):
        """Test branch protection passes when CODEOWNERS exists."""
        rule = HygieneRule(
            name="Branch Protection Check",
            config={'check_type': 'branch_protection'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['has_codeowners'] is True
    
    def test_branch_protection_fails_when_no_indicators(self, minimal_snapshot):
        """Test branch protection fails when no indicators exist."""
        rule = HygieneRule(
            name="Branch Protection Check",
            config={'check_type': 'branch_protection'},
            weight=5
        )
        
        result = rule.check(minimal_snapshot)
        
        assert result.passed is False


class TestHygieneRuleEdgeCases:
    """Edge case tests for hygiene rules."""
    
    def test_unknown_check_type(self, sample_snapshot):
        """Test rule fails gracefully with unknown check type."""
        rule = HygieneRule(
            name="Unknown Check",
            config={'check_type': 'unknown_type'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
        assert result.evidence.get('error') == 'unknown_check_type'
    
    def test_default_check_type_is_gitignore(self, sample_snapshot):
        """Test default check type is gitignore."""
        rule = HygieneRule(
            name="Default Check",
            config={},  # No check_type specified
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        # Default is gitignore, which should pass for sample_snapshot
        assert result.passed is True
    
    def test_hygiene_via_registry(self, sample_snapshot):
        """Test HygieneRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='hygiene',
            name='Registry Test',
            config={'check_type': 'gitignore'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
