"""
Tests for base classes in the compliance rule engine.

Tests:
- RuleResult dataclass
- RepositorySnapshot methods
- RuleRegistry registration and lookup
"""
import pytest
from compliance.rules.base import (
    RuleResult,
    RepositorySnapshot,
    BaseRule,
    RuleRegistry
)

# Import rule modules to register them with RuleRegistry
from compliance.rules import file_rules, folder_rules, config_rules  # noqa: F401
from compliance.rules import hygiene_rules, pattern_rules  # noqa: F401



# ============================================
# RuleResult Tests
# ============================================

class TestRuleResult:
    """Tests for the RuleResult dataclass."""
    
    def test_rule_result_creation_passed(self):
        """Test creating a passing RuleResult."""
        result = RuleResult(
            passed=True,
            message="Check passed",
            evidence={"path": "README.md", "exists": True}
        )
        
        assert result.passed is True
        assert result.message == "Check passed"
        assert result.evidence["path"] == "README.md"
    
    def test_rule_result_creation_failed(self):
        """Test creating a failing RuleResult."""
        result = RuleResult(
            passed=False,
            message="Check failed",
            evidence={"path": "README.md", "exists": False}
        )
        
        assert result.passed is False
        assert result.message == "Check failed"
    
    def test_rule_result_default_evidence(self):
        """Test RuleResult with default empty evidence."""
        result = RuleResult(passed=True, message="OK")
        
        assert result.evidence == {}
    
    def test_rule_result_to_dict(self):
        """Test RuleResult serialization to dictionary."""
        result = RuleResult(
            passed=True,
            message="Test message",
            evidence={"key": "value"}
        )
        
        d = result.to_dict()
        
        assert d == {
            'passed': True,
            'message': "Test message",
            'evidence': {"key": "value"}
        }


# ============================================
# RepositorySnapshot Tests
# ============================================

class TestRepositorySnapshot:
    """Tests for the RepositorySnapshot dataclass."""
    
    def test_snapshot_creation_empty(self, empty_snapshot):
        """Test creating an empty snapshot."""
        assert empty_snapshot.files == []
        assert empty_snapshot.folders == []
        assert empty_snapshot.file_contents == {}
    
    def test_snapshot_creation_with_data(self, sample_snapshot):
        """Test creating a snapshot with data."""
        assert 'README.md' in sample_snapshot.files
        assert '.github' in sample_snapshot.folders
        assert 'README.md' in sample_snapshot.file_contents
    
    def test_file_exists_positive(self, sample_snapshot):
        """Test file_exists returns True for existing file."""
        assert sample_snapshot.file_exists('README.md') is True
        assert sample_snapshot.file_exists('LICENSE') is True
    
    def test_file_exists_negative(self, sample_snapshot):
        """Test file_exists returns False for non-existing file."""
        assert sample_snapshot.file_exists('NONEXISTENT.md') is False
        assert sample_snapshot.file_exists('.env') is False
    
    def test_file_exists_with_leading_slash(self, sample_snapshot):
        """Test file_exists handles leading ./ correctly."""
        assert sample_snapshot.file_exists('./README.md') is True
    
    def test_folder_exists_positive(self, sample_snapshot):
        """Test folder_exists returns True for existing folder."""
        assert sample_snapshot.folder_exists('.github') is True
        assert sample_snapshot.folder_exists('.github/workflows') is True
    
    def test_folder_exists_negative(self, sample_snapshot):
        """Test folder_exists returns False for non-existing folder."""
        assert sample_snapshot.folder_exists('nonexistent') is False
        assert sample_snapshot.folder_exists('.circleci') is False
    
    def test_folder_exists_with_trailing_slash(self, sample_snapshot):
        """Test folder_exists handles trailing slash correctly."""
        assert sample_snapshot.folder_exists('.github/') is True
    
    def test_get_file_content_existing(self, sample_snapshot):
        """Test get_file_content returns content for existing file."""
        content = sample_snapshot.get_file_content('README.md')
        assert content is not None
        assert '# Test Project' in content
    
    def test_get_file_content_nonexisting(self, sample_snapshot):
        """Test get_file_content returns None for non-existing file."""
        content = sample_snapshot.get_file_content('NONEXISTENT.md')
        assert content is None
    
    def test_has_any_file_matching_exact(self, sample_snapshot):
        """Test pattern matching with exact filename."""
        matches = sample_snapshot.has_any_file_matching(['README.md'])
        assert 'README.md' in matches
    
    def test_has_any_file_matching_glob(self, sample_snapshot):
        """Test pattern matching with glob patterns."""
        matches = sample_snapshot.has_any_file_matching(['*.py'])
        assert 'src/main.py' in matches
        assert 'src/utils.py' in matches
    
    def test_has_any_file_matching_no_match(self, sample_snapshot):
        """Test pattern matching returns empty for no matches."""
        matches = sample_snapshot.has_any_file_matching(['*.xyz'])
        assert matches == []


# ============================================
# RuleRegistry Tests
# ============================================

class TestRuleRegistry:
    """Tests for the RuleRegistry class."""
    
    def test_registry_has_file_exists(self):
        """Test that file_exists rule is registered."""
        rule_class = RuleRegistry.get_rule_class('file_exists')
        assert rule_class is not None
        assert rule_class.__name__ == 'FileExistsRule'
    
    def test_registry_has_file_forbidden(self):
        """Test that file_forbidden rule is registered."""
        rule_class = RuleRegistry.get_rule_class('file_forbidden')
        assert rule_class is not None
        assert rule_class.__name__ == 'FileForbiddenRule'
    
    def test_registry_returns_none_for_unknown(self):
        """Test that unknown rule type returns None."""
        rule_class = RuleRegistry.get_rule_class('unknown_type')
        assert rule_class is None
    
    def test_create_rule_success(self):
        """Test creating a rule instance via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='file_exists',
            name='Test Rule',
            config={'path': 'README.md'},
            weight=5
        )
        
        assert rule is not None
        assert rule.name == 'Test Rule'
        assert rule.config == {'path': 'README.md'}
        assert rule.weight == 5
    
    def test_create_rule_failure(self):
        """Test creating rule with unknown type returns None."""
        rule = RuleRegistry.create_rule(
            rule_type='nonexistent',
            name='Test',
            config={},
            weight=5
        )
        
        assert rule is None
    
    def test_available_types_not_empty(self):
        """Test that available_types returns registered types."""
        types = RuleRegistry.available_types()
        
        assert len(types) > 0
        assert 'file_exists' in types
        assert 'file_forbidden' in types
