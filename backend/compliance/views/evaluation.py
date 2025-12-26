"""Views for compliance evaluation API."""
import logging
import requests
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from celery import current_app
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from compliance.models import ComplianceEvaluation, RuleResult, ComplianceScore
from compliance.serializers.evaluation import (
    EvaluationListSerializer,
    EvaluationDetailSerializer,
    RuleResultSerializer,
    ComplianceScoreSerializer,
    TriggerEvaluationSerializer
)
from repositories.models import Repository, TenantCredential
from standards.models import RepositoryStandard
from accounts.models import TenantMember

logger = logging.getLogger(__name__)


def get_user_tenant(user):
    """
    Get the tenant for a user based on their membership.
    Returns None if user has no tenant membership.
    Admins (is_staff) can access all tenants.
    """
    if user.is_staff:
        return None  # Admins bypass tenant filtering
    
    membership = TenantMember.objects.filter(
        user=user,
        deleted_at__isnull=True
    ).select_related('tenant').first()
    
    return membership.tenant if membership else None


def get_latest_commit_hash(repository, access_token):
    """
    Fetch the latest commit hash for a repository from GitHub.
    Returns None if unable to fetch.
    """
    try:
        # Parse owner/repo from URL
        url = repository.url
        if 'github.com/' in url:
            parts = url.rstrip('/').split('github.com/')[-1].replace('.git', '').split('/')
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
            else:
                return None
        else:
            return None
        
        branch = repository.default_branch or 'main'
        api_url = f'https://api.github.com/repos/{owner}/{repo}/commits/{branch}'
        
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('sha')
    except Exception as e:
        logger.warning(f"Failed to fetch latest commit: {e}")
    
    return None


@extend_schema_view(
    get=extend_schema(
        summary="List repository evaluations",
        description="List compliance evaluations for a specific repository.",
        tags=["Compliance"]
    )
)
class EvaluationListView(generics.ListAPIView):
    """List evaluations for a repository with tenant isolation."""
    serializer_class = EvaluationListSerializer
    
    def get_queryset(self):
        repository_id = self.kwargs.get('repository_id')
        user = self.request.user
        tenant = get_user_tenant(user)
        
        # Build base queryset
        queryset = ComplianceEvaluation.objects.filter(
            repository_id=repository_id
        )
        
        # Apply tenant filter for non-admin users
        if tenant:
            queryset = queryset.filter(repository__tenant=tenant)
        elif not user.is_staff:
            # User has no tenant membership and is not admin - return empty
            return ComplianceEvaluation.objects.none()
        
        return queryset.select_related(
            'repository', 'standard', 'triggered_by'
        ).prefetch_related(
            'score'
        ).order_by('-created_at')[:50]


@extend_schema_view(
    get=extend_schema(
        summary="Get evaluation details",
        description="Get details of a specific compliance evaluation including all rule results.",
        tags=["Compliance"]
    )
)
class EvaluationDetailView(generics.RetrieveAPIView):
    """Get evaluation details including rule results with tenant isolation."""
    serializer_class = EvaluationDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        tenant = get_user_tenant(user)
        
        queryset = ComplianceEvaluation.objects.select_related(
            'repository', 'standard', 'triggered_by', 'score'
        ).prefetch_related(
            'rule_results', 'rule_results__rule'
        )
        
        # Apply tenant filter for non-admin users
        if tenant:
            queryset = queryset.filter(repository__tenant=tenant)
        elif not user.is_staff:
            return ComplianceEvaluation.objects.none()
        
        return queryset


@extend_schema(
    summary="Trigger compliance evaluation",
    description="Trigger a new compliance evaluation for a repository against a standard.",
    tags=["Compliance"],
    request=TriggerEvaluationSerializer,
    responses={201: EvaluationDetailSerializer}
)
class TriggerEvaluationView(APIView):
    """Trigger a new compliance evaluation."""
    
    def post(self, request):
        user = request.user
        
        serializer = TriggerEvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        repository = serializer.validated_data['repository']
        standard = serializer.validated_data['standard']
        branch = serializer.validated_data.get('branch', repository.default_branch)
        
        # Verify user has access to this repository (via tenant membership)
        membership = TenantMember.objects.filter(
            user=user,
            tenant=repository.tenant,
            deleted_at__isnull=True
        ).first()
        
        if not membership and not user.is_staff:
            return Response(
                {'error': 'You do not have access to this repository'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if there's a pending/running evaluation for same repo+standard
        existing = ComplianceEvaluation.objects.filter(
            repository=repository,
            standard=standard,
            status__in=[ComplianceEvaluation.STATUS_PENDING, ComplianceEvaluation.STATUS_RUNNING]
        ).first()
        
        if existing:
            # Check if the existing evaluation is stale (stuck for > 30 minutes)
            from django.utils import timezone
            from datetime import timedelta
            
            stale_threshold = timezone.now() - timedelta(minutes=30)
            is_stale = existing.created_at < stale_threshold
            
            if is_stale:
                # Mark stale evaluation as failed and allow new one
                existing.status = ComplianceEvaluation.STATUS_FAILED
                existing.completed_at = timezone.now()
                existing.error_message = 'Evaluation timed out (stale for > 30 minutes)'
                existing.save(update_fields=['status', 'completed_at', 'error_message'])
            else:
                return Response({
                    'error': 'An evaluation is already in progress',
                    'evaluation_id': existing.id
                }, status=status.HTTP_409_CONFLICT)
        
        # Commit-based deduplication: check if already evaluated at current commit
        force_run = request.data.get('force', False)
        latest_commit = None
        
        if not force_run:
            # Get access token to fetch latest commit
            credential = TenantCredential.objects.filter(
                tenant=repository.tenant,
                is_active=True,
                provider='github'
            ).first()
            
            if credential:
                access_token = credential.get_access_token()
                if access_token:
                    latest_commit = get_latest_commit_hash(repository, access_token)
                    
                    if latest_commit:
                        # Check if we have a completed evaluation for this commit
                        existing_for_commit = ComplianceEvaluation.objects.filter(
                            repository=repository,
                            standard=standard,
                            commit_hash=latest_commit,
                            status=ComplianceEvaluation.STATUS_COMPLETED
                        ).first()
                        
                        if existing_for_commit:
                            return Response({
                                'already_evaluated': True,
                                'evaluation_id': existing_for_commit.id,
                                'commit_hash': latest_commit,
                                'message': 'Already evaluated at this commit. Use force=true to re-run.',
                                'score': float(existing_for_commit.score.total_score) if hasattr(existing_for_commit, 'score') else None
                            }, status=status.HTTP_200_OK)
        
        # Create the evaluation
        evaluation = ComplianceEvaluation.objects.create(
            repository=repository,
            standard=standard,
            triggered_by=user,
            branch=branch,
            status=ComplianceEvaluation.STATUS_PENDING
        )
        
        # Queue the Celery task
        try:
            task = current_app.send_task(
                'compliance.tasks.run_compliance_evaluation',
                args=[evaluation.id],
                queue='compliance'
            )
            evaluation.task_id = task.id
            evaluation.save(update_fields=['task_id'])
        except Exception as e:
            evaluation.status = ComplianceEvaluation.STATUS_FAILED
            evaluation.error_message = f"Failed to queue task: {str(e)}"
            evaluation.save(update_fields=['status', 'error_message'])
            return Response({
                'error': 'Failed to queue evaluation task',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_serializer = EvaluationDetailSerializer(evaluation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class LatestEvaluationView(APIView):
    """Get latest completed evaluation for a repo+standard pair with tenant isolation."""
    
    def get(self, request, repository_id, standard_id):
        user = request.user
        tenant = get_user_tenant(user)
        
        # Build queryset with tenant filter
        queryset = ComplianceEvaluation.objects.filter(
            repository_id=repository_id,
            standard_id=standard_id,
            status=ComplianceEvaluation.STATUS_COMPLETED
        )
        
        # Apply tenant filter for non-admin users
        if tenant:
            queryset = queryset.filter(repository__tenant=tenant)
        elif not user.is_staff:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        evaluation = queryset.select_related(
            'repository', 'standard', 'triggered_by', 'score'
        ).prefetch_related(
            'rule_results', 'rule_results__rule'
        ).order_by('-completed_at').first()
        
        if not evaluation:
            return Response(
                {'error': 'No completed evaluation found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EvaluationDetailSerializer(evaluation)
        return Response(serializer.data)


class RepositoryScoresView(APIView):
    """Get compliance scores for all standards assigned to a repository with tenant isolation."""
    
    def get(self, request, repository_id):
        user = request.user
        tenant = get_user_tenant(user)
        
        # Get repository with tenant verification
        repository = get_object_or_404(Repository, id=repository_id)
        
        # Verify tenant access for non-admin users
        if tenant and repository.tenant != tenant:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        elif not tenant and not user.is_staff:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all assigned standards
        assignments = RepositoryStandard.objects.filter(
            repository=repository,
            is_active=True
        ).select_related('standard')
        
        scores = []
        for assignment in assignments:
            # Get latest completed evaluation for this standard
            latest = ComplianceEvaluation.objects.filter(
                repository=repository,
                standard=assignment.standard,
                status=ComplianceEvaluation.STATUS_COMPLETED
            ).select_related('score').order_by('-completed_at').first()
            
            score_data = {
                'standard_id': assignment.standard.id,
                'standard_name': assignment.standard.name,
                'standard_version': assignment.standard.version,
                'assigned_at': assignment.assigned_at,
                'latest_evaluation': None
            }
            
            if latest and hasattr(latest, 'score'):
                score_data['latest_evaluation'] = {
                    'evaluation_id': latest.id,
                    'score': float(latest.score.total_score),
                    'grade': latest.score.grade,
                    'passed_count': latest.score.passed_count,
                    'failed_count': latest.score.failed_count,
                    'total_rules': latest.score.total_rules,
                    'evaluated_at': latest.completed_at,
                    'previous_score': float(latest.score.previous_score) if latest.score.previous_score else None
                }
            
            scores.append(score_data)
        
        return Response({
            'repository_id': repository_id,
            'repository_name': repository.name,
            'standards': scores
        })


class DeleteEvaluationView(APIView):
    """Delete an evaluation (owner only, cascades to results and scores)."""
    
    def delete(self, request, pk):
        user = request.user
        
        # Get evaluation with related objects
        evaluation = get_object_or_404(
            ComplianceEvaluation.objects.select_related('repository__tenant'),
            pk=pk
        )
        
        repository = evaluation.repository
        tenant = repository.tenant
        
        # Verify user is tenant OWNER (not just member)
        membership = TenantMember.objects.filter(
            user=user,
            tenant=tenant,
            role='owner',
            deleted_at__isnull=True
        ).first()
        
        if not membership and not user.is_staff:
            return Response(
                {'error': 'Only tenant owners can delete evaluations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        evaluation_id = evaluation.id
        evaluation_status = evaluation.status
        
        # Delete evaluation (CASCADE will handle RuleResults and ComplianceScore)
        evaluation.delete()
        
        return Response({
            'message': f'Evaluation #{evaluation_id} deleted successfully',
            'evaluation_id': evaluation_id,
            'was_status': evaluation_status
        }, status=status.HTTP_200_OK)

