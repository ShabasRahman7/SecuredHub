"""
Tests for configuration check rules.

Tests:
- ConfigCheckRule: Checks JSON config files for keys and values
"""
import pytest
from compliance.rules.config_rules import ConfigCheckRule
from compliance.rules.base import RepositorySnapshot, RuleRegistry


class TestConfigCheckRule:
    """Tests for the ConfigCheckRule class."""
    
    def test_config_check_key_exists(self, sample_snapshot):
        """Test rule passes when key exists in JSON file."""
        rule = ConfigCheckRule(
            name="License Check",
            config={
                'file': 'package.json',
                'key': 'license'
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence['found'] is True or result.evidence.get('value') is not None
    
    def test_config_check_key_with_expected_value(self, sample_snapshot):
        """Test rule passes when key has expected value."""
        rule = ConfigCheckRule(
            name="License MIT",
            config={
                'file': 'package.json',
                'key': 'license',
                'expected_value': 'MIT'
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
        assert result.evidence.get('match') is True
    
    def test_config_check_key_wrong_value(self):
        """Test rule fails when key has wrong value."""
        snapshot = RepositorySnapshot(
            files=['package.json'],
            folders=[],
            file_contents={
                'package.json': '{"license": "GPL-3.0"}'
            }
        )
        
        rule = ConfigCheckRule(
            name="License MIT",
            config={
                'file': 'package.json',
                'key': 'license',
                'expected_value': 'MIT'
            },
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is False
        assert result.evidence['match'] is False
    
    def test_config_check_missing_key(self, sample_snapshot):
        """Test rule fails when key is missing."""
        rule = ConfigCheckRule(
            name="Scripts.Deploy Check",
            config={
                'file': 'package.json',
                'key': 'scripts.deploy'
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
    
    def test_config_check_nested_key(self):
        """Test rule works with dot notation for nested keys."""
        snapshot = RepositorySnapshot(
            files=['package.json'],
            folders=[],
            file_contents={
                'package.json': '{"scripts": {"test": "jest", "build": "webpack"}}'
            }
        )
        
        rule = ConfigCheckRule(
            name="Test Script Check",
            config={
                'file': 'package.json',
                'key': 'scripts.test'
            },
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
    
    def test_config_check_file_not_found(self, sample_snapshot):
        """Test rule fails when config file doesn't exist."""
        rule = ConfigCheckRule(
            name="Webpack Config",
            config={
                'file': 'webpack.config.js',
                'key': 'entry'
            },
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
        assert result.evidence['file_exists'] is False
    
    def test_config_check_invalid_json(self):
        """Test rule fails gracefully on invalid JSON."""
        snapshot = RepositorySnapshot(
            files=['package.json'],
            folders=[],
            file_contents={
                'package.json': 'not valid json {'
            }
        )
        
        rule = ConfigCheckRule(
            name="License Check",
            config={
                'file': 'package.json',
                'key': 'license'
            },
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is False
        assert result.evidence.get('parse_error') is True
    
    def test_config_check_no_file_config(self, sample_snapshot):
        """Test rule fails when file config is missing."""
        rule = ConfigCheckRule(
            name="Empty Config",
            config={'file': '', 'key': 'test'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is False
    
    def test_config_check_file_only_no_key(self):
        """Test rule passes when only checking file exists and is valid."""
        snapshot = RepositorySnapshot(
            files=['package.json'],
            folders=[],
            file_contents={
                'package.json': '{"name": "test"}'
            }
        )
        
        rule = ConfigCheckRule(
            name="Valid JSON",
            config={'file': 'package.json'},  # No key specified
            weight=5
        )
        
        result = rule.check(snapshot)
        
        assert result.passed is True
    
    def test_config_check_via_registry(self, sample_snapshot):
        """Test ConfigCheckRule can be created via registry."""
        rule = RuleRegistry.create_rule(
            rule_type='config_check',
            name='Registry Test',
            config={'file': 'package.json', 'key': 'name'},
            weight=5
        )
        
        result = rule.check(sample_snapshot)
        
        assert result.passed is True
