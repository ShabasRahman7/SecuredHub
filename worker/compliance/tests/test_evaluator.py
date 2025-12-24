"""
Tests for the compliance evaluator.

Tests:
- EvaluationResult: Aggregates results and calculates scores
- Evaluator: Orchestrates rule execution
"""
import pytest
from compliance.evaluator import EvaluationResult, Evaluator
from compliance.rules.base import RuleResult, RepositorySnapshot


# ============================================
# EvaluationResult Tests
# ============================================

class TestEvaluationResult:
    """Tests for the EvaluationResult dataclass."""
    
    def test_empty_result(self):
        """Test empty EvaluationResult has correct defaults."""
        result = EvaluationResult()
        
        assert result.rule_results == []
        assert result.passed_count == 0
        assert result.failed_count == 0
        assert result.total_count == 0
        assert result.score == 0.0
    
    def test_add_result_passed(self):
        """Test adding a passed result updates counters correctly."""
        result = EvaluationResult()
        
        rule_result = RuleResult(passed=True, message="OK", evidence={})
        result.add_result(
            rule_id=1,
            rule_name="Test Rule",
            rule_type="file_exists",
            weight=5,
            result=rule_result
        )
        
        assert result.passed_count == 1
        assert result.failed_count == 0
        assert result.total_count == 1
        assert result.passed_weight == 5
        assert result.total_weight == 5
    
    def test_add_result_failed(self):
        """Test adding a failed result updates counters correctly."""
        result = EvaluationResult()
        
        rule_result = RuleResult(passed=False, message="Failed", evidence={})
        result.add_result(
            rule_id=1,
            rule_name="Test Rule",
            rule_type="file_exists",
            weight=5,
            result=rule_result
        )
        
        assert result.passed_count == 0
        assert result.failed_count == 1
        assert result.total_count == 1
        assert result.passed_weight == 0
        assert result.total_weight == 5
    
    def test_add_multiple_results(self):
        """Test adding multiple results."""
        result = EvaluationResult()
        
        # Add 3 passed, 2 failed with weights
        for i in range(3):
            result.add_result(
                rule_id=i,
                rule_name=f"Pass {i}",
                rule_type="file_exists",
                weight=5,
                result=RuleResult(passed=True, message="OK")
            )
        
        for i in range(2):
            result.add_result(
                rule_id=i + 3,
                rule_name=f"Fail {i}",
                rule_type="file_exists",
                weight=10,
                result=RuleResult(passed=False, message="FAIL")
            )
        
        assert result.passed_count == 3
        assert result.failed_count == 2
        assert result.total_count == 5
        assert result.passed_weight == 15  # 3 * 5
        assert result.total_weight == 35   # 15 + 20
    
    def test_calculate_score_perfect(self):
        """Test score calculation with all passed."""
        result = EvaluationResult()
        
        result.add_result(1, "R1", "file", 10, RuleResult(passed=True, message="OK"))
        result.add_result(2, "R2", "file", 10, RuleResult(passed=True, message="OK"))
        result.calculate_score()
        
        assert result.score == 100.0
    
    def test_calculate_score_zero(self):
        """Test score calculation with all failed."""
        result = EvaluationResult()
        
        result.add_result(1, "R1", "file", 10, RuleResult(passed=False, message="FAIL"))
        result.add_result(2, "R2", "file", 10, RuleResult(passed=False, message="FAIL"))
        result.calculate_score()
        
        assert result.score == 0.0
    
    def test_calculate_score_weighted(self):
        """Test score calculation respects weights."""
        result = EvaluationResult()
        
        # Pass rule with weight 10
        result.add_result(1, "High Weight", "file", 10, RuleResult(passed=True, message="OK"))
        # Fail rule with weight 5
        result.add_result(2, "Low Weight", "file", 5, RuleResult(passed=False, message="FAIL"))
        result.calculate_score()
        
        # Score = (10 / 15) * 100 = 66.67%
        expected_score = round((10 / 15) * 100, 2)
        assert result.score == expected_score
    
    def test_calculate_score_empty(self):
        """Test score calculation with no results doesn't divide by zero."""
        result = EvaluationResult()
        result.calculate_score()
        
        assert result.score == 0.0
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = EvaluationResult()
        result.add_result(1, "R1", "file_exists", 5, RuleResult(passed=True, message="OK"))
        result.calculate_score()
        
        d = result.to_dict()
        
        assert 'rule_results' in d
        assert 'passed_count' in d
        assert 'failed_count' in d
        assert 'score' in d
        assert len(d['rule_results']) == 1


# ============================================
# Evaluator Tests
# ============================================

class TestEvaluator:
    """Tests for the Evaluator class."""
    
    def test_evaluator_init_valid_rules(self, sample_rules):
        """Test evaluator initializes with valid rules."""
        evaluator = Evaluator(sample_rules)
        
        assert len(evaluator._rule_instances) == len(sample_rules)
    
    def test_evaluator_init_empty_rules(self):
        """Test evaluator initializes with empty rules list."""
        evaluator = Evaluator([])
        
        assert len(evaluator._rule_instances) == 0
    
    def test_evaluator_skips_unknown_rules(self):
        """Test evaluator skips rules with unknown type."""
        rules = [
            {'id': 1, 'name': 'Valid', 'rule_type': 'file_exists', 'check_config': {'path': 'README.md'}, 'weight': 5},
            {'id': 2, 'name': 'Invalid', 'rule_type': 'nonexistent_type', 'check_config': {}, 'weight': 5},
        ]
        
        evaluator = Evaluator(rules)
        
        # Only valid rule should be registered
        assert len(evaluator._rule_instances) == 1
    
    def test_evaluate_all_pass(self, sample_snapshot, sample_rules):
        """Test evaluation with all rules passing."""
        # sample_snapshot has README.md, LICENSE, no .env, and .github/workflows
        evaluator = Evaluator(sample_rules)
        result = evaluator.evaluate(sample_snapshot)
        
        assert result.total_count == len(sample_rules)
        assert result.passed_count == len(sample_rules)
        assert result.failed_count == 0
        assert result.score == 100.0
    
    def test_evaluate_mixed_results(self, minimal_snapshot, sample_rules):
        """Test evaluation with mixed pass/fail results."""
        evaluator = Evaluator(sample_rules)
        result = evaluator.evaluate(minimal_snapshot)
        
        # minimal_snapshot doesn't have README.md, LICENSE, or .github/workflows
        # but also doesn't have .env (so file_forbidden passes)
        assert result.total_count == len(sample_rules)
        assert result.passed_count < len(sample_rules)
        assert result.failed_count > 0
        assert 0 < result.score < 100
    
    def test_evaluate_empty_snapshot(self, empty_snapshot, sample_rules):
        """Test evaluation on empty repository."""
        evaluator = Evaluator(sample_rules)
        result = evaluator.evaluate(empty_snapshot)
        
        # All file_exists and folder_exists should fail
        # file_forbidden should pass (no .env)
        assert result.total_count == len(sample_rules)
        assert result.failed_count >= 1
    
    def test_evaluate_with_progress_callback(self, sample_snapshot, sample_rules):
        """Test evaluation calls progress callback."""
        progress_calls = []
        
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        evaluator = Evaluator(sample_rules)
        evaluator.evaluate(sample_snapshot, progress_callback=progress_callback)
        
        assert len(progress_calls) == len(sample_rules)
        # Verify progress calls are sequential
        for i, (current, total, _) in enumerate(progress_calls):
            assert current == i + 1
            assert total == len(sample_rules)
    
    def test_evaluate_handles_rule_exception(self):
        """Test evaluator continues when rule raises exception."""
        # Create a malformed rule config that might cause issues
        rules = [
            {'id': 1, 'name': 'Normal', 'rule_type': 'file_exists', 'check_config': {'path': 'README.md'}, 'weight': 5},
            {'id': 2, 'name': 'Bad Config', 'rule_type': 'config_check', 'check_config': {}, 'weight': 5},
        ]
        
        snapshot = RepositorySnapshot(files=['README.md'], folders=[], file_contents={})
        evaluator = Evaluator(rules)
        
        # Should not raise, should handle gracefully
        result = evaluator.evaluate(snapshot)
        
        assert result.total_count == 2
    
    def test_evaluate_calculates_score(self, sample_snapshot, sample_rules):
        """Test evaluate() calculates score automatically."""
        evaluator = Evaluator(sample_rules)
        result = evaluator.evaluate(sample_snapshot)
        
        # Score should be calculated (not 0 unless actually 0)
        # sample_snapshot should pass all rules
        assert result.score > 0
    
    def test_evaluate_rule_results_contain_details(self, sample_snapshot):
        """Test rule results contain expected details."""
        rules = [
            {'id': 42, 'name': 'README Check', 'rule_type': 'file_exists', 'check_config': {'path': 'README.md'}, 'weight': 7}
        ]
        
        evaluator = Evaluator(rules)
        result = evaluator.evaluate(sample_snapshot)
        
        assert len(result.rule_results) == 1
        rule_result = result.rule_results[0]
        
        assert rule_result['rule_id'] == 42
        assert rule_result['rule_name'] == 'README Check'
        assert rule_result['rule_type'] == 'file_exists'
        assert rule_result['weight'] == 7
        assert rule_result['passed'] is True
        assert 'message' in rule_result
        assert 'evidence' in rule_result


# ============================================
# Integration Tests
# ============================================

class TestEvaluatorIntegration:
    """Integration tests for the complete evaluation flow."""
    
    def test_full_evaluation_flow(self, sample_snapshot):
        """Test complete evaluation from rules to score."""
        rules = [
            {'id': 1, 'name': 'README', 'rule_type': 'file_exists', 'check_config': {'path': 'README.md'}, 'weight': 5},
            {'id': 2, 'name': 'LICENSE', 'rule_type': 'file_exists', 'check_config': {'path': 'LICENSE'}, 'weight': 5},
            {'id': 3, 'name': 'No .env', 'rule_type': 'file_forbidden', 'check_config': {'path': '.env'}, 'weight': 10},
            {'id': 4, 'name': 'CI/CD', 'rule_type': 'folder_exists', 'check_config': {'path': '.github/workflows'}, 'weight': 5},
            {'id': 5, 'name': 'Gitignore', 'rule_type': 'hygiene', 'check_config': {'check_type': 'gitignore'}, 'weight': 3},
        ]
        
        evaluator = Evaluator(rules)
        result = evaluator.evaluate(sample_snapshot)
        
        # All should pass for sample_snapshot
        assert result.passed_count == 5
        assert result.total_count == 5
        assert result.score == 100.0
        
        # Verify to_dict works
        data = result.to_dict()
        assert data['score'] == 100.0
