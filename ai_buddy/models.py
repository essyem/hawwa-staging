from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class Conversation(models.Model):
    """Model for AI buddy conversations with mothers"""
    
    CONVERSATION_TYPES = (
        ('general', _('General Support')),
        ('wellness', _('Wellness Check-in')),
        ('nutrition', _('Nutrition Guidance')),
        ('emotional', _('Emotional Support')),
        ('schedule', _('Schedule Planning')),
        ('milestone', _('Milestone Tracking')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('User')
    )
    conversation_type = models.CharField(
        max_length=20, 
        choices=CONVERSATION_TYPES,
        default='general',
        verbose_name=_('Conversation Type')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


class Message(models.Model):
    """Model for individual messages in AI buddy conversations"""
    
    MESSAGE_TYPES = (
        ('user', _('User Message')),
        ('ai', _('AI Response')),
        ('system', _('System Message')),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversation')
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        verbose_name=_('Message Type')
    )
    content = models.TextField(verbose_name=_('Content'))
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text=_('Additional data like sentiment, confidence, etc.')
    )
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_('Timestamp'))
    is_read = models.BooleanField(default=False, verbose_name=_('Is Read'))
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."


class WellnessTracking(models.Model):
    """Model for tracking mother's wellness metrics"""
    
    MOOD_CHOICES = (
        ('excellent', _('Excellent')),
        ('good', _('Good')),
        ('neutral', _('Neutral')),
        ('low', _('Low')),
        ('concerning', _('Concerning')),
    )
    
    ENERGY_LEVELS = (
        ('high', _('High Energy')),
        ('moderate', _('Moderate Energy')),
        ('low', _('Low Energy')),
        ('exhausted', _('Exhausted')),
    )
    
    SLEEP_QUALITY = (
        ('excellent', _('Excellent')),
        ('good', _('Good')),
        ('fair', _('Fair')),
        ('poor', _('Poor')),
        ('very_poor', _('Very Poor')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wellness_tracking',
        verbose_name=_('User')
    )
    date = models.DateField(default=timezone.now, verbose_name=_('Date'))
    mood = models.CharField(
        max_length=20, 
        choices=MOOD_CHOICES,
        verbose_name=_('Mood')
    )
    energy_level = models.CharField(
        max_length=20,
        choices=ENERGY_LEVELS,
        verbose_name=_('Energy Level')
    )
    sleep_quality = models.CharField(
        max_length=20,
        choices=SLEEP_QUALITY,
        verbose_name=_('Sleep Quality')
    )
    sleep_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Hours of Sleep')
    )
    pain_level = models.PositiveIntegerField(
        default=0,
        help_text=_('Scale of 0-10'),
        verbose_name=_('Pain Level')
    )
    notes = models.TextField(blank=True, verbose_name=_('Additional Notes'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    
    class Meta:
        verbose_name = _('Wellness Tracking')
        verbose_name_plural = _('Wellness Tracking')
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date}"


class Milestone(models.Model):
    """Model for tracking postpartum milestones and achievements"""
    
    MILESTONE_TYPES = (
        ('physical', _('Physical Recovery')),
        ('emotional', _('Emotional Wellbeing')),
        ('baby_care', _('Baby Care Skills')),
        ('self_care', _('Self Care')),
        ('family', _('Family Bonding')),
        ('social', _('Social Connection')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name=_('User')
    )
    milestone_type = models.CharField(
        max_length=20,
        choices=MILESTONE_TYPES,
        verbose_name=_('Milestone Type')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    target_date = models.DateField(null=True, blank=True, verbose_name=_('Target Date'))
    achieved_date = models.DateField(null=True, blank=True, verbose_name=_('Achieved Date'))
    is_achieved = models.BooleanField(default=False, verbose_name=_('Is Achieved'))
    progress_percentage = models.PositiveIntegerField(
        default=0,
        help_text=_('Progress from 0-100%'),
        verbose_name=_('Progress Percentage')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Milestone')
        verbose_name_plural = _('Milestones')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


class CareRecommendation(models.Model):
    """Model for AI-generated care recommendations"""
    
    RECOMMENDATION_TYPES = (
        ('nutrition', _('Nutrition')),
        ('exercise', _('Exercise')),
        ('rest', _('Rest & Recovery')),
        ('wellness', _('Wellness Activity')),
        ('medical', _('Medical Consultation')),
        ('emotional', _('Emotional Support')),
        ('baby_care', _('Baby Care Tips')),
    )
    
    PRIORITY_LEVELS = (
        ('low', _('Low Priority')),
        ('medium', _('Medium Priority')),
        ('high', _('High Priority')),
        ('urgent', _('Urgent')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='care_recommendations',
        verbose_name=_('User')
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPES,
        verbose_name=_('Recommendation Type')
    )
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium',
        verbose_name=_('Priority')
    )
    is_completed = models.BooleanField(default=False, verbose_name=_('Is Completed'))
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Due Date'))
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed Date'))
    ai_confidence = models.FloatField(
        default=0.0,
        help_text=_('AI confidence score (0.0-1.0)'),
        verbose_name=_('AI Confidence')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional data like related services, context, etc.')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Care Recommendation')
        verbose_name_plural = _('Care Recommendations')
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


class AIBuddyProfile(models.Model):
    """Model for customizing AI buddy personality and preferences"""
    
    PERSONALITY_TYPES = (
        ('supportive', _('Supportive & Encouraging')),
        ('clinical', _('Clinical & Professional')),
        ('friendly', _('Friendly & Casual')),
        ('gentle', _('Gentle & Nurturing')),
        ('practical', _('Practical & Direct')),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_buddy_profile',
        verbose_name=_('User')
    )
    buddy_name = models.CharField(
        max_length=50,
        default='Hawwa',
        verbose_name=_('AI Buddy Name')
    )
    personality_type = models.CharField(
        max_length=20,
        choices=PERSONALITY_TYPES,
        default='supportive',
        verbose_name=_('Personality Type')
    )
    check_in_frequency = models.PositiveIntegerField(
        default=1,
        help_text=_('How often to check in (days)'),
        verbose_name=_('Check-in Frequency')
    )
    preferred_topics = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of preferred conversation topics'),
        verbose_name=_('Preferred Topics')
    )
    language_preference = models.CharField(
        max_length=10,
        default='en',
        verbose_name=_('Language Preference')
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enable Notifications')
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('AI Buddy Profile')
        verbose_name_plural = _('AI Buddy Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s AI Buddy ({self.buddy_name})"
