from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Import your models (adjust imports based on your actual models)
from services.models import Service, ServiceCategory
from bookings.models import Booking
from accounts.models import User
from django.contrib.auth.models import User as AuthUser


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access admin views"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this area.")
        return redirect('core:home')


@login_required
@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard view"""
    
    # Get current date and time ranges
    now = timezone.now()
    today = now.date()
    month_start = today.replace(day=1)
    last_month = (month_start - timedelta(days=1)).replace(day=1)
    
    # Calculate key metrics
    try:
        # Client metrics
        total_clients = AuthUser.objects.filter(is_staff=False).count()
        new_clients_this_month = AuthUser.objects.filter(
            date_joined__gte=month_start,
            is_staff=False
        ).count()
        
        # Booking metrics
        todays_bookings = Booking.objects.filter(scheduled_date=today).count() if hasattr(Booking, 'scheduled_date') else 0
        pending_today = Booking.objects.filter(
            scheduled_date=today,
            status='PENDING'
        ).count() if hasattr(Booking, 'status') else 0
        
        # Revenue metrics (placeholder - adjust based on your models)
        monthly_revenue = 0
        revenue_growth = 0
        
        # Service metrics
        active_services = Service.objects.filter(is_active=True).count() if hasattr(Service, 'is_active') else Service.objects.count()
        featured_services = Service.objects.filter(is_featured=True).count() if hasattr(Service, 'is_featured') else 0
        
        # Recent activity (placeholder - implement based on your activity tracking)
        recent_activities = []
        
        # Today's schedule
        todays_schedule = []
        if hasattr(Booking, 'scheduled_date'):
            todays_schedule = Booking.objects.filter(
                scheduled_date=today
            ).order_by('scheduled_time')[:5] if hasattr(Booking, 'scheduled_time') else []
        
        # Pending approvals
        pending_approvals = Booking.objects.filter(status='PENDING').count() if hasattr(Booking, 'status') else 0
        
        # Top service
        top_service = None
        
        # Satisfaction metrics
        satisfaction_rate = 85  # Placeholder
        average_rating = 4.2    # Placeholder
        total_reviews = 0       # Placeholder
        
        # System status
        last_backup_time = now - timedelta(hours=6)  # Placeholder
        system_uptime = "99.9%"  # Placeholder
        
        # Notifications
        notifications = []
        
    except Exception as e:
        # Handle any database errors gracefully
        print(f"Dashboard error: {e}")
        # Set default values
        total_clients = new_clients_this_month = todays_bookings = pending_today = 0
        monthly_revenue = revenue_growth = active_services = featured_services = 0
        recent_activities = todays_schedule = []
        pending_approvals = satisfaction_rate = 0
        top_service = None
        average_rating = total_reviews = 0
        last_backup_time = now
        system_uptime = "99.9%"
        notifications = []
    
    context = {
        # Key metrics
        'total_clients': total_clients,
        'new_clients_this_month': new_clients_this_month,
        'todays_bookings': todays_bookings,
        'pending_today': pending_today,
        'monthly_revenue': monthly_revenue,
        'revenue_growth': revenue_growth,
        'active_services': active_services,
        'featured_services': featured_services,
        
        # Activity and schedule
        'recent_activities': recent_activities,
        'todays_schedule': todays_schedule,
        'pending_approvals': pending_approvals,
        
        # Performance metrics
        'top_service': top_service,
        'satisfaction_rate': satisfaction_rate,
        'average_rating': average_rating,
        'total_reviews': total_reviews,
        
        # System info
        'last_backup_time': last_backup_time,
        'system_uptime': system_uptime,
        'notifications': notifications,
    }
    
    return render(request, 'admin/dashboard.html', context)


class AdminServiceListView(AdminRequiredMixin, ListView):
    """Admin view for listing all services with advanced filtering"""
    
    model = Service
    template_name = 'admin/services_list.html'
    context_object_name = 'services'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Service.objects.all()
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        category = self.request.GET.get('category')
        if category and hasattr(Service, 'category'):
            queryset = queryset.filter(category=category)
        
        status = self.request.GET.get('status')
        if status == 'active' and hasattr(Service, 'is_active'):
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive' and hasattr(Service, 'is_active'):
            queryset = queryset.filter(is_active=False)
        elif status == 'featured' and hasattr(Service, 'is_featured'):
            queryset = queryset.filter(is_featured=True)
        
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        context.update({
            'total_services': Service.objects.count(),
            'active_services': Service.objects.filter(is_active=True).count() if hasattr(Service, 'is_active') else Service.objects.count(),
            'new_this_month': Service.objects.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count() if hasattr(Service, 'created_at') else 0,
            'active_percentage': round((context.get('active_services', 0) / max(context.get('total_services', 1), 1)) * 100),
            'avg_rating': 4.2,  # Placeholder
            'total_reviews': 0,  # Placeholder
            'monthly_bookings': 0,  # Placeholder
            'booking_growth': 0,  # Placeholder
        })
        
        return context


class AdminServiceDetailView(AdminRequiredMixin, DetailView):
    """Admin view for service details with analytics"""
    
    model = Service
    template_name = 'admin/services_detail.html'
    context_object_name = 'service'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        
        # Add service analytics
        context.update({
            'total_bookings': 0,  # Placeholder
            'monthly_bookings': 0,  # Placeholder
            'average_rating': 4.2,  # Placeholder
            'review_count': 0,  # Placeholder
            'view_count': 0,  # Placeholder
            'weekly_views': 0,  # Placeholder
            'recent_bookings': [],  # Placeholder
            'recent_reviews': [],  # Placeholder
            'last_booking': None,  # Placeholder
            'last_review': None,  # Placeholder
            'booking_rate': 75,  # Placeholder
            'satisfaction_rate': 85,  # Placeholder
            'revenue_percentage': 25,  # Placeholder
        })
        
        return context


class AdminServiceCreateView(AdminRequiredMixin, CreateView):
    """Admin view for creating new services"""
    
    model = Service
    template_name = 'admin/services_form.html'
    fields = ['name', 'description', 'category', 'price', 'duration', 'is_active', 'is_featured']
    
    def get_fields(self):
        # Dynamically get fields based on model
        return [field.name for field in self.model._meta.fields if field.name not in ['id', 'created_at', 'updated_at']]
    
    def get_success_url(self):
        messages.success(self.request, f'Service "{self.object.name}" created successfully!')
        return reverse_lazy('services:admin_service_detail', kwargs={'pk': self.object.pk})


class AdminServiceUpdateView(AdminRequiredMixin, UpdateView):
    """Admin view for editing services"""
    
    model = Service
    template_name = 'admin/services_form.html'
    fields = ['name', 'description', 'category', 'price', 'duration', 'is_active', 'is_featured']
    
    def get_fields(self):
        # Dynamically get fields based on model
        return [field.name for field in self.model._meta.fields if field.name not in ['id', 'created_at', 'updated_at']]
    
    def get_success_url(self):
        messages.success(self.request, f'Service "{self.object.name}" updated successfully!')
        return reverse_lazy('services:admin_service_detail', kwargs={'pk': self.object.pk})


class AdminBookingListView(AdminRequiredMixin, ListView):
    """Admin view for listing all bookings"""
    
    model = Booking
    template_name = 'admin/bookings_list.html'
    context_object_name = 'bookings'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Booking.objects.all()
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search) |
                Q(service__name__icontains=search)
            ) if hasattr(Booking, 'client') and hasattr(Booking, 'service') else queryset
        
        status = self.request.GET.get('status')
        if status and hasattr(Booking, 'status'):
            queryset = queryset.filter(status=status)
        
        date_filter = self.request.GET.get('date')
        if date_filter == 'today' and hasattr(Booking, 'scheduled_date'):
            queryset = queryset.filter(scheduled_date=timezone.now().date())
        elif date_filter == 'week' and hasattr(Booking, 'scheduled_date'):
            week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
            queryset = queryset.filter(scheduled_date__gte=week_start)
        elif date_filter == 'month' and hasattr(Booking, 'scheduled_date'):
            month_start = timezone.now().date().replace(day=1)
            queryset = queryset.filter(scheduled_date__gte=month_start)
        
        return queryset.order_by('-id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add booking statistics
        today = timezone.now().date()
        
        context.update({
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='PENDING').count() if hasattr(Booking, 'status') else 0,
            'confirmed_bookings': Booking.objects.filter(status='CONFIRMED').count() if hasattr(Booking, 'status') else 0,
            'new_today': Booking.objects.filter(created_at__date=today).count() if hasattr(Booking, 'created_at') else 0,
            'upcoming_today': Booking.objects.filter(
                scheduled_date=today,
                status='CONFIRMED'
            ).count() if hasattr(Booking, 'scheduled_date') and hasattr(Booking, 'status') else 0,
            'monthly_revenue': 0,  # Placeholder
            'revenue_growth': 0,  # Placeholder
            'todays_bookings': [],  # Placeholder
        })
        
        return context


@login_required
@staff_member_required
def admin_dashboard_refresh(request):
    """AJAX endpoint to refresh dashboard data"""
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get fresh data
        today = timezone.now().date()
        
        data = {
            'total_clients': AuthUser.objects.filter(is_staff=False).count(),
            'todays_bookings': Booking.objects.filter(scheduled_date=today).count() if hasattr(Booking, 'scheduled_date') else 0,
            'active_services': Service.objects.filter(is_active=True).count() if hasattr(Service, 'is_active') else Service.objects.count(),
            'pending_approvals': Booking.objects.filter(status='PENDING').count() if hasattr(Booking, 'status') else 0,
            'timestamp': timezone.now().isoformat(),
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@staff_member_required
def export_services(request):
    """Export services data in various formats"""
    
    format_type = request.GET.get('format', 'csv')
    
    # Get filtered services
    services = Service.objects.all()
    
    search = request.GET.get('search')
    if search:
        services = services.filter(name__icontains=search)
    
    # Generate export data
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="services.csv"'
        
        # CSV generation logic here
        response.write('Service Name,Category,Price,Status\n')
        for service in services:
            response.write(f'"{service.name}","Category","Price","Active"\n')
        
        return response
    
    elif format_type == 'excel':
        # Excel generation would go here
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="services.xlsx"'
        return response
    
    elif format_type == 'pdf':
        # PDF generation would go here
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="services.pdf"'
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)


@login_required
@staff_member_required
def export_bookings(request):
    """Export bookings data in various formats"""
    
    format_type = request.GET.get('format', 'csv')
    
    # Get filtered bookings
    bookings = Booking.objects.all()
    
    # Generate export data (placeholder)
    if format_type in ['csv', 'excel', 'pdf']:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bookings.{format_type}"'
        
        response.write('Booking ID,Client,Service,Date,Status\n')
        for booking in bookings[:100]:  # Limit for demo
            response.write(f'"{booking.id}","Client","Service","Date","Status"\n')
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)