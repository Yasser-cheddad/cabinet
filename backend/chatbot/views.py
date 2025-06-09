from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message, BotResponse, UserFeedback

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Get all conversations for the current user"""
    user = request.user
    
    # Get conversations for this user, newest first
    conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
    
    # Format response data
    data = [{
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at,
        'updated_at': conversation.updated_at,
        'is_active': conversation.is_active,
        # Get the last message in each conversation
        'last_message': conversation.messages.order_by('-timestamp').first().content[:100] if conversation.messages.exists() else None
    } for conversation in conversations]
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    """Create a new conversation"""
    user = request.user
    title = request.data.get('title', _('New Conversation'))
    
    # Create the conversation
    conversation = Conversation.objects.create(
        user=user,
        title=title
    )
    
    # Add initial system message if provided
    initial_message = request.data.get('initial_message')
    if initial_message:
        Message.objects.create(
            conversation=conversation,
            message_type='system',
            content=initial_message
        )
    
    return Response({
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """Get all messages for a specific conversation"""
    user = request.user
    
    # Ensure the conversation belongs to the user
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Get messages for this conversation, oldest first
    messages = conversation.messages.all().order_by('timestamp')
    
    # Format response data
    data = [{
        'id': message.id,
        'message_type': message.message_type,
        'content': message.content,
        'timestamp': message.timestamp,
        'is_read': message.is_read
    } for message in messages]
    
    # Mark all unread messages as read
    unread_messages = conversation.messages.filter(is_read=False)
    for message in unread_messages:
        message.is_read = True
        message.save(update_fields=['is_read'])
    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id):
    """Send a new message in a conversation and get bot response"""
    user = request.user
    content = request.data.get('content')
    
    if not content:
        return Response({
            'error': _('Message content is required')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Ensure the conversation belongs to the user
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Create the user message
    user_message = Message.objects.create(
        conversation=conversation,
        message_type='user',
        content=content
    )
    
    # Update conversation timestamp
    conversation.save()  # This will update the updated_at field
    
    # Generate bot response using OpenRouter with DeepSeek V2
    # Pass the conversation_id to provide context from previous messages
    bot_response_text = generate_bot_response(content, conversation_id=conversation_id)
    
    # Create the bot message
    bot_message = Message.objects.create(
        conversation=conversation,
        message_type='bot',
        content=bot_response_text
    )
    
    return Response({
        'user_message': {
            'id': user_message.id,
            'content': user_message.content,
            'timestamp': user_message.timestamp
        },
        'bot_message': {
            'id': bot_message.id,
            'content': bot_message.content,
            'timestamp': bot_message.timestamp
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def provide_feedback(request, message_id):
    """Provide feedback on a bot message"""
    user = request.user
    rating = request.data.get('rating')
    comment = request.data.get('comment', '')
    
    # Validate rating
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError()
    except (ValueError, TypeError):
        return Response({
            'error': _('Rating must be an integer between 1 and 5')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the message
    message = get_object_or_404(Message, id=message_id, message_type='bot')
    
    # Ensure the message belongs to a conversation owned by the user
    if message.conversation.user != user:
        return Response({
            'error': _('You do not have permission to provide feedback on this message')
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Create or update the feedback
    feedback, created = UserFeedback.objects.update_or_create(
        message=message,
        user=user,
        defaults={
            'rating': rating,
            'comment': comment
        }
    )
    
    # Update the effectiveness rating of any matching bot response
    update_bot_response_rating(message.content, rating)
    
    return Response({
        'success': _('Feedback submitted successfully'),
        'id': feedback.id
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_conversation(request, conversation_id):
    """Update a conversation (e.g., title, active status)"""
    user = request.user
    
    # Ensure the conversation belongs to the user
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Update title if provided
    if 'title' in request.data:
        conversation.title = request.data['title']
    
    # Update active status if provided
    if 'is_active' in request.data:
        conversation.is_active = request.data['is_active']
    
    # Save changes
    conversation.save()
    
    return Response({
        'id': conversation.id,
        'title': conversation.title,
        'is_active': conversation.is_active,
        'updated_at': conversation.updated_at
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    user = request.user
    
    # Ensure the conversation belongs to the user
    conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
    
    # Delete the conversation (this will cascade delete all messages)
    conversation.delete()
    
    return Response({
        'success': _('Conversation deleted successfully')
    }, status=status.HTTP_200_OK)

# Helper functions
from .openrouter_client import OpenRouterClient
import logging

logger = logging.getLogger(__name__)

def generate_bot_response(user_message, conversation_id=None):
    """Generate a bot response based on user message using OpenRouter with DeepSeek V2"""
    # First try to find a matching predefined response in our database
    try:
        # Look for responses that match the query pattern
        bot_responses = BotResponse.objects.filter(
            Q(query_pattern__icontains=user_message) | 
            Q(query_pattern__iexact=user_message)
        ).filter(is_active=True).order_by('-effectiveness_rating')
        
        if bot_responses.exists():
            # Use the most effective matching response
            response = bot_responses.first()
            response.increment_usage()
            return response.response_text
    except Exception as e:
        logger.error(f"Error finding predefined response: {str(e)}")
    
    # If no predefined response, use OpenRouter with DeepSeek V2
    try:
        # Get conversation history if conversation_id is provided
        conversation_history = []
        if conversation_id:
            # Get the last 5 messages from the conversation to provide context
            messages = Message.objects.filter(conversation_id=conversation_id).order_by('-timestamp')[:10]
            
            # Format messages for the OpenRouter API
            for message in reversed(messages):
                role = "assistant" if message.message_type == "bot" else "user"
                conversation_history.append({
                    "role": role,
                    "content": message.content
                })
        
        # Initialize OpenRouter client and generate response
        client = OpenRouterClient()
        response = client.generate_medical_response(user_message, conversation_history)
        return response
        
    except Exception as e:
        logger.error(f"Error generating response with OpenRouter: {str(e)}")
        # Fallback response if API call fails
        return _('Je suis désolé, je rencontre des difficultés à répondre à votre question. Veuillez contacter notre personnel médical pour obtenir de l\'aide.')

def update_bot_response_rating(response_text, rating):
    """Update the rating of a bot response"""
    try:
        # Find bot responses with this exact response text
        bot_responses = BotResponse.objects.filter(response_text=response_text)
        
        for response in bot_responses:
            response.update_rating(rating)
    except Exception:
        pass
