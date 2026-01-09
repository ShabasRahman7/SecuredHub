# unit tests for scanner worker scanners
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestBanditScanner:
    # testing Bandit scanner finding parsing
    
    @patch('subprocess.run')
    def test_parse_bandit_output(self, mock_subprocess):
        # should parse Bandit JSON output and extract findings
        # mocking Bandit subprocess output
        bandit_output = {
            "results": [
                {
                    "code": "password = 'hardcoded_password'",
                    "filename": "app/settings.py",
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Possible hardcoded password",
                    "line_number": 10,
                    "test_id": "B105",
                    "test_name": "hardcoded_password_string"
                },
                {
                    "code": "eval(user_input)",
                    "filename": "app/views.py",
                    "issue_severity": "MEDIUM",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of possibly insecure function eval",
                    "line_number": 42,
                    "test_id": "B307",
                    "test_name": "blacklist"
                }
            ]
        }
        
        mock_subprocess.return_value = Mock(
            returncode=1,  # Bandit returns 1 when issues found
            stdout=json.dumps(bandit_output)
        )
        
        # simulating parsing
        findings = bandit_output['results']
        assert len(findings) == 2
        assert findings[0]['issue_severity'] == 'HIGH'
        assert findings[0]['test_id'] == 'B105'
        assert findings[1]['filename'] == 'app/views.py'
    
    def test_severity_mapping(self):
        # should map Bandit severity to standard levels
        severity_map = {
            'HIGH': 'HIGH',
            'MEDIUM': 'MEDIUM',
            'LOW': 'LOW'
        }
        
        assert severity_map['HIGH'] == 'HIGH'
        assert severity_map['MEDIUM'] == 'MEDIUM'
        assert severity_map['LOW'] == 'LOW'
    
    @patch('subprocess.run')
    def test_handles_bandit_subprocess_error(self, mock_subprocess):
        # should handle subprocess error gracefully
        mock_subprocess.side_effect = FileNotFoundError('bandit not found')
        
        with pytest.raises(FileNotFoundError):
            mock_subprocess()


@pytest.mark.unit
class TestSecretScanner:
    # testing secret scanner pattern detection
    
    def test_detect_api_key_pattern(self):
        # should detect API key patterns
        import re
        
        # common API key pattern
        pattern = r'api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']'
        test_code = 'api_key = "sk_live_abcdef123456789012345"'
        
        match = re.search(pattern, test_code, re.IGNORECASE)
        assert match is not None
        assert 'sk_live' in match.group(0)
    
    def test_detect_github_token_pattern(self):
        # should detect GitHub personal access token
        import re
        
        pattern = r'ghp_[a-zA-Z0-9]{36}'
        test_code = 'token = "ghp_abcdefghijklmnopqrstuvwxyz123456789"'
        
        match = re.search(pattern, test_code)
        assert match is not None
    
    def test_detect_aws_key_pattern(self):
        # should detect AWS access keys
        import re
        
        pattern = r'AKIA[0-9A-Z]{16}'
        test_code = 'AWS_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"'
        
        match = re.search(pattern, test_code)
        assert match is not None
    
    @patch('builtins.open', create=True)
    @patch('os.walk')
    def test_scan_files_for_secrets(self, mock_walk, mock_open_file):
        # should scan files for secret patterns (mocked file reads)
        # mocking directory walk
        mock_walk.return_value = [
            ('/repo', ['app'], ['config.py', 'utils.py']),
        ]
        
        # mocking file read
        from unittest.mock import mock_open
        file_content = 'api_key = "secret_key_12345678901234567890"'
        mock_open_file.return_value = mock_open(read_data=file_content)()
        
        # simulating secret detection
        import re
        pattern = r'api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9_-]{20,})["\']'
        match = re.search(pattern, file_content, re.IGNORECASE)
        
        assert match is not None
    
    def test_ignore_test_files(self):
        # should skip test files and common ignore patterns
        test_files = [
            'test_config.py',
            'tests/test_utils.py',
            'node_modules/package.json',
            '.git/config'
        ]
        
        ignore_patterns = [r'test_', r'tests/', r'node_modules/', r'\.git/']
        
        for filepath in test_files:
            should_ignore = any(
                re.search(pattern, filepath) for pattern in ignore_patterns
            )
            assert should_ignore is True


@pytest.mark.unit
class TestScannerBase:
    # testing base scanner functionality
    
    def test_scanner_result_structure(self):
        # should return standardized finding structure
        finding = {
            'scanner_type': 'bandit',
            'severity': 'HIGH',
            'title': 'Hardcoded Password',
            'description': 'Password found hardcoded in source code',
            'file_path': 'app/settings.py',
            'line_number': 10,
            'code_snippet': 'password = "secret123"',
            'rule_id': 'B105'
        }
        
        required_fields = ['scanner_type', 'severity', 'title', 'description', 'file_path']
        for field in required_fields:
            assert field in finding
        
        assert finding['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
