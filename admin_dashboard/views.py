"""
Enhanced admin dashboard views for comprehensive platform management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from accounts.models import User
from accounts.profile_models import (
    MotherProfile, AccommodationProviderProfile, CaretakerProviderProfile,
    WellnessProviderProfile, MeditationConsultantProfile, MentalHealthConsultantProfile,
    FoodProviderProfile
)
from bookings.models import Booking
from services.models import Service, ServiceReview
from vendors.models import VendorProfile
from ai_buddy.models import WellnessTracking, Conversation, AIBuddyProfile


def is_admin_user(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_staff or user.user_type == 'ADMIN')


@login_required
def admin_dashboard_simple(request):
    """Simple admin dashboard view for testing"""
    context = {
        'total_users': 147,
        'total_revenue': '12,450',
        'active_sessions': 89,
        'wellness_entries': 1234,
        'pending_invoices': 7,
        'overdue_payments': 3,
        'active_conversations': 23,
        'daily_messages': 156,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def system_test(request):
    """System integration test page"""
    return render(request, 'system_test.html')


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Main admin dashboard with comprehensive platform overview"""
    template_name = 'admin_dashboard/dashboard.html'
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overview statistics
        context['overview_stats'] = self._get_overview_stats()
        
        # User statistics
        context['user_stats'] = self._get_user_stats()
        
        # Booking statistics
        context['booking_stats'] = self._get_booking_stats()
        
        # Service statistics
        context['service_stats'] = self._get_service_stats()
        
        # Revenue analytics
        context['revenue_stats'] = self._get_revenue_stats()
        
        # Recent activity
        context['recent_activity'] = self._get_recent_activity()
        
        # Platform health metrics
        context['platform_health'] = self._get_platform_health()
        
        return context
    
    def _get_overview_stats(self):
        """Get high-level platform statistics"""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        total_users = User.objects.count()
        new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        total_bookings = Booking.objects.count()
        new_bookings_30d = Booking.objects.filter(created_at__gte=thirty_days_ago).count()
        
        total_services = Service.objects.count()
        active_vendors = VendorProfile.objects.filter(status='active').count()
        
        return {
            'total_users': total_users,
            'new_users_30d': new_users_30d,
            'user_growth_rate': (new_users_30d / max(total_users - new_users_30d, 1)) * 100,
            
            'total_bookings': total_bookings,
            'new_bookings_30d': new_bookings_30d,
            'booking_growth_rate': (new_bookings_30d / max(total_bookings - new_bookings_30d, 1)) * 100,
            
            'total_services': total_services,
            'active_vendors': active_vendors,
        }
    
    def _get_user_stats(self):
        """Get detailed user statistics"""
        user_types = User.objects.values('user_type').annotate(count=Count('id'))
        
        # User activity metrics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users_30d = User.objects.filter(last_login__gte=thirty_days_ago).count()
        
        # Verification status
        verified_users = User.objects.filter(is_verified=True).count()
        unverified_users = User.objects.filter(is_verified=False).count()
        
        return {
            'user_types': list(user_types),
            'active_users_30d': active_users_30d,
            'verified_users': verified_users,
            'unverified_users': unverified_users,
            'verification_rate': (verified_users / max(verified_users + unverified_users, 1)) * 100
        }
    
    def _get_booking_stats(self):
        """Get booking analytics"""
        now = timezone.now()
        
        # Status distribution
        booking_statuses = Booking.objects.values('status').annotate(count=Count('id'))
        
        # Daily bookings for last 30 days
        thirty_days_ago = now - timedelta(days=30)
        daily_bookings = []
        
        for i in range(30):
            date = (thirty_days_ago + timedelta(days=i)).date()
            count = Booking.objects.filter(start_date=date).count()
            daily_bookings.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # Average booking value
        avg_booking_value = Booking.objects.filter(
            status='completed'
        ).aggregate(avg=Avg('service__price'))['avg'] or 0
        
        return {
            'status_distribution': list(booking_statuses),
            'daily_bookings': daily_bookings,
            'avg_booking_value': float(avg_booking_value),
            'completion_rate': self._calculate_completion_rate()
        }
    
    def _get_service_stats(self):
        """Get service and vendor statistics"""
        # Service categories
        service_categories = Service.objects.values('category').annotate(count=Count('id'))
        
        # Top rated services
        top_services = Service.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(review_count__gte=1).order_by('-avg_rating')[:5]
        
        # Vendor performance
        vendor_performance = VendorProfile.objects.annotate(
            booking_count=Count('services__bookings'),
            total_revenue=Sum('services__bookings__service__price')
        ).filter(booking_count__gte=1).order_by('-total_revenue')[:10]
        
        return {
            'service_categories': list(service_categories),
            'top_services': top_services,
            'vendor_performance': vendor_performance
        }
    
    def _get_revenue_stats(self):
        """Get revenue analytics"""
        # Monthly revenue for last 12 months
        monthly_revenue = []
        now = timezone.now()
        
        for i in range(12):
            month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            revenue = Booking.objects.filter(
                status='completed',
                start_date__gte=month_start.date(),
                start_date__lte=month_end.date()
            ).aggregate(total=Sum('service__price'))['total'] or 0
            
            monthly_revenue.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': float(revenue)
            })
        
        # Total platform revenue
        total_revenue = Booking.objects.filter(
            status='completed'
        ).aggregate(total=Sum('service__price'))['total'] or 0
        
        return {
            'monthly_revenue': list(reversed(monthly_revenue)),
            'total_revenue': float(total_revenue),
            'average_monthly_revenue': float(total_revenue) / 12 if total_revenue else 0
        }
    
    def _get_recent_activity(self):
        """Get recent platform activity"""
        # Recent user registrations
        recent_users = User.objects.order_by('-date_joined')[:10]
        
        # Recent bookings
        recent_bookings = Booking.objects.select_related(
            'user', 'service', 'service__vendor_profile'
        ).order_by('-created_at')[:10]
        
        # Recent reviews
        recent_reviews = ServiceReview.objects.select_related(
            'user', 'service'
        ).order_by('-created_at')[:10]
        
        return {
            'recent_users': recent_users,
            'recent_bookings': recent_bookings,
            'recent_reviews': recent_reviews
        }
    
    def _get_platform_health(self):
        """Get platform health metrics"""
        # User engagement
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # AI buddy usage
        ai_conversations = Conversation.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Wellness tracking usage
        wellness_entries = WellnessTracking.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # System performance metrics (placeholder)
        return {
            'weekly_active_users': active_users,
            'monthly_ai_conversations': ai_conversations,
            'monthly_wellness_entries': wellness_entries,
            'system_uptime': 99.9,  # Would be calculated from monitoring
            'average_response_time': 0.2  # Would be calculated from monitoring
        }
    
    def _calculate_completion_rate(self):
        """Calculate booking completion rate"""
        total_bookings = Booking.objects.count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        return (completed_bookings / max(total_bookings, 1)) * 100


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """User management with search, filtering, and actions"""
    model = User
    template_name = 'admin_dashboard/user_management.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Filter by user type
        user_type = self.request.GET.get('user_type')
        if user_type and user_type != 'all':
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by verification status
        verified = self.request.GET.get('verified')
        if verified and verified != 'all':
            queryset = queryset.filter(is_verified=verified == 'true')
        
        # Filter by activity
        activity = self.request.GET.get('activity')
        if activity:
            if activity == 'active':
                queryset = queryset.filter(
                    last_login__gte=timezone.now() - timedelta(days=30)
                )
            elif activity == 'inactive':
                queryset = queryset.filter(
                    Q(last_login__lt=timezone.now() - timedelta(days=30)) |
                    Q(last_login__isnull=True)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['user_types'] = User.USER_TYPE_CHOICES
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'user_type': self.request.GET.get('user_type', 'all'),
            'verified': self.request.GET.get('verified', 'all'),
            'activity': self.request.GET.get('activity', 'all')
        }
        
        # Add user statistics
        context['user_stats'] = {
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'active_users': User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count()
        }
        
        return context


class BookingManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Booking management and oversight"""
    model = Booking
    template_name = 'admin_dashboard/booking_management.html'
    context_object_name = 'bookings'
    paginate_by = 25
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_queryset(self):
        queryset = Booking.objects.select_related(
            'user', 'service', 'service__vendor_profile'
        ).order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        date_range = self.request.GET.get('date_range')
        if date_range:
            if date_range == 'today':
                queryset = queryset.filter(start_date=timezone.now().date())
            elif date_range == 'week':
                week_ago = timezone.now() - timedelta(days=7)
                queryset = queryset.filter(created_at__gte=week_ago)
            elif date_range == 'month':
                month_ago = timezone.now() - timedelta(days=30)
                queryset = queryset.filter(created_at__gte=month_ago)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(service__name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add booking statistics
        context['booking_stats'] = {
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'completed_bookings': Booking.objects.filter(status='completed').count(),
            'cancelled_bookings': Booking.objects.filter(status='cancelled').count(),
            'total_revenue': Booking.objects.filter(
                status='completed'
            ).aggregate(total=Sum('service__price'))['total'] or 0
        }
        
        # Add filter options
        context['current_filters'] = {
            'status': self.request.GET.get('status', 'all'),
            'date_range': self.request.GET.get('date_range', 'all'),
            'search': self.request.GET.get('search', '')
        }
        
        return context


class VendorManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vendor approval and management"""
    model = VendorProfile
    template_name = 'admin_dashboard/vendor_management.html'
    context_object_name = 'vendors'
    paginate_by = 25
    
    def test_func(self):
        return is_admin_user(self.request.user)
    
    def get_queryset(self):
        queryset = VendorProfile.objects.select_related('user').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add vendor statistics
        context['vendor_stats'] = {
            'total_vendors': VendorProfile.objects.count(),
            'active_vendors': VendorProfile.objects.filter(status='active').count(),
            'pending_vendors': VendorProfile.objects.filter(status='pending').count(),
            'suspended_vendors': VendorProfile.objects.filter(status='suspended').count()
        }
        
        # Add filter options
        context['current_filters'] = {
            'status': self.request.GET.get('status', 'all'),
            'search': self.request.GET.get('search', '')
        }
        
        return context


@staff_member_required
def admin_analytics_api(request):
    """API endpoint for admin dashboard analytics"""
    # User growth data
    user_growth = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        users = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        
        user_growth.append({
            'month': month_start.strftime('%B'),
            'users': users
        })
    
    # Booking trends
    booking_trends = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        bookings = Booking.objects.filter(start_date=date).count()
        booking_trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'bookings': bookings
        })
    
    # Revenue trends
    revenue_trends = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=i*30)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        revenue = Booking.objects.filter(
            status='completed',
            start_date__gte=month_start.date(),
            start_date__lte=month_end.date()
        ).aggregate(total=Sum('service__price'))['total'] or 0
        
        revenue_trends.append({
            'month': month_start.strftime('%B'),
            'revenue': float(revenue)
        })
    
    return JsonResponse({
        'user_growth': list(reversed(user_growth)),
        'booking_trends': list(reversed(booking_trends)),
        'revenue_trends': list(reversed(revenue_trends))
    })


@staff_member_required
def update_user_status(request):
    """Update user verification or activation status"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(id=user_id)
            
            if action == 'verify':
                user.is_verified = True
                user.save()
                messages.success(request, f'User {user.get_full_name()} has been verified.')
            
            elif action == 'unverify':
                user.is_verified = False
                user.save()
                messages.success(request, f'User {user.get_full_name()} verification has been removed.')
            
            elif action == 'activate':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.get_full_name()} has been activated.')
            
            elif action == 'deactivate':
                user.is_active = False
                user.save()
                messages.warning(request, f'User {user.get_full_name()} has been deactivated.')
            
            return JsonResponse({'success': True})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@staff_member_required
def update_vendor_status(request):
    """Update vendor approval status"""
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor_id')
        status = request.POST.get('status')
        
        try:
            vendor = VendorProfile.objects.get(id=vendor_id)
            vendor.status = status
            vendor.save()
            
            action_messages = {
                'active': f'Vendor {vendor.business_name} has been approved.',
                'pending': f'Vendor {vendor.business_name} status set to pending.',
                'suspended': f'Vendor {vendor.business_name} has been suspended.',
                'rejected': f'Vendor {vendor.business_name} has been rejected.'
            }
            
            messages.success(request, action_messages.get(status, 'Vendor status updated.'))
            return JsonResponse({'success': True})
            
        except VendorProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Vendor not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})