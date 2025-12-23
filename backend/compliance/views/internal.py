"""
Internal API views for worker → backend communication.

These endpoints are called by the Celery worker to update evaluation state.
All writes are now centralized here, making Backend the single source of truth.
"""
import json
import logging
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from api.internal.auth import ServiceTokenAuthentication, IsInternalService
from compliance.models import ComplianceEvaluation, RuleResult, ComplianceScore
from compliance.serializers.internal import (
    UpdateStatusSerializer,
    BulkRuleResultSerializer,
    CompleteEvaluationSerializer,
    EvaluationStatusResponseSerializer,
)
from standards.models import ComplianceRule

logger = logging.getLogger(__name__)


def send_ws_update(evaluation_id: int, payload: dict):
    """Send WebSocket update for an evaluation."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("No channel layer available for WebSocket update")
        return
    
    group_name = f'evaluation_{evaluation_id}'
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "evaluation_update", **payload},
        )
        logger.debug(f"Sent WS update to {group_name}: {payload.get('status')}")
    except Exception as e:
        logger.warning(f"Failed to send WebSocket update: {e}")


class UpdateEvaluationStatusView(APIView):
    """
    Update evaluation status.
    
    PATCH /api/internal/evaluations/{id}/status/
    
    Called by worker to update status and progress.
    """
    
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def patch(self, request, pk):
        evaluation = get_object_or_404(ComplianceEvaluation, pk=pk)
        
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        new_status = data['status']
        old_status = evaluation.status
        
        # Validate state transition
        valid_transitions = {
            'pending': ['running', 'failed'],
            'running': ['running', 'completed', 'failed'],  # Allow running→running for progress updates
        }
        
        if old_status not in valid_transitions:
            return Response(
                {'error': f'Evaluation in terminal state: {old_status}'},
                status=status.HTTP_409_CONFLICT
            )
        
        if new_status not in valid_transitions.get(old_status, []):
            return Response(
                {'error': f'Invalid transition: {old_status} → {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update evaluation
        update_fields = []
        
        # Only update status if it changed
        if new_status != old_status:
            evaluation.status = new_status
            update_fields.append('status')
        
        if new_status == 'running' and not evaluation.started_at:
            evaluation.started_at = timezone.now()
            update_fields.append('started_at')
        
        if new_status in ['completed', 'failed']:
            evaluation.completed_at = timezone.now()
            update_fields.append('completed_at')
        
        if data.get('error_message'):
            evaluation.error_message = data['error_message']
            update_fields.append('error_message')
        
        if data.get('commit_hash'):
            evaluation.commit_hash = data['commit_hash']
            update_fields.append('commit_hash')
        
        if data.get('task_id'):
            evaluation.task_id = data['task_id']
            update_fields.append('task_id')
        
        # Only save if there are fields to update
        if update_fields:
            evaluation.save(update_fields=update_fields)
        
        if old_status != new_status:
            logger.info(f"Evaluation {pk} status: {old_status} → {new_status}")
        else:
            logger.debug(f"Evaluation {pk} progress update (status unchanged: {new_status})")
        
        # Send WebSocket update
        ws_payload = {
            'evaluation_id': pk,
            'status': new_status,
            'message': data.get('message', ''),
            'progress': data.get('progress'),
        }
        send_ws_update(pk, ws_payload)
        
        response_serializer = EvaluationStatusResponseSerializer(evaluation)
        return Response(response_serializer.data)


class BulkCreateResultsView(APIView):
    """
    Bulk create rule results for an evaluation.
    
    POST /api/internal/evaluations/{id}/results/
    
    Called by worker after evaluating all rules.
    """
    
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def post(self, request, pk):
        evaluation = get_object_or_404(ComplianceEvaluation, pk=pk)
        
        # Validate evaluation is in running state
        if evaluation.status != ComplianceEvaluation.STATUS_RUNNING:
            return Response(
                {'error': f'Evaluation not in running state: {evaluation.status}'},
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = BulkRuleResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        results_data = serializer.validated_data['results']
        
        # Validate rule IDs exist
        rule_ids = [r['rule_id'] for r in results_data]
        existing_rules = set(
            ComplianceRule.objects.filter(id__in=rule_ids).values_list('id', flat=True)
        )
        
        missing_rules = set(rule_ids) - existing_rules
        if missing_rules:
            return Response(
                {'error': f'Invalid rule IDs: {list(missing_rules)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicates within this evaluation
        existing_results = set(
            RuleResult.objects.filter(
                evaluation=evaluation,
                rule_id__in=rule_ids
            ).values_list('rule_id', flat=True)
        )
        
        if existing_results:
            return Response(
                {'error': f'Results already exist for rules: {list(existing_results)}'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Bulk create results
        with transaction.atomic():
            rule_results = [
                RuleResult(
                    evaluation=evaluation,
                    rule_id=r['rule_id'],
                    passed=r['passed'],
                    message=r.get('message', ''),
                    evidence=r.get('evidence', {}),
                    weight=r['weight'],
                )
                for r in results_data
            ]
            RuleResult.objects.bulk_create(rule_results)
        
        logger.info(f"Created {len(rule_results)} results for evaluation {pk}")
        
        return Response(
            {'created': len(rule_results)},
            status=status.HTTP_201_CREATED
        )


class CompleteEvaluationView(APIView):
    """
    Complete an evaluation and calculate/store the score.
    
    POST /api/internal/evaluations/{id}/complete/
    
    Called by worker after all results are stored.
    This endpoint:
    1. Creates the ComplianceScore record
    2. Updates evaluation status to 'completed'
    3. Sends final WebSocket update
    """
    
    authentication_classes = [ServiceTokenAuthentication]
    permission_classes = [IsInternalService]
    
    def post(self, request, pk):
        evaluation = get_object_or_404(
            ComplianceEvaluation.objects.select_related('repository', 'standard'),
            pk=pk
        )
        
        # Validate evaluation is in running state
        if evaluation.status != ComplianceEvaluation.STATUS_RUNNING:
            return Response(
                {'error': f'Evaluation not in running state: {evaluation.status}'},
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = CompleteEvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Calculate score percentage
        total_weight = data['total_weight']
        passed_weight = data['passed_weight']
        
        if total_weight > 0:
            total_score = Decimal(passed_weight) / Decimal(total_weight) * 100
            total_score = round(total_score, 2)
        else:
            total_score = Decimal('0.00')
        
        # Get previous score for trend tracking
        previous_eval = ComplianceEvaluation.objects.filter(
            repository=evaluation.repository,
            standard=evaluation.standard,
            status=ComplianceEvaluation.STATUS_COMPLETED,
            id__lt=pk
        ).order_by('-created_at').first()
        
        previous_score = None
        if previous_eval:
            try:
                previous_score = previous_eval.score.total_score
            except ComplianceScore.DoesNotExist:
                pass
        
        with transaction.atomic():
            # Create score record
            ComplianceScore.objects.create(
                evaluation=evaluation,
                total_score=total_score,
                passed_weight=data['passed_weight'],
                total_weight=data['total_weight'],
                passed_count=data['passed_count'],
                failed_count=data['failed_count'],
                total_rules=data['total_rules'],
                previous_score=previous_score,
            )
            
            # Update evaluation status
            evaluation.status = ComplianceEvaluation.STATUS_COMPLETED
            evaluation.completed_at = timezone.now()
            evaluation.save(update_fields=['status', 'completed_at'])
        
        logger.info(
            f"Evaluation {pk} completed: {total_score}% "
            f"({data['passed_count']}/{data['total_rules']} rules)"
        )
        
        # Send final WebSocket update
        ws_payload = {
            'evaluation_id': pk,
            'status': 'completed',
            'message': f'Evaluation complete: {total_score}% compliance',
            'progress': 100,
            'score': float(total_score),
            'passed_count': data['passed_count'],
            'failed_count': data['failed_count'],
            'total_rules': data['total_rules'],
        }
        send_ws_update(pk, ws_payload)
        
        return Response({
            'evaluation_id': pk,
            'status': 'completed',
            'score': float(total_score),
            'passed_count': data['passed_count'],
            'failed_count': data['failed_count'],
            'total_rules': data['total_rules'],
        })
