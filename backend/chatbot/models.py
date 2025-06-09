from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User

class Conversation(models.Model):
    """Model to store chat conversations"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=_('User')
    )
    
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"

class Message(models.Model):
    """Model to store individual chat messages"""
    TYPE_CHOICES = [
        ('user', _('User')),
        ('bot', _('Bot')),
        ('system', _('System')),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversation')
    )
    
    message_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='user',
        verbose_name=_('Message Type')
    )
    
    content = models.TextField(verbose_name=_('Content'))
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # For tracking message status
    is_read = models.BooleanField(default=False, verbose_name=_('Read'))
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class BotResponse(models.Model):
    """Model to store predefined bot responses for common queries"""
    query_pattern = models.CharField(max_length=255, verbose_name=_('Query Pattern'))
    response_text = models.TextField(verbose_name=_('Response Text'))
    
    # For categorizing responses
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Category'))
    
    # For tracking and improving responses
    usage_count = models.PositiveIntegerField(default=0, verbose_name=_('Usage Count'))
    effectiveness_rating = models.FloatField(default=0.0, verbose_name=_('Effectiveness Rating'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    class Meta:
        verbose_name = _('Bot Response')
        verbose_name_plural = _('Bot Responses')
        ordering = ['-usage_count']
    
    def __str__(self):
        return f"{self.query_pattern} -> {self.response_text[:50]}..."
    
    def increment_usage(self):
        """Increment the usage count of this response"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def update_rating(self, rating):
        """Update the effectiveness rating (1-5 scale)"""
        if 1 <= rating <= 5:
            # Simple moving average
            current_count = self.usage_count or 1
            self.effectiveness_rating = ((self.effectiveness_rating * (current_count - 1)) + rating) / current_count
            self.save(update_fields=['effectiveness_rating'])

class UserFeedback(models.Model):
    """Model to store user feedback on bot responses"""
    RATING_CHOICES = [
        (1, _('Not helpful at all')),
        (2, _('Slightly helpful')),
        (3, _('Moderately helpful')),
        (4, _('Very helpful')),
        (5, _('Extremely helpful')),
    ]
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name=_('Message')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chatbot_feedback',
        verbose_name=_('User')
    )
    
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_('Rating')
    )
    
    comment = models.TextField(blank=True, null=True, verbose_name=_('Comment'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('User Feedback')
        verbose_name_plural = _('User Feedback')
        ordering = ['-created_at']
        # Ensure a user can only give feedback once per message
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"Feedback from {self.user.get_full_name()} - Rating: {self.rating}"
