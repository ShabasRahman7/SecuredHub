"""Secret scanner using regex patterns"""
import re
import os
import fnmatch
from typing import List, Dict
from .base import BaseScanner

class SecretScanner(BaseScanner):
    
    # common secret patterns
    PATTERNS = {
        'aws_access_key': {
            'pattern': r'AKIA[0-9A-Z]{16}',
            'description': 'AWS Access Key ID detected'
        },
        'aws_secret_key': {
            'pattern': r'aws_secret[_-]?key[\s:=]+[\'"]?([A-Za-z0-9/+=]{40})[\'"]?',
            'description': 'AWS Secret Access Key detected'
        },
        'github_token': {
            'pattern': r'gh[pousr]_[A-Za-z0-9]{36,}',
            'description': 'GitHub Personal Access Token detected'
        },
        'github_oauth': {
            'pattern': r'gho_[A-Za-z0-9]{36,}',
            'description': 'GitHub OAuth Token detected'
        },
        'generic_api_key': {
            'pattern': r'[aA][pP][iI][-_]?[kK][eE][yY][\s:=]+[\'"]?([a-zA-Z0-9_-]{20,})[\'"]?',
            'description': 'Generic API key pattern detected'
        },
        'private_key': {
            'pattern': r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
            'description': 'Private key detected'
        },
        'password_in_code': {
            'pattern': r'[pP][aA][sS][sS][wW][oO][rR][dD][\s:=]+[\'"]([^\'"]{8,})[\'"]',
            'description': 'Hardcoded password detected'
        },
        'slack_token': {
            'pattern': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}',
            'description': 'Slack token detected'
        },
        'jwt_token': {
            'pattern': r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
            'description': 'JWT token detected'
        }
    }
    
    # file extensions to scan
    SCANNABLE_EXTENSIONS = (
        '.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.yml', '.yaml',
        '.env', '.env.example', '.config', '.conf', '.xml', '.java',
        '.go', '.rb', '.php', '.c', '.cpp', '.h', '.sh', '.bash'
    )
    
    # directories to skip (including test directories)
    SKIP_DIRS = {
        '.git', 'node_modules', 'venv', 'env', '__pycache__',
        'dist', 'build', '.next', 'vendor', 'target',
        # testing directories - primary false positive source
        'tests', '__tests__', 'test', 'spec', 'specs',
        'fixtures', 'mocks', '__mocks__', 'testing',
        # documentation and examples
        'docs', 'examples', 'samples', 'demo',
        # backend/infrastructure code (DB drivers, migrations, etc)
        'backends', 'migrations'
    }
    
    # testing file patterns to skip
    SKIP_PATTERNS = [
        '*_test.py', 'test_*.py', '*test*.py',
        '*_spec.py', 'spec_*.py', '*spec*.py',
        '*.test.js', '*.spec.js', '*.test.ts', '*.spec.ts',
        '*_test.go', '*_spec.rb', 'test*.java'
    ]
    
    def should_skip_file(self, file_path: str) -> bool:
        # normalizing path separators
        normalized_path = file_path.replace('\\', '/')
        path_parts = normalized_path.split('/')
        
        # skipping if any directory in path is in SKIP_DIRS
        if any(part in self.SKIP_DIRS for part in path_parts):
            return True
        
        # skipping if filename matches test patterns
        filename = os.path.basename(file_path)
        if any(fnmatch.fnmatch(filename, pattern) for pattern in self.SKIP_PATTERNS):
            return True
        
        return False
    
    def scan(self, workspace_path: str) -> List[Dict]:
        findings = []
        
        for root, dirs, files in os.walk(workspace_path):
            # skipping ignored directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for file in files:
                if file.endswith(self.SCANNABLE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    
                    # skipping test files and non-production code
                    if self.should_skip_file(file_path):
                        continue
                    
                    findings.extend(self._scan_file(file_path, workspace_path))
        
        return findings
    
    def _scan_file(self, file_path: str, workspace_root: str) -> List[Dict]:
        findings = []
        rel_path = os.path.relpath(file_path, workspace_root)
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    findings.extend(
                        self._scan_line(line, rel_path, line_num)
                    )
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
        
        return findings
    
    def _scan_line(self, line: str, file_path: str, line_num: int) -> List[Dict]:
        findings = []
        
        for secret_type, pattern_info in self.PATTERNS.items():
            pattern = pattern_info['pattern']
            
            if re.search(pattern, line, re.IGNORECASE):
                # skipping if line is a comment (basic heuristic)
                stripped = line.strip()
                if stripped.startswith(('#', '//', '/*', '*', '<!--')):
                    continue
                
                findings.append({
                    'tool': 'secret_scanner',
                    'rule_id': f'SECRET_{secret_type.upper()}',
                    'title': f'Hardcoded Secret: {secret_type.replace("_", " ").title()}',
                    'description': pattern_info['description'],
                    'severity': 'critical',  # All secrets are critical
                    'file_path': file_path,
                    'line_number': line_num,
                    'raw_output': {
                        'secret_type': secret_type,
                        'line': line.strip()[:100],  # Truncate for safety
                        'pattern': pattern
                    }
                })
        
        return findings
