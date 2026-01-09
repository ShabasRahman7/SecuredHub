# unit tests for notifications app models
import pytest
from notifications.models import Notification


@pytest.mark.django_db
class TestNotificationModel:
    # testing Notification model
    
    def test_notification_creation(self, test_user):
        # should create notification with all fields
        notification = Notification.objects.create(
            user=test_user,
            notification_type='repo_assigned',
            title='Repository Assigned',
            message='You have been assigned to repository test-repo',
            data={'repository_id': 123, 'repository_name': 'test-repo'}
        )
        assert notification.user == test_user
        assert notification.notification_type == 'repo_assigned'
        assert notification.is_read is False
    
    def test_str_representation(self, test_user):
        # should return formatted string
        notification = Notification.objects.create(
            user=test_user,
            notification_type='scan_complete',
            title='Scan Completed',
            message='Security scan completed successfully'
        )
        expected = f"{test_user.email}: Scan Completed (scan_complete)"
        assert str(notification) == expected
    
    def test_mark_as_read_idempotent(self, test_user):
        # should mark as read only if currently unread (idempotent)
        notification = Notification.objects.create(
            user=test_user,
            notification_type='test',
            title='Test',
            message='Test message'
        )
        assert notification.is_read is False
        
        # first mark as read
        notification.mark_as_read()
        notification.refresh_from_db()
        assert notification.is_read is True
        
        # second call should not cause unnecessary DB write
        notification.mark_as_read()
        notification.refresh_from_db()
        assert notification.is_read is True
    
    def test_mark_as_unread(self, test_user):
        # should mark notification as unread
        notification = Notification.objects.create(
            user=test_user,
            notification_type='test',
            title='Test',
            message='Test message',
            is_read=True
        )
        
        notification.mark_as_unread()
        notification.refresh_from_db()
        assert notification.is_read is False
    
    def test_mark_as_unread_idempotent(self, test_user):
        # should only update if currently read (idempotent)
        notification = Notification.objects.create(
            user=test_user,
            notification_type='test',
            title='Test',
            message='Test message',
            is_read=False
        )
        
        notification.mark_as_unread()
        notification.refresh_from_db()
        assert notification.is_read is False
    
    def test_json_data_field(self, test_user):
        # should store and retrieve JSON data
        notification = Notification.objects.create(
            user=test_user,
            notification_type='repo_assigned',
            title='Repository Assigned',
            message='New assignment',
            data={
                'repository_id': 456,
                'repository_name': 'secure-app',
                'assigned_by': 'admin@example.com'
            }
        )
        notification.refresh_from_db()
        
        assert notification.data['repository_id'] == 456
        assert notification.data['repository_name'] == 'secure-app'
        assert notification.data['assigned_by'] == 'admin@example.com'
    
    def test_filter_unread_notifications(self, test_user):
        # should filter unread notifications correctly
        # creating mix of read and unread
        Notification.objects.create(
            user=test_user,
            notification_type='test1',
            title='Unread 1',
            message='Message 1',
            is_read=False
        )
        Notification.objects.create(
            user=test_user,
            notification_type='test2',
            title='Read',
            message='Message 2',
            is_read=True
        )
        Notification.objects.create(
            user=test_user,
            notification_type='test3',
            title='Unread 2',
            message='Message 3',
            is_read=False
        )
        
        unread = Notification.objects.filter(user=test_user, is_read=False)
        assert unread.count() == 2
    
    def test_ordering_by_created_at(self, test_user):
        # should order by newest first
        notif1 = Notification.objects.create(
            user=test_user,
            notification_type='test1',
            title='Old',
            message='Old message'
        )
        notif2 = Notification.objects.create(
            user=test_user,
            notification_type='test2',
            title='New',
            message='New message'
        )
        
        notifications = list(Notification.objects.filter(user=test_user))
        # notif2 should be first (newest)
        assert notifications[0] == notif2
        assert notifications[1] == notif1
