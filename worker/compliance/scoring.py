"""
Scoring calculator for compliance evaluations.

Provides utilities for calculating and interpreting compliance scores.
"""
from typing import Optional
from decimal import Decimal


def calculate_score(passed_weight: int, total_weight: int) -> Decimal:
    """
    Calculate compliance score as a percentage.
    
    Args:
        passed_weight: Sum of weights for passed rules
        total_weight: Sum of all rule weights
        
    Returns:
        Score as Decimal (0-100)
    """
    if total_weight <= 0:
        return Decimal('0.00')
    
    score = (Decimal(passed_weight) / Decimal(total_weight)) * 100
    return score.quantize(Decimal('0.01'))


def get_grade(score: float) -> str:
    """
    Convert a numeric score to a letter grade.
    
    Args:
        score: Numeric score (0-100)
        
    Returns:
        Letter grade (A, B, C, D, F)
    """
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'


def get_score_color(score: float) -> str:
    """
    Get a color code for the score (for UI rendering).
    
    Args:
        score: Numeric score (0-100)
        
    Returns:
        Color name (green, yellow, orange, red)
    """
    if score >= 80:
        return 'green'
    elif score >= 60:
        return 'yellow'
    elif score >= 40:
        return 'orange'
    else:
        return 'red'


def score_improvement_estimate(
    current_passed: int,
    current_failed: int,
    rules_to_fix: int,
    avg_weight: float = 7.0
) -> Optional[float]:
    """
    Estimate potential score improvement if certain rules are fixed.
    
    Args:
        current_passed: Current number of passed rules
        current_failed: Current number of failed rules
        rules_to_fix: Number of rules that will be fixed
        avg_weight: Average weight per rule (for estimation)
        
    Returns:
        Estimated new score, or None if calculation not possible
    """
    if rules_to_fix > current_failed:
        rules_to_fix = current_failed
    
    total_rules = current_passed + current_failed
    if total_rules == 0:
        return None
    
    # Estimate current total weight
    current_total_weight = total_rules * avg_weight
    
    # Current passed weight (estimate)
    current_passed_weight = current_passed * avg_weight
    
    # New passed weight after fixes
    new_passed_weight = current_passed_weight + (rules_to_fix * avg_weight)
    
    # Calculate new score
    new_score = (new_passed_weight / current_total_weight) * 100
    
    return round(new_score, 2)
