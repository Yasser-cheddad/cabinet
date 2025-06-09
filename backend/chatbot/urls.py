from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Conversation endpoints
    path('conversations/', views.get_conversations, name='conversation-list'),
    path('conversations/create/', views.create_conversation, name='conversation-create'),
    path('conversations/<int:conversation_id>/', views.get_conversation_messages, name='conversation-detail'),
    path('conversations/<int:conversation_id>/update/', views.update_conversation, name='conversation-update'),
    path('conversations/<int:conversation_id>/delete/', views.delete_conversation, name='conversation-delete'),
    
    # Message endpoints
    path('conversations/<int:conversation_id>/messages/', views.get_conversation_messages, name='message-list'),
    path('conversations/<int:conversation_id>/messages/send/', views.send_message, name='send-message'),
    
    # Feedback endpoints
    path('messages/<int:message_id>/feedback/', views.provide_feedback, name='provide-feedback'),
]
