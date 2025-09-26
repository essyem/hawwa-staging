"""
Enhanced user profile management views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import User
from .profile_models import (
    MotherProfile, AccommodationProviderProfile, CaretakerProviderProfile,
    WellnessProviderProfile, MeditationConsultantProfile, MentalHealthConsultantProfile,
    FoodProviderProfile
)
from bookings.models import Booking
from services.models import Service, ServiceReview
from ai_buddy.models import WellnessTracking, Conversation, AIBuddyProfile
from vendors.models import VendorProfile


class ProfileDashboardView(LoginRequiredMixin, TemplateView):
    """Enhanced user profile dashboard with comprehensive information"""
    template_name = 'accounts/profile_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Basic user info
        context['user'] = user
        context['profile'] = self._get_user_profile(user)
        
        # Dashboard statistics
        context['dashboard_stats'] = self._get_dashboard_stats(user)
        
        # Recent activity
        context['recent_bookings'] = self._get_recent_bookings(user)
        context['upcoming_bookings'] = self._get_upcoming_bookings(user)
        
        # AI Buddy integration
        context['ai_buddy_stats'] = self._get_ai_buddy_stats(user)
        context['wellness_summary'] = self._get_wellness_summary(user)
        
        # Account metrics
        context['account_metrics'] = self._get_account_metrics(user)
        
        return context
    
    def _get_user_profile(self, user):
        """Get the appropriate profile based on user type"""
        profile_mappings = {
            'MOTHER': MotherProfile,
            'ACCOMMODATION': AccommodationProviderProfile,
            'CARETAKER': CaretakerProviderProfile,
            'WELLNESS': WellnessProviderProfile,
            'MEDITATION': MeditationConsultantProfile,
            'MENTAL_HEALTH': MentalHealthConsultantProfile,
            'FOOD': FoodProviderProfile,
        }
        
        profile_class = profile_mappings.get(user.user_type)
        if profile_class:
            try:
                return profile_class.objects.get(user=user)
            except profile_class.DoesNotExist:
                return None
        return None
    
    def _get_dashboard_stats(self, user):
        """Get comprehensive dashboard statistics"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Booking statistics
        total_bookings = Booking.objects.filter(user=user).count()
        recent_bookings = Booking.objects.filter(
            user=user, 
            created_at__gte=thirty_days_ago
        ).count()
        
        # Service interactions
        service_reviews = ServiceReview.objects.filter(user=user).count()
        
        # Vendor profile if applicable
        vendor_stats = {}
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            vendor_stats = {
                'has_vendor_profile': True,
                'vendor_bookings': Booking.objects.filter(
                    service__vendor_profile=vendor_profile
                ).count(),
                'vendor_revenue': Booking.objects.filter(
                    service__vendor_profile=vendor_profile,
                    status='confirmed'
                ).aggregate(total=Sum('service__price'))['total'] or 0
            }
        except VendorProfile.DoesNotExist:
            vendor_stats = {'has_vendor_profile': False}
        
        return {
            'total_bookings': total_bookings,
            'recent_bookings': recent_bookings,
            'service_reviews': service_reviews,
            'account_age_days': (now - user.date_joined).days,
            'vendor_stats': vendor_stats
        }
    
    def _get_recent_bookings(self, user):
        """Get recent bookings for the user"""
        return Booking.objects.filter(
            user=user
        ).select_related(
            'service', 'service__vendor_profile__user'
        ).order_by('-created_at')[:5]
    
    def _get_upcoming_bookings(self, user):
        """Get upcoming bookings for the user"""
        return Booking.objects.filter(
            user=user,
            start_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).select_related(
            'service', 'service__vendor_profile__user'
        ).order_by('start_date', 'start_time')[:5]
    
    def _get_ai_buddy_stats(self, user):
        """Get AI buddy and wellness statistics"""
        try:
            ai_profile = AIBuddyProfile.objects.get(user=user)
            conversation_count = Conversation.objects.filter(user=user).count()
            
            return {
                'has_ai_profile': True,
                'buddy_name': ai_profile.buddy_name,
                'conversation_count': conversation_count,
                'last_conversation': Conversation.objects.filter(
                    user=user
                ).order_by('-updated_at').first()
            }
        except AIBuddyProfile.DoesNotExist:
            return {'has_ai_profile': False}
    
    def _get_wellness_summary(self, user):
        """Get wellness tracking summary"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        wellness_entries = WellnessTracking.objects.filter(
            user=user,
            date__gte=thirty_days_ago.date()
        )
        
        if wellness_entries.exists():
            return {
                'entry_count': wellness_entries.count(),
                'avg_mood': wellness_entries.aggregate(
                    avg=Avg('mood_rating')
                )['avg'] or 0,
                'avg_energy': wellness_entries.aggregate(
                    avg=Avg('energy_level')
                )['avg'] or 0,
                'avg_sleep': wellness_entries.aggregate(
                    avg=Avg('sleep_hours')
                )['avg'] or 0,
                'latest_entry': wellness_entries.order_by('-date').first()
            }
        
        return {'entry_count': 0}
    
    def _get_account_metrics(self, user):
        """Get account-related metrics"""
        return {
            'profile_completion': self._calculate_profile_completion(user),
            'verification_status': user.is_verified,
            'last_login': user.last_login,
            'notification_preferences': {
                'email': user.receive_emails,
                'sms': user.receive_sms
            }
        }
    
    def _calculate_profile_completion(self, user):
        """Calculate profile completion percentage"""
        # Check basic user fields
        basic_fields = [
            user.first_name, user.last_name, user.phone,
            user.address, user.city, user.country
        ]
        filled_basic = sum(1 for field in basic_fields if field)
        
        # Check profile-specific fields
        profile = self._get_user_profile(user)
        profile_completion = 0
        
        if profile:
            if user.user_type == 'MOTHER':
                profile_fields = [
                    profile.due_date, profile.birth_date, profile.baby_name,
                    profile.blood_type, profile.emergency_contact_name,
                    profile.emergency_contact_phone
                ]
                profile_completion = sum(1 for field in profile_fields if field) / len(profile_fields) * 100
        
        basic_completion = (filled_basic / len(basic_fields)) * 100
        total_completion = (basic_completion + profile_completion) / 2
        
        return round(total_completion)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile information"""
    model = User
    template_name = 'accounts/profile_edit.html'
    fields = [
        'first_name', 'last_name', 'phone', 'profile_picture',
        'address', 'city', 'state', 'country', 'postal_code',
        'receive_emails', 'receive_sms'
    ]
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return '/accounts/profile/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get profile-specific form if needed
        profile_form = self._get_profile_form(user)
        if profile_form:
            context['profile_form'] = profile_form
        
        return context
    
    def _get_profile_form(self, user):
        """Get the appropriate profile form based on user type"""
        # This would include specific profile forms for different user types
        return None


class BookingHistoryView(LoginRequiredMixin, TemplateView):
    """View booking history with filtering and search"""
    template_name = 'accounts/booking_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all bookings for the user
        bookings = Booking.objects.filter(user=user).select_related(
            'service', 'service__vendor_profile__user'
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'all':
            bookings = bookings.filter(status=status_filter)
        
        date_filter = self.request.GET.get('date_range')
        if date_filter:
            if date_filter == 'last_month':
                start_date = timezone.now() - timedelta(days=30)
                bookings = bookings.filter(created_at__gte=start_date)
            elif date_filter == 'last_year':
                start_date = timezone.now() - timedelta(days=365)
                bookings = bookings.filter(created_at__gte=start_date)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(bookings, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['bookings'] = page_obj
        context['booking_stats'] = self._get_booking_stats(user)
        
        return context
    
    def _get_booking_stats(self, user):
        """Get booking statistics"""
        bookings = Booking.objects.filter(user=user)
        
        return {
            'total_bookings': bookings.count(),
            'completed_bookings': bookings.filter(status='completed').count(),
            'pending_bookings': bookings.filter(status='pending').count(),
            'cancelled_bookings': bookings.filter(status='cancelled').count(),
            'total_spent': bookings.filter(
                status='completed'
            ).aggregate(
                total=Sum('service__price')
            )['total'] or 0
        }


class PreferencesView(LoginRequiredMixin, TemplateView):
    """User preferences and settings management"""
    template_name = 'accounts/preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get AI buddy preferences
        try:
            ai_profile = AIBuddyProfile.objects.get(user=user)
            context['ai_profile'] = ai_profile
        except AIBuddyProfile.DoesNotExist:
            context['ai_profile'] = None
        
        # Get notification preferences
        context['notification_preferences'] = {
            'email_notifications': user.receive_emails,
            'sms_notifications': user.receive_sms
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle preference updates"""
        user = request.user
        
        # Update notification preferences
        if 'email_notifications' in request.POST:
            user.receive_emails = request.POST.get('email_notifications') == 'on'
        
        if 'sms_notifications' in request.POST:
            user.receive_sms = request.POST.get('sms_notifications') == 'on'
        
        user.save()
        
        # Update AI buddy preferences if provided
        ai_buddy_name = request.POST.get('ai_buddy_name')
        ai_personality = request.POST.get('ai_personality')
        
        if ai_buddy_name or ai_personality:
            ai_profile, created = AIBuddyProfile.objects.get_or_create(
                user=user,
                defaults={
                    'buddy_name': ai_buddy_name or 'Hawwa',
                    'personality_type': ai_personality or 'supportive'
                }
            )
            
            if not created:
                if ai_buddy_name:
                    ai_profile.buddy_name = ai_buddy_name
                if ai_personality:
                    ai_profile.personality_type = ai_personality
                ai_profile.save()
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('accounts:preferences')


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    """Security settings and account management"""
    template_name = 'accounts/security_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['user'] = user
        context['login_activity'] = self._get_login_activity(user)
        
        return context
    
    def _get_login_activity(self, user):
        """Get recent login activity (placeholder - would need session tracking)"""
        return {
            'last_login': user.last_login,
            'account_created': user.date_joined,
            'password_last_changed': None  # Would need additional tracking
        }


@login_required
def profile_analytics_api(request):
    """API endpoint for profile analytics data"""
    user = request.user
    
    # Get wellness trends
    thirty_days_ago = timezone.now() - timedelta(days=30)
    wellness_entries = WellnessTracking.objects.filter(
        user=user,
        date__gte=thirty_days_ago.date()
    ).order_by('date')
    
    wellness_data = {
        'labels': [entry.date.strftime('%Y-%m-%d') for entry in wellness_entries],
        'mood_data': [entry.mood_rating for entry in wellness_entries],
        'energy_data': [entry.energy_level for entry in wellness_entries],
        'sleep_data': [entry.sleep_hours for entry in wellness_entries]
    }
    
    # Get booking trends
    booking_data = []
    for i in range(6):  # Last 6 months
        month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
        month_bookings = Booking.objects.filter(
            user=user,
            created_at__gte=month_start,
            created_at__lt=month_start + timedelta(days=30)
        ).count()
        booking_data.append({
            'month': month_start.strftime('%B'),
            'bookings': month_bookings
        })
    
    return JsonResponse({
        'wellness_trends': wellness_data,
        'booking_trends': list(reversed(booking_data))
    })


@login_required
def update_profile_picture(request):
    """Update user profile picture via AJAX"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        return JsonResponse({
            'success': True,
            'image_url': user.profile_picture.url
        })
    
    return JsonResponse({'success': False, 'error': 'No image provided'})