"""URL configuration for chat endpoints"""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('conversations', views.get_all_conversations, name='all_conversations'),
    path('conversations/<int:conversation_id>', views.delete_conversation, name='delete_conversation'),
    path('findings/<int:finding_id>/chat/init', views.init_chat, name='init_chat'),
    path('findings/<int:finding_id>/chat', views.send_message, name='send_message'),
    path('findings/<int:finding_id>/chat/history', views.get_chat_history, name='chat_history'),
]

