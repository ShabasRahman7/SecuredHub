import pytest
from scans.models import Scan, ScanFinding


@pytest.mark.django_db
class TestScan:
    
    def test_scan_defaults_to_queued(self, repository, user):
        scan = Scan.objects.create(repository=repository, triggered_by=user)
        assert scan.status == 'queued'
        assert scan.progress == 0
    
    def test_scan_str(self, scan):
        assert 'Scan' in str(scan)


@pytest.mark.django_db
class TestScanFinding:
    
    def test_finding_stored_correctly(self, finding):
        assert finding.tool == 'semgrep'
        assert finding.severity == 'high'
        assert finding.file_path == 'config.py'
    
    def test_findings_count(self, scan):
        ScanFinding.objects.create(
            scan=scan,
            tool='gitleaks',
            rule_id='github-token',
            title='GitHub Token',
            description='Token found',
            severity='critical',
            file_path='secrets.py'
        )
        assert scan.findings.count() == 1
