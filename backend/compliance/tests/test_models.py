"""
Tests for compliance models.

Tests:
- ComplianceEvaluation status transitions
- ComplianceScore grade calculation
- RuleResult storage
"""
import pytest
from django.utils import timezone
from compliance.models import ComplianceEvaluation, ComplianceScore, RuleResult


# ============================================
# ComplianceEvaluation Tests
# ============================================

@pytest.mark.django_db
class TestComplianceEvaluation:
    """Tests for the ComplianceEvaluation model."""
    
    def test_create_evaluation(self, repository, builtin_standard, admin_user):
        """Test creating an evaluation."""
        evaluation = ComplianceEvaluation.objects.create(
            repository=repository,
            standard=builtin_standard,
            triggered_by=admin_user,
            status='pending',
            commit_hash='abc123'
        )
        
        assert evaluation.id is not None
        assert evaluation.status == 'pending'
        assert evaluation.started_at is None
    
    def test_evaluation_str(self, pending_evaluation):
        """Test __str__ method."""
        s = str(pending_evaluation)
        assert 'test-repo' in s
        assert 'Test Standard' in s
    
    def test_mark_running(self, pending_evaluation):
        """Test mark_running sets status and started_at."""
        assert pending_evaluation.started_at is None
        
        pending_evaluation.mark_running()
        
        assert pending_evaluation.status == 'running'
        assert pending_evaluation.started_at is not None
    
    def test_mark_completed(self, pending_evaluation):
        """Test mark_completed sets status and completed_at."""
        pending_evaluation.mark_running()
        pending_evaluation.mark_completed()
        
        assert pending_evaluation.status == 'completed'
        assert pending_evaluation.completed_at is not None
    
    def test_mark_failed(self, pending_evaluation):
        """Test mark_failed sets status and error message."""
        error_msg = "Something went wrong"
        pending_evaluation.mark_failed(error_msg)
        
        assert pending_evaluation.status == 'failed'
        assert pending_evaluation.error_message == error_msg
    
    def test_duration_seconds_completed(self, completed_evaluation):
        """Test duration_seconds calculation for completed evaluation."""
        duration = completed_evaluation.duration_seconds
        
        # Should be a number >= 0
        assert duration is not None
        assert duration >= 0
    
    def test_duration_seconds_not_started(self, pending_evaluation):
        """Test duration_seconds returns None when not started."""
        duration = pending_evaluation.duration_seconds
        
        assert duration is None


# ============================================
# RuleResult Tests
# ============================================

@pytest.mark.django_db
class TestRuleResult:
    """Tests for the RuleResult model."""
    
    def test_create_rule_result(self, pending_evaluation, compliance_rule):
        """Test creating a rule result."""
        result = RuleResult.objects.create(
            evaluation=pending_evaluation,
            rule=compliance_rule,
            passed=True,
            message="README.md exists",
            evidence={"path": "README.md", "exists": True},
            weight=5
        )
        
        assert result.id is not None
        assert result.passed is True
    
    def test_rule_result_str(self, pending_evaluation, compliance_rule):
        """Test __str__ method."""
        result = RuleResult.objects.create(
            evaluation=pending_evaluation,
            rule=compliance_rule,
            passed=True,
            message="OK",
            weight=5
        )
        
        s = str(result)
        assert 'README Check' in s or 'PASS' in s.upper() or 'True' in s
    
    def test_weighted_score_passed(self, pending_evaluation, compliance_rule):
        """Test weighted_score returns weight when passed."""
        result = RuleResult.objects.create(
            evaluation=pending_evaluation,
            rule=compliance_rule,
            passed=True,
            message="OK",
            weight=7
        )
        
        assert result.weighted_score == 7
    
    def test_weighted_score_failed(self, pending_evaluation, compliance_rule):
        """Test weighted_score returns 0 when failed."""
        result = RuleResult.objects.create(
            evaluation=pending_evaluation,
            rule=compliance_rule,
            passed=False,
            message="FAIL",
            weight=7
        )
        
        assert result.weighted_score == 0


# ============================================
# ComplianceScore Tests
# ============================================

@pytest.mark.django_db
class TestComplianceScore:
    """Tests for the ComplianceScore model."""
    
    def test_create_score(self, pending_evaluation):
        """Test creating a compliance score."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=85.5,
            passed_count=8,
            failed_count=2,
            total_rules=10,
            passed_weight=17,
            total_weight=20
        )
        
        assert score.evaluation_id is not None
        assert score.total_score == 85.5
    
    def test_score_str(self, completed_evaluation):
        """Test __str__ method."""
        score = completed_evaluation.score
        s = str(score)
        
        assert '85' in s or 'B' in s  # Score or grade
    
    def test_grade_A(self, pending_evaluation):
        """Test grade A for score >= 90."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=95.0,
            passed_count=10,
            failed_count=0,
            total_rules=10,
            passed_weight=20,
            total_weight=20
        )
        
        assert score.grade == 'A'
    
    def test_grade_B(self, pending_evaluation):
        """Test grade B for score >= 80."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=85.0,
            passed_count=8,
            failed_count=2,
            total_rules=10,
            passed_weight=17,
            total_weight=20
        )
        
        assert score.grade == 'B'
    
    def test_grade_C(self, pending_evaluation):
        """Test grade C for score >= 70."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=75.0,
            passed_count=7,
            failed_count=3,
            total_rules=10,
            passed_weight=15,
            total_weight=20
        )
        
        assert score.grade == 'C'
    
    def test_grade_D(self, pending_evaluation):
        """Test grade D for score >= 60."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=65.0,
            passed_count=6,
            failed_count=4,
            total_rules=10,
            passed_weight=13,
            total_weight=20
        )
        
        assert score.grade == 'D'
    
    def test_grade_F(self, pending_evaluation):
        """Test grade F for score < 60."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=45.0,
            passed_count=4,
            failed_count=6,
            total_rules=10,
            passed_weight=9,
            total_weight=20
        )
        
        assert score.grade == 'F'
    
    def test_calculate_from_results(self, repository, standard_with_rules, admin_user):
        """Test calculate_from_results creates score from rule results."""
        from compliance.models import ComplianceEvaluation
        
        # Create a new evaluation with standard that has rules
        evaluation = ComplianceEvaluation.objects.create(
            repository=repository,
            standard=standard_with_rules,
            triggered_by=admin_user,
            status='pending'
        )
        
        # Get rules from the standard
        rules = list(standard_with_rules.rules.all())
        
        # Create rule results - first 2 pass, last 1 fails
        RuleResult.objects.create(
            evaluation=evaluation,
            rule=rules[0],
            passed=True,
            message="PASS",
            weight=rules[0].weight
        )
        RuleResult.objects.create(
            evaluation=evaluation,
            rule=rules[1],
            passed=True,
            message="PASS",
            weight=rules[1].weight
        )
        RuleResult.objects.create(
            evaluation=evaluation,
            rule=rules[2],
            passed=False,
            message="FAIL",
            weight=rules[2].weight
        )
        
        # Calculate score
        score = ComplianceScore.calculate_from_results(evaluation)
        
        assert score is not None
        assert score.passed_count == 2
        assert score.failed_count == 1
        assert score.total_rules == 3


# ============================================
# Edge Case Tests
# ============================================

@pytest.mark.django_db
class TestComplianceModelsEdgeCases:
    """Edge case tests for compliance models."""
    
    def test_grade_boundary_90(self, pending_evaluation):
        """Test grade boundary at exactly 90."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=90.0,
            passed_count=9,
            failed_count=1,
            total_rules=10,
            passed_weight=18,
            total_weight=20
        )
        
        assert score.grade == 'A'
    
    def test_grade_boundary_80(self, pending_evaluation):
        """Test grade boundary at exactly 80."""
        score = ComplianceScore.objects.create(
            evaluation=pending_evaluation,
            total_score=80.0,
            passed_count=8,
            failed_count=2,
            total_rules=10,
            passed_weight=16,
            total_weight=20
        )
        
        assert score.grade == 'B'
    
    def test_calculate_from_results_empty(self, pending_evaluation):
        """Test calculate_from_results with no results."""
        # No rule results exist
        score = ComplianceScore.calculate_from_results(pending_evaluation)
        
        assert float(score.total_score) == 0.0
        assert score.passed_count == 0
        assert score.total_rules == 0
