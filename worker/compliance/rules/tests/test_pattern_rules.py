"""
Tests for pattern matching rules.

Tests:
- PatternMatchRule: Checks for files matching glob patterns
"""
import pytest
from compliance.rules.pattern_rules import PatternMatchRule
from compliance.rules.base import RepositorySnapshot, RuleRegistry


class TestPatternMatchRuleShouldExist:
    """Tests for PatternMatchRule when pattern should match files."""
    
    def test_pattern_match_finds_exact_file(self, sample_snapshot):
        """Test pattern finds exact filename match."""
        rule = PatternMatchRule(
            name="README Check",
            config={'pattern': 'README.md', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert 'README.md' in result.evidence['matching_files']
    
    def test_pattern_match_glob_extension(self, sample_snapshot):
        """Test pattern matches files by extension."""
        rule = PatternMatchRule(
            name="Python Files",
            config={'pattern': '*.py', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['match_count'] >= 1
    
    def test_pattern_match_fails_no_match(self, sample_snapshot):
        """Test pattern fails when no files match."""
        rule = PatternMatchRule(
            name="Ruby Files",
            config={'pattern': '*.rb', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
        assert result.evidence['match_count'] == 0
    
    def test_pattern_match_test_files(self, sample_snapshot):
        """Test pattern finds test files."""
        rule = PatternMatchRule(
            name="Test Files",
            config={'pattern': 'test_*.py', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_pattern_match_empty_snapshot(self, empty_snapshot):
        """Test pattern fails on empty repository."""
        rule = PatternMatchRule(
            name="Any File",
            config={'pattern': '*', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False


class TestPatternMatchRuleShouldNotExist:
    """Tests for PatternMatchRule when pattern should NOT match files."""
    
    def test_forbidden_pattern_passes(self, sample_snapshot):
        """Test forbidden pattern passes when no matches."""
        rule = PatternMatchRule(
            name="No Log Files",
            config={'pattern': '*.log', 'should_exist': False},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_forbidden_pattern_fails(self, insecure_snapshot):
        """Test forbidden pattern fails when files match."""
        rule = PatternMatchRule(
            name="No Secret Files",
            config={'pattern': '*.json', 'should_exist': False},
            weight=5
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False
        assert result.evidence['match_count'] >= 1
    
    def test_forbidden_env_file(self, insecure_snapshot):
        """Test forbidden pattern catches .env file."""
        rule = PatternMatchRule(
            name="No .env",
            config={'pattern': '.env', 'should_exist': False},
            weight=10
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False


class TestPatternMatchRuleEdgeCases:
    """Edge case tests for pattern matching rules."""
    
    def test_default_should_exist_is_true(self, sample_snapshot):
        """Test default should_exist is True."""
        rule = PatternMatchRule(
            name="README",
            config={'pattern': 'README.md'},  # No should_exist
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        # Should pass because README.md exists and should_exist defaults to True
        assert result.passed is True
    
    def test_default_pattern_is_star(self, sample_snapshot):
        """Test default pattern is * (matches anything)."""
        rule = PatternMatchRule(
            name="Any Files",
            config={},  # No pattern specified
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        # Should match all files
        assert result.passed is True
    
    def test_matching_files_limited_to_10(self):
        """Test matching_files evidence is limited to 10."""
        # Create snapshot with many files
        files = [f'file{i}.py' for i in range(20)]
        snapshot = RepositorySnapshot(files=files, folders=[], file_contents={})
        
        rule = PatternMatchRule(
            name="Python Files",
            config={'pattern': '*.py', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
        assert len(result.evidence['matching_files']) <= 10
        assert result.evidence['match_count'] == 20
    
    def test_pattern_via_registry(self, sample_snapshot):
        """Test PatternMatchRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='pattern_match',
            name='Registry Test',
            config={'pattern': '*.md', 'should_exist': True},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
