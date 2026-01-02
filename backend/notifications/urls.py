"""
Notification URL patterns.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('unread-count/', views.unread_count, name='unread_count'),
]
