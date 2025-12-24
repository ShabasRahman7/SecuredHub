"""
Tests for folder-related compliance rules.

Tests:
- FolderExistsRule: Checks for required folders
"""
import pytest
from compliance.rules.folder_rules import FolderExistsRule
from compliance.rules.base import RepositorySnapshot, RuleRegistry


class TestFolderExistsRule:
    """Tests for the FolderExistsRule class."""
    
    def test_folder_exists_passes_when_present(self, sample_snapshot):
        """Test rule passes when required folder exists."""
        rule = FolderExistsRule(
            name="GitHub Folder",
            config={'path': '.github'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['exists'] is True
        assert result.evidence['path'] == '.github'
    
    def test_folder_exists_nested_folder(self, sample_snapshot):
        """Test rule passes for nested folder path."""
        rule = FolderExistsRule(
            name="GitHub Workflows",
            config={'path': '.github/workflows'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
    
    def test_folder_exists_fails_when_missing(self, sample_snapshot):
        """Test rule fails when required folder is missing."""
        rule = FolderExistsRule(
            name="Docker Folder",
            config={'path': 'docker'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
        assert 'not found' in result.message.lower()
    
    def test_folder_exists_fails_on_empty_snapshot(self, empty_snapshot):
        """Test rule fails on empty repository."""
        rule = FolderExistsRule(
            name="Tests Folder",
            config={'path': 'tests'},
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False
    
    def test_folder_exists_with_alternatives_primary_passes(self, sample_snapshot):
        """Test rule passes when primary folder exists."""
        rule = FolderExistsRule(
            name="Test Folder",
            config={
                'path': 'tests',
                'alternatives': ['test', 'spec', '__tests__']
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['path'] == 'tests'
    
    def test_folder_exists_with_alternatives_fallback(self):
        """Test rule passes when alternative folder exists."""
        snapshot = RepositorySnapshot(
            files=['spec/test_main.rb'],
            folders=['spec'],
            file_contents={}
        )
        
        rule = FolderExistsRule(
            name="Test Folder",
            config={
                'path': 'tests',
                'alternatives': ['test', 'spec', '__tests__']
            },
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
        assert result.evidence['path'] == 'spec'
    
    def test_folder_exists_all_alternatives_missing(self, empty_snapshot):
        """Test rule fails when all alternatives are missing."""
        rule = FolderExistsRule(
            name="Test Folder",
            config={
                'path': 'tests',
                'alternatives': ['test', 'spec']
            },
            weight=5
        )
        
        result = rule.check(empty_snapshot)
        
        assert result.passed is False
        assert 'alternatives' in result.evidence
    
    def test_folder_exists_via_registry(self, sample_snapshot):
        """Test FolderExistsRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='folder_exists',
            name='Registry Test',
            config={'path': '.github'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
