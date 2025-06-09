import os
import json
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for interacting with the OpenRouter API to access DeepSeek V2 model"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3-opus:beta"  # Using Claude 3 Opus model
        
    def generate_response(self, messages, max_tokens=400):
        """
        Generate a response using the DeepSeek V2 model via OpenRouter
        
        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text response or error message
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.SITE_DOMAIN,  # Required for OpenRouter
            "X-Title": "Medical Cabinet Assistant"  # Optional but helpful for tracking
        }
        
        # Limit max_tokens to 400 to stay within free tier limits
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": min(max_tokens, 400),  # Ensure we never exceed 400 tokens
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return f"Sorry, I'm having trouble connecting to my knowledge base. Error: {response.status_code}"
                
        except Exception as e:
            logger.exception(f"Error calling OpenRouter API: {str(e)}")
            return "Sorry, I'm having trouble generating a response right now. Please try again later."
    
    def generate_medical_response(self, user_message, conversation_history=None):
        """
        Generate a medical assistant response with appropriate context
        
        Args:
            user_message: The user's current message
            conversation_history: Optional list of previous messages
            
        Returns:
            Generated response text
        """
        # System prompt to guide the model behavior
        system_prompt = {
            "role": "system",
            "content": (
                "You are a helpful medical assistant for a doctor's office. "
                "Provide accurate, helpful information about medical appointments, general health questions, "
                "and clinic procedures. Be conversational and friendly. "
                "For specific medical advice, always recommend consulting with a doctor. "
                "For appointment scheduling, collect relevant information like preferred date, time, and reason. "
                "Never provide specific diagnoses or treatment recommendations. "
                "Respond in French as this is a French medical office."
            )
        }
        
        # Prepare the messages array
        messages = [system_prompt]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Generate and return the response
        return self.generate_response(messages)
