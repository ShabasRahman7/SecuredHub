"""AI assistant chat endpoints with RAG-enhanced context."""
import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import ChatConversation, ChatMessage
from scans.models import ScanFinding
from scans.serializers import ScanFindingSerializer

# import service URLs from centralized settings
RAG_SERVICE_URL = settings.RAG_SERVICE_URL

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def init_chat(request, finding_id):
    finding = get_object_or_404(ScanFinding, id=finding_id)
    
    # handling potential duplicates by getting the first conversation
    conversation = ChatConversation.objects.filter(finding=finding).first()
    created = False
    
    if not conversation:
        conversation = ChatConversation.objects.create(finding=finding)
        created = True
    
    if not created:
        messages = list(conversation.messages.values('role', 'content', 'created_at'))
        return Response({
            'conversation_id': conversation.id,
            'messages': messages
        })
    
    
    try:
        rag_response = requests.post(
            f"{RAG_SERVICE_URL}/chat/init",
            json={
                'finding_id': finding.id,
                'finding': {
                    'id': finding.id,
                    'title': finding.title,
                    'description': finding.description,
                    'file_path': finding.file_path,
                    'line_number': finding.line_number,
                    'severity': finding.severity,
                    'rule_id': finding.rule_id
                }
            },
            timeout=10
        )
        rag_response.raise_for_status()
        initial_message = rag_response.json()['message']
        
        ChatMessage.objects.create(
            conversation=conversation,
            role='system',
            content=initial_message
        )
        
        return Response({
            'conversation_id': conversation.id,
            'initial_message': initial_message
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to initialize chat: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, finding_id):
    finding = get_object_or_404(ScanFinding, id=finding_id)
    user_message = request.data.get('message', '').strip()
    
    if not user_message:
        return Response(
            {'error': 'Message cannot be empty'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # getting or create conversation (handle duplicates)
    conversation = ChatConversation.objects.filter(finding=finding).first()
    if not conversation:
        conversation = ChatConversation.objects.create(finding=finding)
    
    ChatMessage.objects.create(
        conversation=conversation,
        role='user',
        content=user_message
    )
    
    history = list(conversation.messages.values('role', 'content'))
    
    finding_context = {
        'id': finding.id,
        'title': finding.title,
        'description': finding.description,
        'file_path': finding.file_path,
        'line_number': finding.line_number,
        'severity': finding.severity,
        'rule_id': finding.rule_id,
        'tool': finding.tool
    }
    
    code_snippet = _fetch_code_context(finding)
    if code_snippet:
        finding_context['code_snippet'] = code_snippet
    
    # nOTE: N+1 query pattern here, but acceptable for current scale
    # consider batch loading if tenant has >1000 findings
    similar_findings = _fetch_similar_findings(finding)
    if similar_findings:
        finding_context['similar_past_findings'] = similar_findings
    
    try:
        rag_response = requests.post(
            f"{RAG_SERVICE_URL}/chat",
            json={
                'finding_id': finding.id,
                'message': user_message,
                'conversation_history': history,
                'finding': finding_context  # Enriched with code + history!
            },
            timeout=30
        )
        rag_response.raise_for_status()
        ai_reply = rag_response.json()['reply']
        
        ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_reply
        )
        
        return Response({'reply': ai_reply})
    except Exception as e:
        return Response(
            {'error': f'Chat failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def _fetch_code_context(finding):
    try:
        if finding.raw_output and isinstance(finding.raw_output, dict):
            # bandit stores code in raw_output
            if 'code' in finding.raw_output:
                return finding.raw_output['code']
            # try to extract from more_info
            if 'more_info' in finding.raw_output:
                return finding.raw_output.get('more_info', '')
        return None
    except Exception:
        return None

def _fetch_similar_findings(finding):
    try:
        tenant = finding.scan.repository.tenant
        
        similar = ScanFinding.objects.filter(
            rule_id=finding.rule_id,
            scan__repository__tenant=tenant
        ).exclude(
            id=finding.id
        ).order_by('-created_at').values(
            'id', 'title', 'file_path', 'created_at', 'scan__repository__name'
        )[:3]
        
        return [
            {
                'finding_id': f['id'],
                'title': f['title'],
                'file': f['file_path'],
                'repo': f['scan__repository__name'],
                'when': f['created_at'].strftime('%Y-%m-%d')
            }
            for f in similar
        ] if similar else None
    except Exception:
        return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_conversations(request):
    user = request.user
    
    # multitenant filtering through membership relation
    if not hasattr(user, 'tenant_membership') or not user.tenant_membership:
        return Response({'conversations': []})
    
    tenant = user.tenant_membership.tenant
    
    # getting all conversations from findings in user's scans
    conversations = ChatConversation.objects.filter(
        finding__scan__repository__tenant=tenant
    ).select_related('finding').prefetch_related('messages').order_by('-updated_at')
    
    result = []
    for conv in conversations:
        last_message = conv.messages.last()
        result.append({
            'conversation_id': conv.id,
            'finding_id': conv.finding.id,
            'finding_title': conv.finding.title,
            'finding_severity': conv.finding.severity,
            'file_path': conv.finding.file_path,
            'message_count': conv.messages.count(),
            'last_message': last_message.content[:100] if last_message else None,
            'updated_at': conv.updated_at,
            'created_at': conv.created_at
        })
    
    return Response({'conversations': result})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request, finding_id):
    finding = get_object_or_404(ScanFinding, id=finding_id)
    
    try:
        # handling duplicates by getting the first conversation
        conversation = ChatConversation.objects.filter(finding=finding).first()
        if not conversation:
            return Response({'messages': []})
        
        messages = list(conversation.messages.values('role', 'content', 'created_at'))
        return Response({'messages': messages})
    except Exception:
        return Response({'messages': []})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    try:
        conversation = get_object_or_404(ChatConversation, id=conversation_id)
        
        # verifying user has access to this conversation's tenant
        user = request.user
        if hasattr(user, 'tenant_membership') and user.tenant_membership:
            tenant = user.tenant_membership.tenant
            if conversation.finding.scan.repository.tenant != tenant:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        conversation.delete()
        return Response({'success': True})
    except Exception as e:
        return Response(
            {'error': f'Failed to delete conversation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
