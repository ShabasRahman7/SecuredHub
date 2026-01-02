# database models

from django.db import models
from scans.models import ScanFinding

class AIAnalysis(models.Model):
    """
    AI-generated fix suggestions for security findings.
    Linked to ScanFinding for HIGH and CRITICAL severity issues.
    """
    finding = models.OneToOneField(
        ScanFinding,
        on_delete=models.CASCADE,
        related_name='ai_analysis',
        help_text="The scan finding this analysis is for"
    )
    
    # aI-generated content
    title = models.CharField(max_length=255, help_text="Title of the security issue")
    explanation = models.TextField(help_text="Detailed explanation of the vulnerability")
    fix_code = models.TextField(help_text="Code fix suggestion with examples")
    references = models.JSONField(default=list, help_text="List of reference links and standards")
    
    # metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    service_version = models.CharField(max_length=50, default="1.0.0")
    
    class Meta:
        db_table = 'ai_analyses'
        verbose_name = 'AI Analysis'
        verbose_name_plural = 'AI Analyses'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"AI Analysis for {self.finding.rule_id} (Finding #{self.finding.id})"
