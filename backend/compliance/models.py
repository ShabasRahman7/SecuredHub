"""
Models for compliance evaluations and rule results.

This module defines:
- ComplianceEvaluation: A single evaluation run (replaces Scan)
- RuleResult: Pass/fail result for each rule in an evaluation
- ComplianceScore: Calculated score per evaluation
"""
from django.db import models
from django.utils import timezone


class ComplianceEvaluation(models.Model):
    """
    A single compliance evaluation run for a repository against a standard.
    
    This replaces the old Scan model. Instead of scanning for vulnerabilities,
    we evaluate against a defined set of compliance rules.
    """
    
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    )
    
    repository = models.ForeignKey(
        'repositories.Repository',
        on_delete=models.CASCADE,
        related_name='compliance_evaluations',
        db_index=True
    )
    
    standard = models.ForeignKey(
        'standards.ComplianceStandard',
        on_delete=models.CASCADE,
        related_name='evaluations',
        db_index=True
    )
    
    triggered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_evaluations',
        help_text="User who triggered this evaluation"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Git metadata captured at evaluation time
    commit_hash = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="Git commit hash at time of evaluation"
    )
    
    branch = models.CharField(
        max_length=100,
        default='main',
        help_text="Branch evaluated"
    )
    
    # Error handling
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if evaluation failed"
    )
    
    # Celery task tracking
    task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Celery task ID"
    )
    
    class Meta:
        db_table = 'cpl_evaluations'
        verbose_name = 'Compliance Evaluation'
        verbose_name_plural = 'Compliance Evaluations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'status']),
            models.Index(fields=['repository', 'standard', '-created_at']),
        ]
    
    def __str__(self):
        return f"Eval #{self.id} - {self.repository.name} ({self.standard.name})"
    
    def mark_running(self):
        """Mark the evaluation as running."""
        self.status = self.STATUS_RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self):
        """Mark the evaluation as completed."""
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message: str):
        """Mark the evaluation as failed with an error message."""
        self.status = self.STATUS_FAILED
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    @property
    def duration_seconds(self):
        """Calculate evaluation duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or timezone.now()
        return (end_time - self.started_at).total_seconds()


class RuleResult(models.Model):
    """
    Result of evaluating a single rule in a compliance evaluation.
    
    For each rule in the standard, we store:
    - Whether it passed or failed
    - Evidence captured during the check
    - The specific message/reason
    """
    
    evaluation = models.ForeignKey(
        ComplianceEvaluation,
        on_delete=models.CASCADE,
        related_name='rule_results',
        db_index=True
    )
    
    rule = models.ForeignKey(
        'standards.ComplianceRule',
        on_delete=models.CASCADE,
        related_name='results',
        db_index=True
    )
    
    passed = models.BooleanField(
        help_text="Whether the rule check passed"
    )
    
    # Evidence captured during the check
    # Examples:
    # - file_exists: {"file_path": "README.md", "exists": true, "size_bytes": 1234}
    # - file_forbidden: {"file_path": ".env", "exists": false}
    # - config_check: {"file": "package.json", "key": "license", "value": "MIT", "expected": "MIT"}
    evidence = models.JSONField(
        default=dict,
        help_text="Evidence captured during the rule check"
    )
    
    message = models.TextField(
        blank=True,
        help_text="Human-readable message explaining the result"
    )
    
    # Cached weight from the rule (in case rule weight changes later)
    weight = models.PositiveIntegerField(
        help_text="Weight of this rule at time of evaluation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cpl_rule_results'
        verbose_name = 'Rule Result'
        verbose_name_plural = 'Rule Results'
        ordering = ['evaluation', 'rule__order']
        unique_together = ('evaluation', 'rule')
    
    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{status} {self.rule.name} (weight: {self.weight})"
    
    @property
    def weighted_score(self):
        """Return the weighted score contribution (weight if passed, 0 if failed)."""
        return self.weight if self.passed else 0


class ComplianceScore(models.Model):
    """
    Computed compliance score for an evaluation.
    
    This is stored separately to allow for quick lookups and historical tracking
    without needing to recalculate from RuleResults.
    """
    
    evaluation = models.OneToOneField(
        ComplianceEvaluation,
        on_delete=models.CASCADE,
        related_name='score',
        primary_key=True
    )
    
    # Score metrics
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage score (0-100)"
    )
    
    passed_weight = models.PositiveIntegerField(
        help_text="Sum of weights for passed rules"
    )
    
    total_weight = models.PositiveIntegerField(
        help_text="Sum of weights for all evaluated rules"
    )
    
    passed_count = models.PositiveIntegerField(
        help_text="Number of rules that passed"
    )
    
    failed_count = models.PositiveIntegerField(
        help_text="Number of rules that failed"
    )
    
    total_rules = models.PositiveIntegerField(
        help_text="Total number of rules evaluated"
    )
    
    # Previous score for comparison (null for first evaluation)
    previous_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score from previous evaluation (for trend)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cpl_scores'
        verbose_name = 'Compliance Score'
        verbose_name_plural = 'Compliance Scores'
    
    def __str__(self):
        return f"Score: {self.total_score}% ({self.passed_count}/{self.total_rules} rules)"
    
    @property
    def score_change(self):
        """Calculate the change from previous score."""
        if self.previous_score is None:
            return None
        return float(self.total_score) - float(self.previous_score)
    
    @property
    def grade(self):
        """Return a letter grade based on score."""
        score = float(self.total_score)
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
    
    @classmethod
    def calculate_from_results(cls, evaluation):
        """
        Calculate and create a ComplianceScore from an evaluation's rule results.
        
        Returns the created ComplianceScore instance.
        """
        results = evaluation.rule_results.all()
        
        passed_results = results.filter(passed=True)
        failed_results = results.filter(passed=False)
        
        passed_weight = sum(r.weight for r in passed_results)
        total_weight = sum(r.weight for r in results)
        
        passed_count = passed_results.count()
        failed_count = failed_results.count()
        total_rules = results.count()
        
        # Calculate percentage score
        if total_weight > 0:
            total_score = (passed_weight / total_weight) * 100
        else:
            total_score = 0
        
        # Get previous score for this repo + standard
        previous_eval = ComplianceEvaluation.objects.filter(
            repository=evaluation.repository,
            standard=evaluation.standard,
            status=ComplianceEvaluation.STATUS_COMPLETED,
            id__lt=evaluation.id
        ).order_by('-created_at').first()
        
        previous_score = None
        if previous_eval and hasattr(previous_eval, 'score'):
            previous_score = previous_eval.score.total_score
        
        return cls.objects.create(
            evaluation=evaluation,
            total_score=round(total_score, 2),
            passed_weight=passed_weight,
            total_weight=total_weight,
            passed_count=passed_count,
            failed_count=failed_count,
            total_rules=total_rules,
            previous_score=previous_score
        )
