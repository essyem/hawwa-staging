# import openai  # Temporarily commented out for testing
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Avg
from .models import (
    Conversation, Message, WellnessTracking, 
    CareRecommendation, AIBuddyProfile, Milestone
)
from bookings.models import Booking
from services.models import Service
import logging

logger = logging.getLogger(__name__)


class AIBuddyEngine:
    """Enhanced AI Buddy Engine with contextual awareness and personalization"""
    
    def __init__(self, user):
        self.user = user
        self.ai_profile = self._get_ai_profile()
        self.context = self._build_user_context()
    
    def _get_ai_profile(self) -> AIBuddyProfile:
        """Get or create AI buddy profile for the user"""
        profile, created = AIBuddyProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'buddy_name': 'Hawwa',
                'personality_type': 'supportive'
            }
        )
        return profile
    
    def _build_user_context(self) -> Dict:
        """Build comprehensive user context for personalized responses"""
        context = {
            'user_name': self.user.get_full_name() or self.user.username,
            'buddy_name': self.ai_profile.buddy_name,
            'personality': self.ai_profile.personality_type,
            'language': self.ai_profile.language_preference,
            'wellness_trends': self._get_wellness_trends(),
            'recent_bookings': self._get_recent_bookings(),
            'pending_recommendations': self._get_pending_recommendations(),
            'milestones': self._get_current_milestones(),
            'conversation_history': self._get_conversation_summary(),
        }
        return context
    
    def _get_wellness_trends(self) -> Dict:
        """Analyze recent wellness trends"""
        recent_wellness = WellnessTracking.objects.filter(
            user=self.user,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('-date')[:7]
        
        if not recent_wellness:
            return {'status': 'no_data'}
        
        # Calculate averages and trends
        moods = [w.mood for w in recent_wellness]
        sleep_hours = [w.sleep_hours for w in recent_wellness]
        pain_levels = [w.pain_level for w in recent_wellness]
        
        mood_score_map = {
            'excellent': 5, 'good': 4, 'neutral': 3, 'low': 2, 'concerning': 1
        }
        
        avg_mood_score = sum(mood_score_map.get(mood, 3) for mood in moods) / len(moods)
        avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else 0
        avg_pain = sum(pain_levels) / len(pain_levels) if pain_levels else 0
        
        # Determine trends
        trends = {
            'mood_trend': self._calculate_trend([mood_score_map.get(mood, 3) for mood in moods]),
            'sleep_trend': self._calculate_trend(sleep_hours),
            'pain_trend': self._calculate_trend(pain_levels),
            'avg_mood_score': avg_mood_score,
            'avg_sleep': avg_sleep,
            'avg_pain': avg_pain,
            'latest_mood': moods[0] if moods else 'neutral',
            'data_points': len(recent_wellness)
        }
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if values are trending up, down, or stable"""
        if len(values) < 2:
            return 'stable'
        
        recent_avg = sum(values[:3]) / min(3, len(values))
        older_avg = sum(values[3:]) / max(1, len(values) - 3)
        
        diff = (recent_avg - older_avg) / max(older_avg, 1)
        
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _get_recent_bookings(self) -> Dict:
        """Get recent and upcoming bookings"""
        recent_bookings = Booking.objects.filter(
            user=self.user,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-start_date')[:5]
        
        upcoming_bookings = Booking.objects.filter(
            user=self.user,
            start_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('start_date')[:3]
        
        return {
            'recent_count': recent_bookings.count(),
            'upcoming_count': upcoming_bookings.count(),
            'recent_bookings': [
                {
                    'service': b.service.name,
                    'date': b.start_date,
                    'status': b.status
                } for b in recent_bookings
            ],
            'upcoming_bookings': [
                {
                    'service': b.service.name,
                    'date': b.start_date,
                    'status': b.status
                } for b in upcoming_bookings
            ]
        }
    
    def _get_pending_recommendations(self) -> List[Dict]:
        """Get pending care recommendations"""
        recommendations = CareRecommendation.objects.filter(
            user=self.user,
            is_completed=False,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-priority', '-created_at')[:5]
        
        return [
            {
                'type': r.recommendation_type,
                'title': r.title,
                'priority': r.priority,
                'created_at': r.created_at
            } for r in recommendations
        ]
    
    def _get_current_milestones(self) -> List[Dict]:
        """Get current active milestones"""
        milestones = Milestone.objects.filter(
            user=self.user,
            is_achieved=False
        ).order_by('-created_at')[:3]
        
        return [
            {
                'title': m.title,
                'type': m.milestone_type,
                'progress': m.progress_percentage,
                'target_date': m.target_date
            } for m in milestones
        ]
    
    def _get_conversation_summary(self) -> Dict:
        """Get summary of recent conversations"""
        recent_conversations = Conversation.objects.filter(
            user=self.user,
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:3]
        
        return {
            'recent_count': recent_conversations.count(),
            'common_topics': [c.conversation_type for c in recent_conversations],
            'last_conversation_date': recent_conversations.first().updated_at if recent_conversations else None
        }
    
    def generate_response(self, message: str, conversation_type: str = 'general', conversation_id: str = None) -> str:
        """Generate intelligent AI response based on context and message"""
        
        # Analyze the message for intent and topics
        message_analysis = self._analyze_message(message)
        
        # Build context-aware prompt
        prompt = self._build_prompt(message, message_analysis, conversation_type)
        
        # Generate response using AI service or fallback
        try:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                response = self._generate_openai_response(prompt)
            else:
                response = self._generate_fallback_response(message, message_analysis, conversation_type)
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            response = self._generate_fallback_response(message, message_analysis, conversation_type)
        
        # Post-process response
        response = self._post_process_response(response, message_analysis)
        
        return response
    
    def _analyze_message(self, message: str) -> Dict:
        """Analyze message for intent, sentiment, and topics"""
        message_lower = message.lower()
        
        # Detect emotional indicators
        emotional_keywords = {
            'positive': ['happy', 'good', 'great', 'wonderful', 'excited', 'grateful', 'better'],
            'negative': ['sad', 'tired', 'exhausted', 'worried', 'anxious', 'overwhelmed', 'stressed'],
            'pain': ['pain', 'hurt', 'ache', 'sore', 'uncomfortable'],
            'sleep': ['sleep', 'tired', 'exhausted', 'rest', 'nap'],
            'feeding': ['feeding', 'breastfeeding', 'nursing', 'bottle', 'formula'],
            'mood': ['mood', 'feeling', 'emotional', 'emotions', 'depressed', 'anxiety']
        }
        
        detected_topics = []
        sentiment = 'neutral'
        
        for topic, keywords in emotional_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_topics.append(topic)
                if topic in ['negative', 'pain']:
                    sentiment = 'negative'
                elif topic == 'positive' and sentiment != 'negative':
                    sentiment = 'positive'
        
        # Detect questions
        is_question = '?' in message or any(
            message_lower.startswith(q) for q in ['how', 'what', 'when', 'where', 'why', 'can', 'should', 'is', 'are', 'do']
        )
        
        # Detect urgency
        urgent_keywords = ['emergency', 'urgent', 'help', 'pain', 'bleeding', 'fever']
        is_urgent = any(keyword in message_lower for keyword in urgent_keywords)
        
        return {
            'sentiment': sentiment,
            'topics': detected_topics,
            'is_question': is_question,
            'is_urgent': is_urgent,
            'length': len(message.split()),
            'emotional_indicators': detected_topics
        }
    
    def _build_prompt(self, message: str, analysis: Dict, conversation_type: str) -> str:
        """Build context-aware prompt for AI generation"""
        
        context_summary = f"""
You are {self.context['buddy_name']}, a caring and knowledgeable AI companion for postpartum mothers. 
Your personality is {self.context['personality']} and you're talking to {self.context['user_name']}.

CONTEXT:
- User's recent wellness trends: {self.context['wellness_trends']}
- Recent bookings: {self.context['recent_bookings']['recent_count']} in the last month
- Upcoming appointments: {self.context['recent_bookings']['upcoming_count']}
- Pending recommendations: {len(self.context['pending_recommendations'])}
- Active milestones: {len(self.context['milestones'])}

CONVERSATION TYPE: {conversation_type}

MESSAGE ANALYSIS:
- Sentiment: {analysis['sentiment']}
- Topics detected: {', '.join(analysis['topics'])}
- Is question: {analysis['is_question']}
- Urgency level: {'high' if analysis['is_urgent'] else 'normal'}

USER MESSAGE: "{message}"

Respond in a {self.context['personality']} manner, keeping your response:
1. Empathetic and understanding
2. Relevant to their context and current situation
3. Actionable when appropriate
4. No longer than 150 words
5. In a warm, conversational tone

If the message indicates urgency or concerning symptoms, acknowledge the seriousness and suggest professional help.
If they mention specific wellness tracking data, reference their trends.
If they ask about services, you can suggest relevant bookings.
"""
        
        return context_summary
    
    def _generate_openai_response(self, prompt: str) -> str:
        """Generate response using OpenAI API"""
        # Temporarily disabled for testing - falling back to rule-based response
        raise Exception("OpenAI not available - using fallback")
        
        # try:
        #     openai.api_key = settings.OPENAI_API_KEY
        #     
        #     response = openai.ChatCompletion.create(
        #         model="gpt-3.5-turbo",
        #         messages=[
        #             {"role": "system", "content": prompt},
        #         ],
        #         max_tokens=200,
        #         temperature=0.7,
        #         top_p=1,
        #         frequency_penalty=0.5,
        #         presence_penalty=0.3
        #     )
        #     
        #     return response.choices[0].message.content.strip()
        #     
        # except Exception as e:
        #     logger.error(f"OpenAI API error: {e}")
        #     raise
    
    def _generate_fallback_response(self, message: str, analysis: Dict, conversation_type: str) -> str:
        """Generate fallback response using rule-based system"""
        
        buddy_name = self.context['buddy_name']
        personality = self.context['personality']
        
        # Handle urgent messages first
        if analysis['is_urgent']:
            return f"I can see this sounds urgent, {self.context['user_name']}. If you're experiencing a medical emergency, please contact your healthcare provider immediately or call emergency services. I'm here to support you, but professional medical care is most important right now."
        
        # Handle different conversation types and sentiments
        if conversation_type == 'wellness':
            if analysis['sentiment'] == 'negative':
                response = f"I hear that you're going through a tough time right now. Your feelings are completely valid, and it's important that you're checking in with yourself."
                
                # Add context based on wellness trends
                if self.context['wellness_trends'].get('mood_trend') == 'declining':
                    response += " I've noticed you've been tracking some challenging days lately. Remember, healing isn't linear."
                
                if 'sleep' in analysis['topics']:
                    response += " Sleep deprivation can make everything feel harder. Have you been able to rest when the baby sleeps?"
                
            elif analysis['sentiment'] == 'positive':
                response = f"It's wonderful to hear some positivity in your voice! Those good moments are so precious during this time."
                
                if self.context['wellness_trends'].get('mood_trend') == 'improving':
                    response += " I can see in your recent tracking that things have been looking up - that's fantastic!"
            
            else:  # neutral
                response = f"Thank you for checking in with yourself today. How are you feeling physically and emotionally right now?"
        
        elif conversation_type == 'nutrition':
            if 'feeding' in analysis['topics']:
                response = f"Feeding questions are so common - you're definitely not alone in this! Whether you're breastfeeding, bottle feeding, or combination feeding, what matters most is that both you and baby are getting the nutrition you need."
            else:
                response = f"Taking care of your nutrition is such an important part of your recovery. Your body has done something incredible and deserves to be nourished well."
                
                if self.context['wellness_trends'].get('avg_sleep') < 5:
                    response += " I notice you haven't been getting much sleep - proper nutrition can help with energy levels."
        
        elif conversation_type == 'emotional':
            response = f"I'm really glad you felt comfortable reaching out about this. Your emotional wellbeing is just as important as your physical recovery."
            
            if analysis['sentiment'] == 'negative':
                response += " What you're feeling is valid, and you don't have to go through this alone."
                
                # Check for pending emotional recommendations
                emotional_recs = [r for r in self.context['pending_recommendations'] if r['type'] == 'emotional']
                if emotional_recs:
                    response += " I have some gentle suggestions that might help - would you like to hear them?"
        
        else:  # general conversation
            if analysis['is_question']:
                response = f"That's a great question! I'm here to help however I can."
            else:
                response = f"Thank you for sharing that with me. I'm here to listen and support you."
            
            # Add contextual elements
            if self.context['recent_bookings']['upcoming_count'] > 0:
                response += f" I see you have some appointments coming up - that's great that you're taking care of yourself!"
        
        # Add personality flavor
        if personality == 'gentle':
            response = response.replace("That's great", "That's lovely").replace("wonderful", "beautiful")
        elif personality == 'practical':
            response += " What specific support would be most helpful for you right now?"
        elif personality == 'friendly':
            response = response.replace("Thank you", "Thanks so much")
        
        return response
    
    def _post_process_response(self, response: str, analysis: Dict) -> str:
        """Post-process and enhance the response"""
        
        # Add relevant service suggestions if appropriate
        if any(topic in analysis['topics'] for topic in ['pain', 'sleep', 'mood']):
            response += self._suggest_relevant_services(analysis['topics'])
        
        # Add milestone encouragement if relevant
        if self.context['milestones'] and analysis['sentiment'] != 'negative':
            response += f" Keep up the great work on your recovery goals!"
        
        # Ensure response ends appropriately
        if not response.endswith(('.', '!', '?')):
            response += "."
        
        return response
    
    def _suggest_relevant_services(self, topics: List[str]) -> str:
        """Suggest relevant services based on detected topics"""
        suggestions = []
        
        if 'pain' in topics:
            suggestions.append("massage therapy or physical therapy")
        if 'sleep' in topics:
            suggestions.append("sleep support services")
        if 'mood' in topics or 'negative' in topics:
            suggestions.append("counseling or wellness sessions")
        if 'feeding' in topics:
            suggestions.append("lactation consultation")
        
        if suggestions:
            if len(suggestions) == 1:
                return f" If you'd like, I can help you find {suggestions[0]} services in your area."
            else:
                return f" If you'd like, I can help you find services like {', '.join(suggestions[:-1])}, or {suggestions[-1]} in your area."
        
        return ""
    
    def generate_recommendations(self, wellness_data: WellnessTracking = None) -> List[Dict]:
        """Generate intelligent care recommendations"""
        recommendations = []
        
        # Use provided wellness data or get latest
        if not wellness_data:
            wellness_data = WellnessTracking.objects.filter(user=self.user).order_by('-date').first()
        
        if not wellness_data:
            return recommendations
        
        # Analyze patterns and generate recommendations
        trends = self.context['wellness_trends']
        
        # Sleep recommendations
        if wellness_data.sleep_hours < 4:
            recommendations.append({
                'type': 'rest',
                'title': 'Emergency Sleep Support',
                'description': 'You\'re getting critically low sleep. Consider asking family/friends for help with night feeds, or look into postpartum doula services.',
                'priority': 'urgent',
                'confidence': 0.95
            })
        elif trends.get('sleep_trend') == 'declining':
            recommendations.append({
                'type': 'rest',
                'title': 'Sleep Pattern Improvement',
                'description': 'Your sleep has been declining. Try establishing a consistent bedtime routine and consider sleep hygiene improvements.',
                'priority': 'high',
                'confidence': 0.8
            })
        
        # Mood recommendations
        if wellness_data.mood in ['low', 'concerning']:
            if trends.get('mood_trend') == 'declining':
                recommendations.append({
                    'type': 'emotional',
                    'title': 'Professional Mental Health Support',
                    'description': 'Your mood has been consistently low. Please consider speaking with a mental health professional who specializes in postpartum care.',
                    'priority': 'urgent',
                    'confidence': 0.9
                })
            else:
                recommendations.append({
                    'type': 'emotional',
                    'title': 'Mood Support Activities',
                    'description': 'Try gentle activities that can help lift your mood: short walks, connecting with friends, or mindfulness exercises.',
                    'priority': 'medium',
                    'confidence': 0.75
                })
        
        # Pain management
        if wellness_data.pain_level > 6:
            recommendations.append({
                'type': 'medical',
                'title': 'Pain Management Consultation',
                'description': 'High pain levels need professional attention. Contact your healthcare provider to discuss pain management options.',
                'priority': 'urgent',
                'confidence': 0.95
            })
        elif wellness_data.pain_level > 3:
            recommendations.append({
                'type': 'wellness',
                'title': 'Pain Relief Techniques',
                'description': 'Consider gentle pain relief methods: warm baths, light stretching, or professional massage therapy.',
                'priority': 'medium',
                'confidence': 0.8
            })
        
        # Energy and nutrition
        if wellness_data.energy_level == 'exhausted' and trends.get('avg_sleep') > 6:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Energy-Boosting Nutrition',
                'description': 'You\'re sleeping adequately but still exhausted. Focus on iron-rich foods, staying hydrated, and consider a nutritional assessment.',
                'priority': 'medium',
                'confidence': 0.7
            })
        
        return recommendations
    
    def suggest_services(self, topics: List[str] = None, location: str = None) -> List[Dict]:
        """Suggest relevant services based on user needs"""
        if not topics:
            # Infer topics from recent wellness data
            latest_wellness = WellnessTracking.objects.filter(user=self.user).order_by('-date').first()
            topics = []
            
            if latest_wellness:
                if latest_wellness.mood in ['low', 'concerning']:
                    topics.append('emotional_support')
                if latest_wellness.pain_level > 3:
                    topics.append('pain_management')
                if latest_wellness.sleep_hours < 5:
                    topics.append('rest_support')
                if latest_wellness.energy_level in ['low', 'exhausted']:
                    topics.append('wellness')
        
        # Map topics to service categories
        service_mapping = {
            'emotional_support': ['counseling', 'mental health', 'therapy'],
            'pain_management': ['massage', 'physical therapy', 'pain relief'],
            'rest_support': ['sleep support', 'night care', 'doula'],
            'wellness': ['wellness', 'spa', 'nutrition'],
            'feeding': ['lactation', 'breastfeeding', 'nutrition'],
            'recovery': ['postpartum care', 'recovery', 'healing']
        }
        
        suggested_services = []
        
        for topic in topics:
            if topic in service_mapping:
                # Find services matching these keywords
                keywords = service_mapping[topic]
                for keyword in keywords:
                    services = Service.objects.filter(
                        Q(name__icontains=keyword) |
                        Q(description__icontains=keyword) |
                        Q(short_description__icontains=keyword),
                        status='available'
                    )[:3]
                    
                    for service in services:
                        suggested_services.append({
                            'service_id': service.id,
                            'name': service.name,
                            'description': service.short_description,
                            'price': service.price,
                            'category': service.category.name,
                            'relevance_topic': topic
                        })
        
        # Remove duplicates and limit results
        seen_services = set()
        unique_services = []
        for service in suggested_services:
            if service['service_id'] not in seen_services:
                seen_services.add(service['service_id'])
                unique_services.append(service)
                if len(unique_services) >= 5:
                    break
        
        return unique_services