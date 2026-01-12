import pytest


class TestSemgrepSeverityMapping:
    
    def test_error_is_critical(self):
        from scanners.semgrep_scanner import SemgrepScanner
        scanner = SemgrepScanner()
        assert scanner._map_severity('ERROR') == 'critical'
    
    def test_warning_is_high(self):
        from scanners.semgrep_scanner import SemgrepScanner
        scanner = SemgrepScanner()
        assert scanner._map_severity('WARNING') == 'high'


class TestGitleaksSeverityMapping:
    
    def test_aws_key_is_critical(self):
        from scanners.gitleaks_scanner import GitleaksScanner
        scanner = GitleaksScanner()
        assert scanner._determine_severity('aws-secret-key', '') == 'critical'
    
    def test_generic_secret_is_high(self):
        from scanners.gitleaks_scanner import GitleaksScanner
        scanner = GitleaksScanner()
        assert scanner._determine_severity('generic-api-key', 'api key found') == 'high'


class TestTrivySeverityMapping:
    
    def test_critical_stays_critical(self):
        from scanners.trivy_scanner import TrivyScanner
        scanner = TrivyScanner()
        assert scanner._map_severity('CRITICAL') == 'critical'
    
    def test_unknown_defaults_to_medium(self):
        from scanners.trivy_scanner import TrivyScanner
        scanner = TrivyScanner()
        assert scanner._map_severity('UNKNOWN') == 'medium'
