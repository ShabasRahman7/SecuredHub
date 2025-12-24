"""Unit tests for audits app models."""
import pytest
from audits.models import AuditLog, EvaluationEvidence


@pytest.mark.django_db
class TestAuditLog:
    """Tests for the AuditLog model."""
    
    def test_create_audit_log(self, tenant, admin_user):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            actor=admin_user,
            organization=tenant,
            action='create',
            description='Created a new repository'
        )
        
        assert log.id is not None
        assert log.action == 'create'
        assert log.created_at is not None
    
    def test_audit_log_str(self, tenant, admin_user):
        """Test __str__ method."""
        log = AuditLog.objects.create(
            actor=admin_user,
            organization=tenant,
            action='update',
            description='Updated repository settings'
        )
        
        s = str(log)
        assert admin_user.email in s
        assert 'update' in s.lower()
    
    def test_audit_log_no_actor(self, tenant):
        """Test audit log without actor (system action)."""
        log = AuditLog.objects.create(
            actor=None,  # System action
            organization=tenant,
            action='complete',
            description='Evaluation completed automatically'
        )
        
        s = str(log)
        assert 'System' in s
    
    def test_audit_log_with_metadata(self, tenant, admin_user):
        """Test audit log with metadata."""
        log = AuditLog.objects.create(
            actor=admin_user,
            organization=tenant,
            action='trigger',
            description='Triggered evaluation',
            metadata={'repository_id': 123, 'standard_id': 456}
        )
        
        assert log.metadata['repository_id'] == 123
        assert log.metadata['standard_id'] == 456
    
    def test_audit_log_with_ip_address(self, tenant, admin_user):
        """Test audit log with IP address."""
        log = AuditLog.objects.create(
            actor=admin_user,
            organization=tenant,
            action='create',
            description='Created from web',
            ip_address='192.168.1.1'
        )
        
        assert log.ip_address == '192.168.1.1'
    
    def test_action_choices(self, tenant, admin_user):
        """Test all action types can be created."""
        actions = ['create', 'update', 'delete', 'trigger', 'complete', 'fail', 'assign', 'unassign']
        
        for action in actions:
            log = AuditLog.objects.create(
                actor=admin_user,
                organization=tenant,
                action=action,
                description=f'Test {action} action'
            )
            assert log.action == action


@pytest.mark.django_db
class TestEvaluationEvidence:
    """Tests for the EvaluationEvidence model."""
    
    def test_create_evidence(self, completed_evaluation):
        """Test creating evidence entry."""
        evidence = EvaluationEvidence.objects.create(
            evaluation=completed_evaluation,
            evidence_type='file_check',
            target_path='README.md',
            captured_data={'exists': True, 'size_bytes': 1234}
        )
        
        assert evidence.id is not None
        assert evidence.evidence_type == 'file_check'
    
    def test_evidence_str(self, completed_evaluation):
        """Test __str__ method."""
        evidence = EvaluationEvidence.objects.create(
            evaluation=completed_evaluation,
            evidence_type='config_check',
            target_path='package.json'
        )
        
        s = str(evidence)
        assert 'config_check' in s.lower()
        assert 'package.json' in s
    
    def test_evidence_without_path(self, completed_evaluation):
        """Test evidence without target path (e.g., repo metadata)."""
        evidence = EvaluationEvidence.objects.create(
            evaluation=completed_evaluation,
            evidence_type='repo_metadata',
            captured_data={'stars': 100, 'forks': 50}
        )
        
        s = str(evidence)
        assert 'repo_metadata' in s.lower()
    
    def test_evidence_with_hash(self, completed_evaluation):
        """Test evidence with content hash."""
        evidence = EvaluationEvidence.objects.create(
            evaluation=completed_evaluation,
            evidence_type='file_check',
            target_path='README.md',
            captured_data={'exists': True},
            content_hash='abc123def456789'
        )
        
        assert evidence.content_hash == 'abc123def456789'
    
    def test_evidence_with_snippet(self, completed_evaluation):
        """Test evidence with content snippet."""
        evidence = EvaluationEvidence.objects.create(
            evaluation=completed_evaluation,
            evidence_type='file_check',
            target_path='LICENSE',
            captured_data={'exists': True},
            content_snippet='MIT License\n\nCopyright (c) 2024'
        )
        
        assert 'MIT License' in evidence.content_snippet
    
    def test_evidence_types(self, completed_evaluation):
        """Test all evidence types can be created."""
        types = ['file_check', 'folder_check', 'config_check', 'repo_metadata', 'commit_info']
        
        for etype in types:
            evidence = EvaluationEvidence.objects.create(
                evaluation=completed_evaluation,
                evidence_type=etype,
                captured_data={'test': True}
            )
            assert evidence.evidence_type == etype
