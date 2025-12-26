"""
AI Agent proxy views.

Routes requests from frontend to AI Agent service.
This allows:
1. Authentication to be handled by Django
2. AI Agent to be on internal network only
3. Proper user/tenant context to be passed
"""
import logging
import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from compliance.models import ComplianceEvaluation, RuleResult
from repositories.models import Repository

logger = logging.getLogger(__name__)

# AI Agent URL - from settings or default
AI_AGENT_URL = getattr(settings, 'AI_AGENT_URL', 'http://ai-agent:8002')


class AIAnalyzeProxyView(APIView):
    """
    Proxy for AI analysis.
    
    POST /api/v1/ai/analyze/
    
    Accepts evaluation_id and forwards to AI Agent.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Forward analysis request to AI Agent."""
        
        # If evaluation_id provided, fetch and build context
        evaluation_id = request.data.get('evaluation_id')
        
        if evaluation_id:
            try:
                evaluation = ComplianceEvaluation.objects.select_related(
                    'repository', 'standard', 'score'
                ).prefetch_related('rule_results__rule').get(pk=evaluation_id)
                
                # Verify user has access
                if not self._user_can_access(request.user, evaluation.repository):
                    return Response(
                        {'error': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Build evaluation context
                evaluation_data = self._build_evaluation_context(evaluation)
                
            except ComplianceEvaluation.DoesNotExist:
                return Response(
                    {'error': 'Evaluation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Use provided evaluation data directly
            evaluation_data = request.data.get('evaluation')
            if not evaluation_data:
                return Response(
                    {'error': 'Either evaluation_id or evaluation data required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Forward to AI Agent
        try:
            response = httpx.post(
                f"{AI_AGENT_URL}/api/v1/analyze",
                json={
                    'evaluation': evaluation_data,
                    'include_remediation': request.data.get('include_remediation', True),
                    'include_framework_mapping': request.data.get('include_framework_mapping', True),
                    'max_recommendations': request.data.get('max_recommendations', 5),
                },
                timeout=30.0
            )
            response.raise_for_status()
            return Response(response.json())
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Agent error: {e}")
            return Response(
                {'error': 'AI analysis failed', 'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.exception(f"AI Agent connection error: {e}")
            return Response(
                {'error': 'AI service unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    def _user_can_access(self, user, repository):
        """Check if user can access this repository."""
        if user.is_staff:
            return True
        return repository.tenant.members.filter(user=user).exists()
    
    def _build_evaluation_context(self, evaluation):
        """Build evaluation context from model."""
        # Get failed rules
        failures = []
        for result in evaluation.rule_results.filter(passed=False):
            rule = result.rule
            failures.append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'rule_type': rule.rule_type,
                'description': rule.description or '',
                'severity': rule.severity,
                'weight': result.weight,
                'message': result.message,
                'evidence': result.evidence or {},
            })
        
        # Get score
        try:
            score = evaluation.score
            score_value = float(score.total_score)
            grade = score.grade
        except Exception:
            score_value = 0.0
            grade = 'F'
        
        return {
            'repository_name': evaluation.repository.name,
            'repository_url': evaluation.repository.url,
            'default_branch': evaluation.branch or 'main',
            'evaluation_id': evaluation.id,
            'score': score_value,
            'grade': grade,
            'total_rules': evaluation.rule_results.count(),
            'passed_rules': evaluation.rule_results.filter(passed=True).count(),
            'failed_rules': len(failures),
            'standard_name': evaluation.standard.name,
            'standard_description': evaluation.standard.description or '',
            'failures': failures,
            'organization_name': evaluation.repository.tenant.name if evaluation.repository.tenant else None,
        }


class AIAgentProxyView(APIView):
    """
    Proxy for AI Agent.
    
    POST /api/v1/ai/agent/
    
    Forwards to AI Agent with goal and context.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Forward agent request to AI Agent."""
        
        goal = request.data.get('goal')
        if not goal:
            return Response(
                {'error': 'Goal is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Forward to AI Agent
        try:
            response = httpx.post(
                f"{AI_AGENT_URL}/api/v1/agent",
                json={
                    'goal': goal,
                    'evaluation_id': request.data.get('evaluation_id'),
                    'repository_id': request.data.get('repository_id'),
                    'max_steps': request.data.get('max_steps', 5),
                },
                timeout=60.0  # Longer timeout for agentic reasoning
            )
            response.raise_for_status()
            return Response(response.json())
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Agent error: {e}")
            return Response(
                {'error': 'AI agent failed', 'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.exception(f"AI Agent connection error: {e}")
            return Response(
                {'error': 'AI service unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class AIEvaluationRecommendationsView(APIView):
    """
    Get AI recommendations for a specific evaluation.
    
    GET /api/v1/ai/evaluations/{id}/recommendations/
    
    Convenience endpoint that fetches evaluation and analyzes.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get AI recommendations for evaluation."""
        
        try:
            evaluation = ComplianceEvaluation.objects.select_related(
                'repository', 'standard', 'score'
            ).prefetch_related('rule_results__rule').get(pk=pk)
            
            # Verify user has access
            if not request.user.is_staff:
                if not evaluation.repository.tenant.members.filter(user=request.user).exists():
                    return Response(
                        {'error': 'Access denied'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Check if evaluation is completed
            if evaluation.status != 'completed':
                return Response(
                    {'error': 'Evaluation not completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if there are failures
            if not evaluation.rule_results.filter(passed=False).exists():
                return Response({
                    'summary': 'All rules passed! No recommendations needed.',
                    'recommendations': [],
                    'score_projection': {
                        'current_score': float(evaluation.score.total_score),
                        'projected_score_all_fixed': float(evaluation.score.total_score),
                    },
                    'confidence_score': 1.0
                })
            
            # Build context and forward to AI
            analyze_view = AIAnalyzeProxyView()
            analyze_view.request = request
            
            # Create a mock request with evaluation_id
            class MockRequest:
                def __init__(self, user, data):
                    self.user = user
                    self.data = data
            
            mock_request = MockRequest(request.user, {'evaluation_id': pk})
            return analyze_view.post(mock_request)
            
        except ComplianceEvaluation.DoesNotExist:
            return Response(
                {'error': 'Evaluation not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AIHealthView(APIView):
    """
    Check AI service health.
    
    GET /api/v1/ai/health/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check AI Agent health."""
        try:
            response = httpx.get(
                f"{AI_AGENT_URL}/health",
                timeout=5.0
            )
            response.raise_for_status()
            return Response({
                'ai_service': 'available',
                **response.json()
            })
        except Exception as e:
            return Response({
                'ai_service': 'unavailable',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
