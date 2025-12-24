"""
Tests for file-related compliance rules.

Tests:
- FileExistsRule: Checks for required files
- FileForbiddenRule: Checks for forbidden files
"""
import pytest
from compliance.rules.file_rules import FileExistsRule, FileForbiddenRule
from compliance.rules.base import RuleRegistry


# ============================================
# FileExistsRule Tests
# ============================================

class TestFileExistsRule:
    """Tests for the FileExistsRule class."""
    
    def test_file_exists_passes_when_present(self, sample_snapshot):
        """Test rule passes when required file exists."""
        rule = FileExistsRule(
            name="README Check",
            config={'path': 'README.md'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert 'exists' in result.message.lower()
        assert result.evidence['exists'] is True
        assert result.evidence['path'] == 'README.md'
    
    def test_file_exists_fails_when_missing(self, sample_snapshot):
        """Test rule fails when required file is missing."""
        rule = FileExistsRule(
            name="Missing File Check",
            config={'path': 'CHANGELOG.md'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
        assert 'not found' in result.message.lower()
        assert result.evidence['exists'] is False
    
    def test_file_exists_fails_on_empty_snapshot(self, empty_snapshot):
        """Test rule fails on empty repository."""
        rule = FileExistsRule(
            name="README Check",
            config={'path': 'README.md'},
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False
    
    def test_file_exists_with_alternatives_primary_passes(self, sample_snapshot):
        """Test rule passes when primary path exists."""
        rule = FileExistsRule(
            name="License Check",
            config={
                'path': 'LICENSE',
                'alternatives': ['license.txt', 'LICENSE.md']
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['path'] == 'LICENSE'
    
    def test_file_exists_with_alternatives_fallback(self):
        """Test rule passes when alternative path exists."""
        # Create snapshot with only alternative
        from compliance.rules.base import RepositorySnapshot
        snapshot = RepositorySnapshot(
            files=['license.txt'],
            folders=[],
            file_contents={}
        )
        
        rule = FileExistsRule(
            name="License Check",
            config={
                'path': 'LICENSE',
                'alternatives': ['license.txt', 'LICENSE.md']
            },
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
        assert result.evidence['path'] == 'license.txt'
    
    def test_file_exists_all_alternatives_missing(self, empty_snapshot):
        """Test rule fails when all alternatives are missing."""
        rule = FileExistsRule(
            name="License Check",
            config={
                'path': 'LICENSE',
                'alternatives': ['license.txt', 'LICENSE.md']
            },
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False
        assert 'alternatives' in result.evidence
    
    def test_file_exists_via_registry(self, sample_snapshot):
        """Test FileExistsRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='file_exists',
            name='Registry Test',
            config={'path': 'README.md'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True


# ============================================
# FileForbiddenRule Tests
# ============================================

class TestFileForbiddenRule:
    """Tests for the FileForbiddenRule class."""
    
    def test_forbidden_passes_when_absent(self, sample_snapshot):
        """Test rule passes when forbidden file is not present."""
        rule = FileForbiddenRule(
            name="No .env File",
            config={'path': '.env'},
            weight=8
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['found_files'] == []
    
    def test_forbidden_fails_when_present(self, insecure_snapshot):
        """Test rule fails when forbidden file is present."""
        rule = FileForbiddenRule(
            name="No .env File",
            config={'path': '.env'},
            weight=8
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False
        assert '.env' in result.evidence['found_files']
        assert 'forbidden' in result.message.lower()
    
    def test_forbidden_passes_on_empty_snapshot(self, empty_snapshot):
        """Test rule passes on empty repository."""
        rule = FileForbiddenRule(
            name="No secrets",
            config={'path': 'secrets.json'},
            weight=8
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is True
    
    def test_forbidden_with_patterns_passes(self, sample_snapshot):
        """Test rule with patterns passes when no matches."""
        rule = FileForbiddenRule(
            name="No Key Files",
            config={
                'path': '.env',
                'patterns': ['*.key', '*.pem', 'secrets/*']
            },
            weight=10
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_forbidden_with_patterns_fails(self, insecure_snapshot):
        """Test rule with patterns fails when pattern matches."""
        rule = FileForbiddenRule(
            name="No Secrets",
            config={
                'path': '.env',
                'patterns': ['*.key', 'secrets.json']
            },
            weight=10
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False
        # Should find .env and secrets.json
        found = result.evidence['found_files']
        assert '.env' in found or 'secrets.json' in found
    
    def test_forbidden_empty_path_with_patterns(self, insecure_snapshot):
        """Test rule with only patterns (no primary path)."""
        rule = FileForbiddenRule(
            name="No Key Files",
            config={
                'path': '',
                'patterns': ['*.key']
            },
            weight=10
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False
        assert 'config/database.key' in result.evidence['found_files']
    
    def test_forbidden_via_registry(self, sample_snapshot):
        """Test FileForbiddenRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='file_forbidden',
            name='Registry Test',
            config={'path': '.env'},
            weight=8
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True


# ============================================
# Edge Case Tests
# ============================================

class TestFileRulesEdgeCases:
    """Edge case tests for file rules."""
    
    def test_empty_config_path(self, sample_snapshot):
        """Test handling of empty path in config."""
        rule = FileExistsRule(
            name="Empty Path",
            config={'path': ''},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        # Should fail - no path to check
        assert result.passed is False
    
    def test_nested_path_exists(self, sample_snapshot):
        """Test checking for nested file paths."""
        rule = FileExistsRule(
            name="CI Config",
            config={'path': '.github/workflows/ci.yml'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_nested_path_forbidden(self, insecure_snapshot):
        """Test forbidden rule with nested paths."""
        rule = FileForbiddenRule(
            name="No Database Keys",
            config={'path': 'config/database.key'},
            weight=10
        )
        
        result = rule.check(insecure_snapshot)
        
        assert result.passed is False
