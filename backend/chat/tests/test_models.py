# unit tests for chat app models
import pytest
from chat.models import ChatConversation, ChatMessage


@pytest.mark.django_db
class TestChatConversationModel:
    # testing ChatConversation model
    
    def test_conversation_creation(self, test_scan_finding):
        # should create conversation linked to finding
        conversation = ChatConversation.objects.create(
            finding=test_scan_finding
        )
        assert conversation.finding == test_scan_finding
        assert conversation.created_at is not None
    
    def test_str_representation(self, test_scan_finding):
        # should return formatted string with finding ID
        conversation = ChatConversation.objects.create(
            finding=test_scan_finding
        )
        expected = f"Chat for Finding #{test_scan_finding.id}"
        assert str(conversation) == expected
    
    def test_ordering_by_updated_at(self, db, test_scan_finding):
        # should order conversations by most recently updated first
        conv1 = ChatConversation.objects.create(finding=test_scan_finding)
        
        # creating another finding for second conversation
        from scans.models import ScanFinding
        finding2 = ScanFinding.objects.create(
            scan=test_scan_finding.scan,
            scanner_type='secret_scanner',
            severity='MEDIUM',
            title='API Key Exposure',
            file_path='config.py',
            line_number=10
        )
        conv2 = ChatConversation.objects.create(finding=finding2)
        
        conversations = list(ChatConversation.objects.all())
        # conv2 should be first (more recent)
        assert conversations[0] == conv2
        assert conversations[1] == conv1


@pytest.mark.django_db
class TestChatMessageModel:
    # testing ChatMessage model
    
    def test_message_creation_user_role(self, test_scan_finding):
        # should create message with user role
        conversation = ChatConversation.objects.create(finding=test_scan_finding)
        message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content='How can I fix this SQL injection?'
        )
        assert message.role == 'user'
        assert message.content == 'How can I fix this SQL injection?'
    
    def test_message_creation_assistant_role(self, test_scan_finding):
        # should create message with assistant role
        conversation = ChatConversation.objects.create(finding=test_scan_finding)
        message = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='Use parameterized queries to prevent SQL injection.'
        )
        assert message.role == 'assistant'
    
    def test_role_choices_validation(self, test_scan_finding):
        # should validate role choices
        conversation = ChatConversation.objects.create(finding=test_scan_finding)
        
        # valid roles
        for role in ['user', 'assistant', 'system']:
            message = ChatMessage.objects.create(
                conversation=conversation,
                role=role,
                content=f'Test message for {role}'
            )
            assert message.role == role
    
    def test_str_representation_truncates_long_content(self, test_scan_finding):
        # should truncate content in string representation
        conversation = ChatConversation.objects.create(finding=test_scan_finding)
        long_content = "A" * 100
        message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=long_content
        )
        str_repr = str(message)
        # should truncate and add ellipsis
        assert len(str_repr) < len(long_content)
        assert str_repr.endswith('...')
    
    def test_ordering_by_created_at(self, test_scan_finding):
        # should order messages chronologically
        conversation = ChatConversation.objects.create(finding=test_scan_finding)
        
        msg1 = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content='First message'
        )
        msg2 = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content='Second message'
        )
        
        messages = list(conversation.messages.all())
        assert messages[0] == msg1
        assert messages[1] == msg2
