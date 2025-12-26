"""
Internal API views for AI Agent data access.

These endpoints are used by the AI Agent to fetch evaluation data.
Authentication is via service token (like worker endpoints).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from compliance.models import ComplianceEvaluation, RuleResult, ComplianceScore
from compliance.views.internal import ServiceTokenAuthentication, IsInternalService
from repositories.models import Repository
from standards.models import ComplianceStandard


class AIEvaluationDetailView(APIView):
    """
    Get evaluation details for AI Agent.
    
    GET /internal/compliance/evaluations/{id}/
    
    Used by AI Agent's get_evaluation tool.
    """
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def get(self, request, pk):
        evaluation = get_object_or_404(ComplianceEvaluation, pk=pk)
        
        # Get score data
        try:
            score = evaluation.score
            score_data = {
                "total_score": float(score.total_score),
                "grade": score.grade,
                "passed_count": score.passed_count,
                "failed_count": score.failed_count,
            }
        except ComplianceScore.DoesNotExist:
            score_data = None
        
        data = {
            "id": evaluation.id,
            "repository_id": evaluation.repository_id,
            "repository_name": evaluation.repository.name if evaluation.repository else None,
            "standard_id": evaluation.standard_id,
            "standard_name": evaluation.standard.name if evaluation.standard else None,
            "status": evaluation.status,
            "commit_hash": evaluation.commit_hash,
            "score": score_data,
            "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
            "completed_at": evaluation.completed_at.isoformat() if evaluation.completed_at else None,
        }
        
        return Response(data)


class AIEvaluationFailuresView(APIView):
    """
    Get failed rules for an evaluation.
    
    GET /internal/compliance/evaluations/{id}/failures/
    
    Used by AI Agent's get_failures tool.
    """
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def get(self, request, pk):
        evaluation = get_object_or_404(ComplianceEvaluation, pk=pk)
        
        # Get only failed results
        failures = RuleResult.objects.filter(
            evaluation=evaluation,
            passed=False
        ).select_related('rule')
        
        data = []
        for failure in failures:
            rule = failure.rule
            data.append({
                "id": failure.id,
                "rule_id": rule.id if rule else None,
                "rule_name": rule.name if rule else "Unknown",
                "rule_type": rule.rule_type if rule else None,
                "severity": rule.severity if rule else None,
                "weight": float(rule.weight) if rule and rule.weight else 1.0,
                "description": rule.description if rule else None,
                "message": failure.message,
                "evidence": failure.evidence,
                "remediation_hint": rule.remediation_hint if rule else None,
            })
        
        return Response({
            "evaluation_id": evaluation.id,
            "total_failures": len(data),
            "failures": data,
        })


class AIRepositoryDetailView(APIView):
    """
    Get repository details for AI Agent.
    
    GET /internal/repositories/{id}/
    """
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def get(self, request, pk):
        repo = get_object_or_404(Repository, pk=pk)
        
        data = {
            "id": repo.id,
            "name": repo.name,
            "full_name": repo.full_name,
            "github_url": repo.github_url,
            "default_branch": repo.default_branch,
            "description": repo.description,
            "tenant_id": repo.tenant_id,
        }
        
        return Response(data)


class AIStandardDetailView(APIView):
    """
    Get compliance standard details for AI Agent.
    
    GET /internal/standards/{id}/
    """
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def get(self, request, pk):
        standard = get_object_or_404(ComplianceStandard, pk=pk)
        
        data = {
            "id": standard.id,
            "name": standard.name,
            "description": standard.description,
            "version": standard.version,
            "is_builtin": standard.is_builtin,
            "rule_count": standard.rules.count(),
        }
        
        return Response(data)


class AIScoreHistoryView(APIView):
    """
    Get score history for a repository.
    
    GET /internal/repositories/{id}/score-history/
    """
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def get(self, request, pk):
        repo = get_object_or_404(Repository, pk=pk)
        limit = int(request.query_params.get('limit', 10))
        
        # Get recent evaluations with scores
        evaluations = ComplianceEvaluation.objects.filter(
            repository=repo,
            status='completed'
        ).select_related('score', 'standard').order_by('-completed_at')[:limit]
        
        history = []
        for eval in evaluations:
            try:
                score = eval.score
                history.append({
                    "evaluation_id": eval.id,
                    "score": float(score.total_score),
                    "grade": score.grade,
                    "standard_name": eval.standard.name if eval.standard else None,
                    "date": eval.completed_at.isoformat() if eval.completed_at else None,
                })
            except ComplianceScore.DoesNotExist:
                pass
        
        return Response({
            "repository_id": repo.id,
            "repository_name": repo.name,
            "history": history,
        })
