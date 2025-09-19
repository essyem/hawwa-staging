from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from datetime import datetime, timedelta

from .models import (
    Conversation, Message, WellnessTracking, Milestone, 
    CareRecommendation, AIBuddyProfile
)
from .ai_engine import AIBuddyEngine
from services.models import Service
from bookings.models import Booking


class AIBuddyHomeView(LoginRequiredMixin, TemplateView):
    """Enhanced AI buddy dashboard view with intelligent insights"""
    template_name = 'ai_buddy/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Initialize AI engine for this user
        ai_engine = AIBuddyEngine(user)
        
        # Get or create AI buddy profile
        ai_profile, created = AIBuddyProfile.objects.get_or_create(user=user)
        
        # Get recent conversations
        recent_conversations = Conversation.objects.filter(
            user=user, is_active=True
        )[:5]
        
        # Get today's wellness tracking
        today_wellness = WellnessTracking.objects.filter(
            user=user, date=timezone.now().date()
        ).first()
        
        # Get pending recommendations (enhanced with AI)
        pending_recommendations = CareRecommendation.objects.filter(
            user=user, is_completed=False
        ).order_by('priority', '-created_at')[:5]
        
        # Get current milestones
        current_milestones = Milestone.objects.filter(
            user=user, is_achieved=False
        ).order_by('-created_at')[:3]
        
        # Get personalized insights from AI engine
        wellness_insights = ai_engine.context['wellness_trends']
        
        # Get suggested services based on current needs
        suggested_services = ai_engine.suggest_services()
        
        # Generate daily check-in message
        if today_wellness:
            daily_message = ai_engine.generate_response(
                f"Today I tracked my mood as {today_wellness.mood} and slept {today_wellness.sleep_hours} hours",
                conversation_type='wellness'
            )
        else:
            daily_message = ai_engine.generate_response(
                "I haven't tracked my wellness today yet",
                conversation_type='wellness'
            )
        
        context.update({
            'ai_profile': ai_profile,
            'recent_conversations': recent_conversations,
            'today_wellness': today_wellness,
            'pending_recommendations': pending_recommendations,
            'current_milestones': current_milestones,
            'wellness_insights': wellness_insights,
            'suggested_services': suggested_services[:3],  # Limit to top 3
            'daily_message': daily_message,
            'has_tracked_today': today_wellness is not None,
        })
        
        return context


class ConversationListView(LoginRequiredMixin, ListView):
    """View for listing all user conversations"""
    model = Conversation
    template_name = 'ai_buddy/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 10
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a specific conversation"""
    model = Conversation
    template_name = 'ai_buddy/conversation_detail.html'
    context_object_name = 'conversation'
    
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.all()
        
        # Mark messages as read
        Message.objects.filter(
            conversation=self.object, 
            message_type='ai',
            is_read=False
        ).update(is_read=True)
        
        return context


@login_required
@require_POST
@csrf_exempt
def start_conversation(request):
    """AJAX view to start a new conversation with enhanced AI"""
    try:
        data = json.loads(request.body)
        conversation_type = data.get('conversation_type', 'general')
        title = data.get('title', f'New {conversation_type.title()} Conversation')
        initial_message = data.get('message', '')
        
        # Create conversation
        conversation = Conversation.objects.create(
            user=request.user,
            conversation_type=conversation_type,
            title=title
        )
        
        # Add initial user message if provided
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                message_type='user',
                content=initial_message
            )
            
            # Generate AI response using enhanced engine
            ai_engine = AIBuddyEngine(request.user)
            ai_response = ai_engine.generate_response(
                initial_message, 
                conversation_type,
                str(conversation.id)
            )
            
            Message.objects.create(
                conversation=conversation,
                message_type='ai',
                content=ai_response
            )
        
        return JsonResponse({
            'success': True,
            'conversation_id': str(conversation.id),
            'redirect_url': f'/ai-buddy/conversation/{conversation.id}/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def send_message(request, conversation_id):
    """AJAX view to send a message in a conversation with enhanced AI"""
    try:
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id, 
            user=request.user
        )
        
        data = json.loads(request.body)
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})
        
        # Create user message
        user_message = Message.objects.create(
            conversation=conversation,
            message_type='user',
            content=message_content
        )
        
        # Generate AI response using enhanced engine
        ai_engine = AIBuddyEngine(request.user)
        ai_response = ai_engine.generate_response(
            message_content, 
            conversation.conversation_type,
            str(conversation.id)
        )
        
        ai_message = Message.objects.create(
            conversation=conversation,
            message_type='ai',
            content=ai_response
        )
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Check if we should generate new recommendations based on the conversation
        if any(keyword in message_content.lower() for keyword in ['pain', 'sleep', 'sad', 'tired', 'help']):
            # Generate smart recommendations
            latest_wellness = WellnessTracking.objects.filter(user=request.user).order_by('-date').first()
            if latest_wellness:
                new_recommendations = ai_engine.generate_recommendations(latest_wellness)
                
                # Create recommendation objects
                for rec_data in new_recommendations:
                    CareRecommendation.objects.get_or_create(
                        user=request.user,
                        recommendation_type=rec_data['type'],
                        title=rec_data['title'],
                        defaults={
                            'description': rec_data['description'],
                            'priority': rec_data['priority'],
                            'ai_confidence': rec_data['confidence'],
                            'due_date': timezone.now() + timedelta(days=3)
                        }
                    )
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': str(user_message.id),
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'ai_message': {
                'id': str(ai_message.id),
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class WellnessTrackingView(LoginRequiredMixin, TemplateView):
    """View for wellness tracking dashboard"""
    template_name = 'ai_buddy/wellness_tracking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get recent wellness data (last 7 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        wellness_data = WellnessTracking.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('-date')
        
        # Get today's tracking
        today_tracking = WellnessTracking.objects.filter(
            user=user,
            date=end_date
        ).first()
        
        context.update({
            'wellness_data': wellness_data,
            'today_tracking': today_tracking,
            'has_tracked_today': today_tracking is not None,
        })
        
        return context


@login_required
@require_POST
@csrf_exempt
def log_wellness(request):
    """AJAX view to log wellness data with enhanced AI recommendations"""
    try:
        data = json.loads(request.body)
        date = data.get('date', timezone.now().date().isoformat())
        
        # Parse date
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get or create wellness tracking for the date
        wellness, created = WellnessTracking.objects.get_or_create(
            user=request.user,
            date=date,
            defaults={
                'mood': data.get('mood', 'neutral'),
                'energy_level': data.get('energy_level', 'moderate'),
                'sleep_quality': data.get('sleep_quality', 'fair'),
                'sleep_hours': data.get('sleep_hours', 0),
                'pain_level': data.get('pain_level', 0),
                'notes': data.get('notes', '')
            }
        )
        
        if not created:
            # Update existing record
            wellness.mood = data.get('mood', wellness.mood)
            wellness.energy_level = data.get('energy_level', wellness.energy_level)
            wellness.sleep_quality = data.get('sleep_quality', wellness.sleep_quality)
            wellness.sleep_hours = data.get('sleep_hours', wellness.sleep_hours)
            wellness.pain_level = data.get('pain_level', wellness.pain_level)
            wellness.notes = data.get('notes', wellness.notes)
            wellness.save()
        
        # Generate enhanced care recommendations using AI engine
        ai_engine = AIBuddyEngine(request.user)
        new_recommendations = ai_engine.generate_recommendations(wellness)
        
        # Create recommendation objects
        recommendations_created = 0
        for rec_data in new_recommendations:
            recommendation, rec_created = CareRecommendation.objects.get_or_create(
                user=request.user,
                recommendation_type=rec_data['type'],
                title=rec_data['title'],
                defaults={
                    'description': rec_data['description'],
                    'priority': rec_data['priority'],
                    'ai_confidence': rec_data['confidence'],
                    'due_date': timezone.now() + timedelta(days=3),
                    'metadata': {'generated_from_wellness': True, 'wellness_date': date.isoformat()}
                }
            )
            if rec_created:
                recommendations_created += 1
        
        # Generate a personalized response based on the wellness data
        wellness_message = f"I logged my mood as {wellness.mood}, slept {wellness.sleep_hours} hours with {wellness.sleep_quality} quality sleep, energy level is {wellness.energy_level}, and pain level is {wellness.pain_level}/10."
        if wellness.notes:
            wellness_message += f" Additional notes: {wellness.notes}"
        
        ai_response = ai_engine.generate_response(wellness_message, conversation_type='wellness')
        
        return JsonResponse({
            'success': True,
            'message': 'Wellness data logged successfully!',
            'ai_response': ai_response,
            'recommendations_created': recommendations_created,
            'wellness_insights': ai_engine.context['wellness_trends']
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class MilestoneListView(LoginRequiredMixin, ListView):
    """View for listing user milestones"""
    model = Milestone
    template_name = 'ai_buddy/milestone_list.html'
    context_object_name = 'milestones'
    paginate_by = 10
    
    def get_queryset(self):
        return Milestone.objects.filter(user=self.request.user)


class CareRecommendationListView(LoginRequiredMixin, ListView):
    """View for listing care recommendations"""
    model = CareRecommendation
    template_name = 'ai_buddy/recommendation_list.html'
    context_object_name = 'recommendations'
    paginate_by = 10
    
    def get_queryset(self):
        return CareRecommendation.objects.filter(user=self.request.user)


class AIBuddyProfileView(LoginRequiredMixin, UpdateView):
    """View for updating AI buddy profile settings"""
    model = AIBuddyProfile
    template_name = 'ai_buddy/profile_settings.html'
    fields = [
        'buddy_name', 'personality_type', 'check_in_frequency',
        'language_preference', 'notifications_enabled'
    ]
    success_url = reverse_lazy('ai_buddy:home')
    
    def get_object(self):
        profile, created = AIBuddyProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, _('AI Buddy settings updated successfully!'))
        return super().form_valid(form)


def generate_ai_response(message, conversation_type, user):
    """
    Generate AI response based on message and context
    This is a simplified implementation - in production, this would
    integrate with an actual AI service like OpenAI, Claude, etc.
    """
    
    # Get user's AI buddy profile
    try:
        ai_profile = user.ai_buddy_profile
        buddy_name = ai_profile.buddy_name
        personality = ai_profile.personality_type
    except AIBuddyProfile.DoesNotExist:
        buddy_name = "Hawwa"
        personality = "supportive"
    
    # Simple response templates based on conversation type and personality
    responses = {
        'general': {
            'supportive': f"Hi there! I'm {buddy_name}, and I'm here to support you on your postpartum journey. How are you feeling today?",
            'clinical': f"Hello. I'm {buddy_name}, your postpartum care assistant. What specific concerns can I help you address today?",
            'friendly': f"Hey! {buddy_name} here! I'm so glad you reached out. What's on your mind?",
            'gentle': f"Hello dear, it's {buddy_name}. I'm here to listen and support you through this beautiful journey. How can I help?",
            'practical': f"I'm {buddy_name}. Let's focus on what you need right now. What would be most helpful for you today?"
        },
        'wellness': {
            'supportive': "It's wonderful that you're taking time to check in with yourself. Your wellbeing matters so much. Tell me how you're feeling physically and emotionally.",
            'clinical': "Let's assess your current wellness status. Please share your energy levels, mood, and any physical symptoms you're experiencing.",
            'friendly': "Love that you're prioritizing your wellness! How's your body feeling today? And more importantly, how's your heart?",
            'gentle': "Taking care of yourself is such an act of love - for you and your baby. What does your body need today?",
            'practical': "Let's get a clear picture of your wellness. Rate your energy, mood, and pain levels so I can provide targeted support."
        },
        'nutrition': {
            'supportive': "Nourishing yourself is so important right now. I'm here to help you make choices that fuel your recovery and energy.",
            'clinical': "Proper nutrition is crucial for postpartum recovery. What are your current eating patterns and any dietary concerns?",
            'friendly': "Let's talk food! What sounds good to you today? I've got lots of ideas for delicious, nourishing meals.",
            'gentle': "Your body has done something amazing, and it deserves to be nourished well. What would feel good to eat right now?",
            'practical': "Let's plan your nutrition. What meals have you had today, and what nutrients might you be missing?"
        },
        'emotional': {
            'supportive': "Your feelings are completely valid, and it's brave of you to reach out. I'm here to listen without judgment.",
            'clinical': "Emotional wellbeing is a critical component of postpartum health. Please share what you're experiencing.",
            'friendly': "I'm here for you, no matter what you're feeling. Want to talk about what's going on in your heart?",
            'gentle': "This journey brings up so many emotions, and that's completely normal. You're safe here to share whatever you're feeling.",
            'practical': "Let's address what you're feeling. Identifying emotions is the first step to managing them effectively."
        }
    }
    
    # Get appropriate response based on type and personality
    if conversation_type in responses and personality in responses[conversation_type]:
        base_response = responses[conversation_type][personality]
    else:
        base_response = responses['general'].get(personality, responses['general']['supportive'])
    
    # Add contextual elements based on user's recent activity
    recent_wellness = WellnessTracking.objects.filter(user=user).order_by('-date').first()
    if recent_wellness:
        if recent_wellness.mood in ['low', 'concerning']:
            base_response += " I noticed you've been feeling a bit low lately. Remember, it's okay to have difficult days."
        elif recent_wellness.sleep_hours < 4:
            base_response += " I see you haven't been getting much sleep. Rest is so important for your recovery."
    
    return base_response


def generate_care_recommendations(user, wellness_tracking):
    """
    Generate personalized care recommendations based on wellness data
    """
    recommendations = []
    
    # Check mood
    if wellness_tracking.mood in ['low', 'concerning']:
        recommendations.append({
            'type': 'emotional',
            'title': 'Consider Emotional Support',
            'description': 'Your mood tracking suggests you might benefit from talking to someone. Consider reaching out to a mental health professional or joining a support group.',
            'priority': 'high' if wellness_tracking.mood == 'concerning' else 'medium'
        })
    
    # Check sleep
    if wellness_tracking.sleep_hours < 4:
        recommendations.append({
            'type': 'rest',
            'title': 'Prioritize Rest',
            'description': 'You\'re getting very little sleep. Try to nap when the baby naps, ask for help with night feeds, or consider sleep support services.',
            'priority': 'high'
        })
    elif wellness_tracking.sleep_quality in ['poor', 'very_poor']:
        recommendations.append({
            'type': 'rest',
            'title': 'Improve Sleep Quality',
            'description': 'Even though you\'re getting some sleep, the quality isn\'t great. Try creating a calming bedtime routine or adjusting your sleep environment.',
            'priority': 'medium'
        })
    
    # Check pain levels
    if wellness_tracking.pain_level > 6:
        recommendations.append({
            'type': 'medical',
            'title': 'Address Pain Management',
            'description': 'Your pain levels are concerning. Please consult with your healthcare provider about pain management options.',
            'priority': 'urgent'
        })
    elif wellness_tracking.pain_level > 3:
        recommendations.append({
            'type': 'wellness',
            'title': 'Pain Relief Activities',
            'description': 'Consider gentle activities that might help with pain relief, such as warm baths, gentle stretching, or massage therapy.',
            'priority': 'medium'
        })
    
    # Check energy levels
    if wellness_tracking.energy_level == 'exhausted':
        recommendations.append({
            'type': 'nutrition',
            'title': 'Energy-Boosting Nutrition',
            'description': 'Focus on nutrient-dense foods that can help boost your energy. Consider iron-rich foods and staying well-hydrated.',
            'priority': 'medium'
        })
    
    # Create recommendation objects
    for rec_data in recommendations:
        CareRecommendation.objects.get_or_create(
            user=user,
            recommendation_type=rec_data['type'],
            title=rec_data['title'],
            defaults={
                'description': rec_data['description'],
                'priority': rec_data['priority'],
                'ai_confidence': 0.8,
                'due_date': timezone.now() + timedelta(days=3)
            }
        )


@login_required
@require_POST
@csrf_exempt
def get_ai_response(request):
    """Generate AI response for a conversation"""
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id, 
            user=request.user
        )
        
        # Get the last user message to respond to
        last_message = conversation.messages.filter(sender='user').order_by('-created_at').first()
        
        if not last_message:
            return JsonResponse({'success': False, 'error': 'No user message found'})
        
        # Generate AI response
        ai_response = generate_ai_response(
            last_message.content, 
            'supportive', 
            request.user
        )
        
        # Create AI message
        message = Message.objects.create(
            conversation=conversation,
            sender='ai',
            content=ai_response
        )
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'message_id': str(message.id)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def get_personalized_insights(request):
    """Get personalized AI insights for the user"""
    try:
        ai_engine = AIBuddyEngine(request.user)
        
        # Get wellness trends and insights
        wellness_insights = ai_engine.context['wellness_trends']
        
        # Generate insight message
        if wellness_insights.get('status') == 'no_data':
            insight_message = "I'd love to learn more about how you're doing! Try tracking your wellness for a few days so I can provide personalized insights."
        else:
            # Build insight based on trends
            insight_parts = []
            
            if wellness_insights.get('mood_trend') == 'improving':
                insight_parts.append("Your mood has been trending upward - that's wonderful to see!")
            elif wellness_insights.get('mood_trend') == 'declining':
                insight_parts.append("I've noticed your mood has been challenging lately. Remember, it's okay to have difficult days.")
            
            if wellness_insights.get('sleep_trend') == 'improving':
                insight_parts.append("Your sleep patterns are improving, which is great for your recovery.")
            elif wellness_insights.get('sleep_trend') == 'declining':
                insight_parts.append("Your sleep has been declining - this is often the biggest challenge in early motherhood.")
            
            if wellness_insights.get('avg_pain') > 5:
                insight_parts.append("You've been experiencing significant pain levels. Please don't hesitate to reach out to your healthcare provider.")
            
            if insight_parts:
                insight_message = " ".join(insight_parts)
            else:
                insight_message = f"You've been tracking consistently for {wellness_insights.get('data_points', 0)} days - keep up the great self-awareness!"
        
        # Get suggested actions
        suggested_services = ai_engine.suggest_services()
        
        return JsonResponse({
            'success': True,
            'insights': {
                'message': insight_message,
                'wellness_trends': wellness_insights,
                'suggested_services': suggested_services[:3]
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def get_smart_recommendations(request):
    """Generate new smart recommendations based on current state"""
    try:
        ai_engine = AIBuddyEngine(request.user)
        
        # Get the user's latest wellness tracking
        latest_wellness = WellnessTracking.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        if latest_wellness:
            new_recommendations = ai_engine.generate_recommendations(latest_wellness)
            
            # Create recommendation objects
            recommendations_created = []
            for rec_data in new_recommendations:
                recommendation, created = CareRecommendation.objects.get_or_create(
                    user=request.user,
                    recommendation_type=rec_data['type'],
                    title=rec_data['title'],
                    defaults={
                        'description': rec_data['description'],
                        'priority': rec_data['priority'],
                        'ai_confidence': rec_data['confidence'],
                        'due_date': timezone.now() + timedelta(days=3),
                        'metadata': {'generated_on_demand': True}
                    }
                )
                
                if created:
                    recommendations_created.append({
                        'id': recommendation.id,
                        'title': recommendation.title,
                        'description': recommendation.description,
                        'priority': recommendation.priority,
                        'type': recommendation.recommendation_type
                    })
            
            return JsonResponse({
                'success': True,
                'recommendations_created': len(recommendations_created),
                'recommendations': recommendations_created
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No wellness data found. Please track your wellness first.'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def ask_ai_question(request):
    """Allow users to ask specific questions to the AI buddy"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        
        if not question:
            return JsonResponse({'success': False, 'error': 'Question cannot be empty'})
        
        # Generate AI response
        ai_engine = AIBuddyEngine(request.user)
        response = ai_engine.generate_response(question, conversation_type='general')
        
        # Create a mini-conversation for this Q&A
        conversation = Conversation.objects.create(
            user=request.user,
            conversation_type='general',
            title=f"Q: {question[:50]}..."
        )
        
        Message.objects.create(
            conversation=conversation,
            message_type='user',
            content=question
        )
        
        Message.objects.create(
            conversation=conversation,
            message_type='ai',
            content=response
        )
        
        return JsonResponse({
            'success': True,
            'response': response,
            'conversation_id': str(conversation.id)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_service_recommendations(request):
    """Get AI-powered service recommendations"""
    try:
        ai_engine = AIBuddyEngine(request.user)
        
        # Get current needs based on wellness data and conversation history
        topics = []
        
        # Analyze recent wellness data
        recent_wellness = WellnessTracking.objects.filter(
            user=request.user,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('-date')[:3]
        
        for wellness in recent_wellness:
            if wellness.mood in ['low', 'concerning']:
                topics.append('emotional_support')
            if wellness.pain_level > 3:
                topics.append('pain_management')
            if wellness.sleep_hours < 5:
                topics.append('rest_support')
            if wellness.energy_level in ['low', 'exhausted']:
                topics.append('wellness')
        
        # Get personalized service suggestions
        suggested_services = ai_engine.suggest_services(topics)
        
        return JsonResponse({
            'success': True,
            'services': suggested_services,
            'identified_needs': topics
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def conversation_list_api(request):
    """API endpoint to get user's conversations"""
    conversations = Conversation.objects.filter(
        user=request.user, is_active=True
    ).order_by('-updated_at')
    
    conversation_data = []
    for conv in conversations:
        last_message = conv.messages.order_by('-created_at').first()
        conversation_data.append({
            'id': str(conv.id),
            'title': conv.title,
            'last_message': last_message.content if last_message else '',
            'message_count': conv.messages.count(),
            'updated_at': conv.updated_at.isoformat()
        })
    
    return JsonResponse({'conversations': conversation_data})
