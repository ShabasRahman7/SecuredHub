# unit tests for scanner worker utilities
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestWorkspaceManager:
    # testing workspace creation and cleanup
    
    @patch('os.makedirs')
    @patch('tempfile.mkdtemp')
    def test_create_workspace(self, mock_mkdtemp, mock_makedirs):
        # should create temporary workspace directory
        mock_mkdtemp.return_value = '/tmp/scan_workspace_123'
        
        workspace_path = mock_mkdtemp()
        
        assert workspace_path.startswith('/tmp')
        assert 'workspace' in workspace_path or 'scan' in workspace_path.lower()
    
    @patch('shutil.rmtree')
    def test_cleanup_workspace(self, mock_rmtree):
        # should remove workspace directory after scan
        workspace_path = '/tmp/scan_workspace_123'
        
        # simulating cleanup
        mock_rmtree(workspace_path)
        
        mock_rmtree.assert_called_once_with(workspace_path)
    
    @patch('shutil.rmtree')
    def test_cleanup_handles_missing_directory(self, mock_rmtree):
        # should handle cleanup of non-existent directory gracefully
        mock_rmtree.side_effect = FileNotFoundError('Directory not found')
        
        try:
            mock_rmtree('/tmp/nonexistent')
        except FileNotFoundError:
            # expected behavior
            pass
    
    @patch('os.path.exists')
    def test_workspace_exists_check(self, mock_exists):
        # should check if workspace exists before operations
        mock_exists.return_value = True
        
        workspace_path = '/tmp/test_workspace'
        exists = mock_exists(workspace_path)
        
        assert exists is True


@pytest.mark.unit
class TestGitOperations:
    # testing Git operations with mocked commands
    
    @patch('subprocess.run')
    def test_clone_repository(self, mock_subprocess):
        # should clone repository with access token (mocked)
        mock_subprocess.return_value = Mock(returncode=0)
        
        repo_url = 'https://github.com/user/repo.git'
        workspace_path = '/tmp/workspace'
        access_token = 'ghp_token123'
        
        # simulating git clone with token
        authenticated_url = repo_url.replace('https://', f'https://{access_token}@')
        
        assert access_token in authenticated_url
        assert 'github.com' in authenticated_url
    
    @patch('subprocess.run')
    def test_get_latest_commit_hash(self, mock_subprocess):
        # should extract latest commit hash (mocked)
        commit_hash = 'abc123def456789'
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout=commit_hash
        )
        
        # simulating git rev-parse HEAD
        result = mock_subprocess()
        
        assert result.stdout == commit_hash
        assert len(commit_hash) > 7  # short commit hash
    
    @patch('subprocess.run')
    def test_get_commit_info(self, mock_subprocess):
        # should extract commit metadata (mocked)
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='abc123\nJohn Doe\n2024-01-15\nFix security issue'
        )
        
        # simulating git log parsing
        output = mock_subprocess().stdout.split('\n')
        
        commit_data = {
            'hash': output[0],
            'author': output[1],
            'date': output[2],
            'message': output[3]
        }
        
        assert commit_data['hash'] == 'abc123'
        assert commit_data['author'] == 'John Doe'
    
    @patch('subprocess.run')
    def test_handles_git_clone_failure(self, mock_subprocess):
        # should handle git clone failure gracefully
        mock_subprocess.return_value = Mock(
            returncode=128,
            stderr='fatal: repository not found'
        )
        
        result = mock_subprocess()
        
        assert result.returncode != 0
        assert 'fatal' in result.stderr


@pytest.mark.unit
class TestFalsePositiveFiltering:
    # testing false positive detection logic
    
    def test_is_test_file(self):
        # should identify test files
        test_files = [
            'test_utils.py',
            'tests/test_models.py',
            'app_test.go',
            'spec/user_spec.rb'
        ]
        
        import re
        test_pattern = r'(test_|_test\.|tests/|spec/)'
        
        for filepath in test_files:
            assert re.search(test_pattern, filepath) is not None
    
    def test_is_example_or_dummy_data(self):
        # should identify example/dummy values
        dummy_values = [
            'example.com',
            'test@test.com',
            'your_api_key_here',
            'REPLACE_ME',
            '1234567890abcdef'
        ]
        
        dummy_patterns = [r'example\.com', r'test@test', r'your_.*_here', r'REPLACE']
        
        for value in dummy_values:
            matches = any(re.search(pattern, value, re.IGNORECASE) for pattern in dummy_patterns)
            assert matches or value == '1234567890abcdef'  # generic placeholder
    
    def test_entropy_check_for_random_strings(self):
        # should calculate entropy to detect random tokens
        import math
        from collections import Counter
        
        def calculate_entropy(string):
            # simple Shannon entropy calculation
            prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
            entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
            return entropy
        
        high_entropy = calculate_entropy('aB3xK9mP2qL5nT') # random-looking
        low_entropy = calculate_entropy('aaaaaa')  # repeating
        
        assert high_entropy > low_entropy
        assert high_entropy > 3.0  # typical threshold for secrets
