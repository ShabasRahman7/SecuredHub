"""
Shared pytest fixtures for SecuredHub worker tests.

This module provides reusable fixtures for:
- Repository snapshots
- Rule configurations
- Test data
"""
import pytest
from compliance.rules.base import RepositorySnapshot


# ============================================
# Repository Snapshot Fixtures
# ============================================

@pytest.fixture
def sample_snapshot():
    """
    Create a typical repository snapshot with common files.
    Represents a well-structured project.
    """
    return RepositorySnapshot(
        files=[
            'README.md',
            'LICENSE',
            'CONTRIBUTING.md',
            '.github/workflows/ci.yml',
            '.github/CODEOWNERS',
            'src/main.py',
            'src/utils.py',
            'tests/test_main.py',
            'package.json',
            '.gitignore',
        ],
        folders=[
            '.github',
            '.github/workflows',
            'src',
            'tests',
        ],
        file_contents={
            'README.md': '# Test Project\n\nA sample project for testing.',
            'LICENSE': 'MIT License\n\nCopyright (c) 2024',
            'package.json': '{"name": "test-project", "version": "1.0.0", "license": "MIT"}',
            '.gitignore': 'node_modules/\n*.log\n.env',
        },
        metadata={
            'default_branch': 'main',
            'has_issues': True,
            'has_wiki': False,
            'stargazers_count': 42,
            'forks_count': 10,
        },
        commit_hash='abc123def456',
        branch='main'
    )


@pytest.fixture
def empty_snapshot():
    """
    Create an empty repository snapshot.
    Represents a brand new, empty repository.
    """
    return RepositorySnapshot(
        files=[],
        folders=[],
        file_contents={},
        metadata={},
        commit_hash='000000000000',
        branch='main'
    )


@pytest.fixture
def minimal_snapshot():
    """
    Create a minimal repository snapshot.
    Has only basic files, missing recommended ones.
    """
    return RepositorySnapshot(
        files=[
            'index.js',
            '.gitignore',
        ],
        folders=[],
        file_contents={
            'index.js': 'console.log("Hello World");',
        },
        metadata={
            'default_branch': 'main',
        },
        commit_hash='def456abc789',
        branch='main'
    )


@pytest.fixture
def insecure_snapshot():
    """
    Create a snapshot with security issues.
    Contains files that should not be in a repository.
    """
    return RepositorySnapshot(
        files=[
            'README.md',
            '.env',                    # Should not exist
            'secrets.json',            # Should not exist
            'config/database.key',     # Should not exist
            'src/main.py',
        ],
        folders=[
            'config',
            'src',
        ],
        file_contents={
            '.env': 'DATABASE_URL=postgres://user:pass@localhost/db',
            'secrets.json': '{"api_key": "sk-1234567890"}',
        },
        metadata={},
        commit_hash='bad123bad456',
        branch='main'
    )


@pytest.fixture
def snapshot_with_ci():
    """
    Create a snapshot with CI/CD configuration.
    """
    return RepositorySnapshot(
        files=[
            'README.md',
            '.github/workflows/ci.yml',
            '.github/workflows/deploy.yml',
            '.github/dependabot.yml',
        ],
        folders=[
            '.github',
            '.github/workflows',
        ],
        file_contents={
            '.github/workflows/ci.yml': 'name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest',
        },
        metadata={},
        commit_hash='ci1234567890',
        branch='main'
    )


# ============================================
# Rule Configuration Fixtures
# ============================================

@pytest.fixture
def file_exists_rule_config():
    """Configuration for a file_exists rule."""
    return {
        'id': 1,
        'name': 'README Check',
        'rule_type': 'file_exists',
        'check_config': {'path': 'README.md'},
        'weight': 5
    }


@pytest.fixture
def file_forbidden_rule_config():
    """Configuration for a file_forbidden rule."""
    return {
        'id': 2,
        'name': 'No .env File',
        'rule_type': 'file_forbidden',
        'check_config': {'path': '.env'},
        'weight': 8
    }


@pytest.fixture
def folder_exists_rule_config():
    """Configuration for a folder_exists rule."""
    return {
        'id': 3,
        'name': 'GitHub Workflows',
        'rule_type': 'folder_exists',
        'check_config': {'path': '.github/workflows'},
        'weight': 4
    }


@pytest.fixture
def sample_rules():
    """Collection of sample rules for testing the evaluator."""
    return [
        {
            'id': 1,
            'name': 'README Check',
            'rule_type': 'file_exists',
            'check_config': {'path': 'README.md'},
            'weight': 5
        },
        {
            'id': 2,
            'name': 'LICENSE Check',
            'rule_type': 'file_exists',
            'check_config': {'path': 'LICENSE'},
            'weight': 5
        },
        {
            'id': 3,
            'name': 'No .env File',
            'rule_type': 'file_forbidden',
            'check_config': {'path': '.env'},
            'weight': 10
        },
        {
            'id': 4,
            'name': 'CI Workflow',
            'rule_type': 'folder_exists',
            'check_config': {'path': '.github/workflows'},
            'weight': 5
        },
    ]
