"""
Compliance evaluator orchestrator.

Coordinates the execution of all rules in a standard against a repository.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .rules.base import BaseRule, RuleResult, RuleRegistry, RepositorySnapshot

# Import rules to register them
from .rules import file_rules, folder_rules, extended_rules  # noqa: F401

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """
    Result of evaluating a repository against a standard.
    
    Contains all individual rule results and summary statistics.
    """
    rule_results: List[Dict[str, Any]] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    passed_weight: int = 0
    total_weight: int = 0
    score: float = 0.0
    
    def add_result(self, rule_id: int, rule_name: str, rule_type: str, 
                   weight: int, result: RuleResult):
        """Add a rule result to the evaluation."""
        self.rule_results.append({
            'rule_id': rule_id,
            'rule_name': rule_name,
            'rule_type': rule_type,
            'weight': weight,
            'passed': result.passed,
            'message': result.message,
            'evidence': result.evidence,
        })
        
        self.total_count += 1
        self.total_weight += weight
        
        if result.passed:
            self.passed_count += 1
            self.passed_weight += weight
        else:
            self.failed_count += 1
    
    def calculate_score(self):
        """Calculate the final compliance score."""
        if self.total_weight > 0:
            self.score = round((self.passed_weight / self.total_weight) * 100, 2)
        else:
            self.score = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'rule_results': self.rule_results,
            'passed_count': self.passed_count,
            'failed_count': self.failed_count,
            'total_count': self.total_count,
            'passed_weight': self.passed_weight,
            'total_weight': self.total_weight,
            'score': self.score,
        }


class Evaluator:
    """
    Orchestrates compliance evaluation of a repository.
    
    Takes a list of rules and a repository snapshot,
    executes all rules, and aggregates results.
    """
    
    def __init__(self, rules: List[Dict[str, Any]]):
        """
        Initialize the evaluator with rules.
        
        Args:
            rules: List of rule dictionaries with:
                - id: Rule ID from database
                - name: Rule name
                - rule_type: Type of rule (e.g., 'file_exists')
                - check_config: Configuration for the rule
                - weight: Weight in score calculation
        """
        self.rules = rules
        self._rule_instances: List[tuple] = []
        
        # Create rule instances
        for rule_data in rules:
            rule_type = rule_data.get('rule_type')
            rule = RuleRegistry.create_rule(
                rule_type=rule_type,
                name=rule_data.get('name', ''),
                config=rule_data.get('check_config', {}),
                weight=rule_data.get('weight', 5)
            )
            
            if rule:
                self._rule_instances.append((rule_data, rule))
            else:
                logger.warning(f"Unknown rule type: {rule_type} for rule {rule_data.get('name')}")
    
    def evaluate(self, snapshot: RepositorySnapshot, 
                 progress_callback: Optional[callable] = None) -> EvaluationResult:
        """
        Execute evaluation against the repository snapshot.
        
        Args:
            snapshot: Repository snapshot to evaluate
            progress_callback: Optional callback(current, total, message) for progress updates
            
        Returns:
            EvaluationResult with all rule results and score
        """
        result = EvaluationResult()
        total_rules = len(self._rule_instances)
        
        for idx, (rule_data, rule) in enumerate(self._rule_instances):
            try:
                # Execute the rule check
                rule_result = rule.check(snapshot)
                
                # Add to results
                result.add_result(
                    rule_id=rule_data.get('id'),
                    rule_name=rule_data.get('name', ''),
                    rule_type=rule_data.get('rule_type', ''),
                    weight=rule_data.get('weight', 5),
                    result=rule_result
                )
                
                logger.debug(
                    f"Rule '{rule.name}': {'PASS' if rule_result.passed else 'FAIL'} - "
                    f"{rule_result.message}"
                )
                
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")
                # Create a failed result for errors
                error_result = RuleResult(
                    passed=False,
                    message=f"Error during check: {str(e)}",
                    evidence={'error': str(e)}
                )
                result.add_result(
                    rule_id=rule_data.get('id'),
                    rule_name=rule_data.get('name', ''),
                    rule_type=rule_data.get('rule_type', ''),
                    weight=rule_data.get('weight', 5),
                    result=error_result
                )
            
            # Report progress
            if progress_callback:
                try:
                    progress = int((idx + 1) / total_rules * 100)
                    progress_callback(idx + 1, total_rules, f"Evaluated {rule.name}")
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
        
        # Calculate final score
        result.calculate_score()
        
        logger.info(
            f"Evaluation complete: {result.passed_count}/{result.total_count} rules passed, "
            f"score: {result.score}%"
        )
        
        return result
