from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, UpdateView, CreateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import VendorProfile, VendorDocument, VendorAvailability, VendorBlackoutDate, VendorPayment, VendorAnalytics
from bookings.models import Booking
from services.models import Service, ServiceReview
from .forms import VendorProfileForm, VendorDocumentForm, VendorAvailabilityForm


class VendorMixin:
    """Mixin to ensure only vendors can access vendor views"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Check if user is a vendor type
        if request.user.user_type not in ['ACCOMMODATION', 'CARETAKER', 'WELLNESS', 'MEDITATION', 'MENTAL_HEALTH', 'FOOD']:
            messages.error(request, 'You need vendor access to view this page.')
            return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)


@login_required
def vendor_dashboard(request):
    """Main vendor dashboard with overview statistics"""
    
    # Get or create vendor profile
    vendor_profile, created = VendorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'business_name': f"{request.user.get_full_name()}'s Services",
            'business_email': request.user.email,
            'business_phone': request.user.phone or '',
            'business_type': 'individual',
            'service_areas': 'Qatar',
        }
    )
    
    # Get recent bookings for this vendor's services
    vendor_services = Service.objects.filter(
        Q(description__icontains=vendor_profile.business_name) |
        Q(name__icontains=vendor_profile.business_name.split()[0])  # Match first word of business name
    )
    
    # Base queryset for all vendor bookings
    all_vendor_bookings = Booking.objects.filter(service__in=vendor_services)
    
    # Calculate statistics from the base queryset
    total_bookings = all_vendor_bookings.count()
    pending_bookings = all_vendor_bookings.filter(status='pending').count()
    completed_bookings = all_vendor_bookings.filter(status='completed').count()
    
    # Calculate revenue (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_revenue = all_vendor_bookings.filter(
        status='completed',
        created_at__date__gte=thirty_days_ago
    ).aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    
    # Get average rating
    avg_rating = ServiceReview.objects.filter(
        service__in=vendor_services
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Get recent bookings (limited for display)
    recent_bookings = all_vendor_bookings.order_by('-created_at')[:5]
    
    # Upcoming bookings
    upcoming_bookings = all_vendor_bookings.filter(
        status__in=['confirmed', 'pending'],
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]
    
    context = {
        'vendor_profile': vendor_profile,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'completed_bookings': completed_bookings,
        'recent_revenue': recent_revenue,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
        'vendor_services': vendor_services,
    }
    
    return render(request, 'vendors/dashboard.html', context)


class VendorProfileDetailView(VendorMixin, DetailView):
    """View vendor profile details"""
    model = VendorProfile
    template_name = 'vendors/profile_detail.html'
    context_object_name = 'vendor_profile'
    
    def get_object(self):
        profile, created = VendorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'business_name': f"{self.request.user.get_full_name()}'s Services",
                'business_email': self.request.user.email,
                'business_phone': self.request.user.phone or '',
                'business_type': 'individual',
                'service_areas': 'Qatar',
            }
        )
        return profile


class VendorProfileUpdateView(VendorMixin, UpdateView):
    """Update vendor profile"""
    model = VendorProfile
    form_class = VendorProfileForm
    template_name = 'vendors/profile_update.html'
    
    def get_object(self):
        profile, created = VendorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'business_name': f"{self.request.user.get_full_name()}'s Services",
                'business_email': self.request.user.email,
                'business_phone': self.request.user.phone or '',
                'business_type': 'individual',
                'service_areas': 'Qatar',
            }
        )
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


@login_required
def vendor_bookings(request):
    """List all bookings for vendor's services"""
    
    # Get vendor's services
    vendor_services = Service.objects.filter(
        Q(name__icontains=request.user.get_full_name()) |
        Q(description__icontains=request.user.get_full_name())
    )
    
    bookings = Booking.objects.filter(
        service__in=vendor_services
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'vendor_services': vendor_services,
    }
    
    return render(request, 'vendors/bookings.html', context)


@login_required
def vendor_booking_detail(request, booking_id):
    """View detailed booking information"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if this booking belongs to vendor's services
    vendor_services = Service.objects.filter(
        Q(name__icontains=request.user.get_full_name()) |
        Q(description__icontains=request.user.get_full_name())
    )
    
    if booking.service not in vendor_services:
        messages.error(request, 'You do not have access to this booking.')
        return redirect('vendors:bookings')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'vendors/booking_detail.html', context)


@login_required
def vendor_services(request):
    """Manage vendor's services"""
    
    # Get vendor's services
    vendor_services = Service.objects.filter(
        Q(name__icontains=request.user.get_full_name()) |
        Q(description__icontains=request.user.get_full_name())
    )
    
    context = {
        'services': vendor_services,
    }
    
    return render(request, 'vendors/services.html', context)


@login_required
def vendor_analytics(request):
    """Show vendor analytics and performance metrics"""
    
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get vendor's services
    vendor_services = Service.objects.filter(
        Q(name__icontains=request.user.get_full_name()) |
        Q(description__icontains=request.user.get_full_name())
    )
    
    bookings = Booking.objects.filter(
        service__in=vendor_services,
        created_at__date__gte=start_date
    )
    
    # Calculate metrics
    total_bookings = bookings.count()
    completed_bookings = bookings.filter(status='completed').count()
    cancelled_bookings = bookings.filter(status='cancelled').count()
    pending_bookings = bookings.filter(status='pending').count()
    
    # Revenue calculations
    total_revenue = bookings.filter(status='completed').aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0')
    
    # Completion rate
    completion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
    
    # Average rating
    avg_rating = ServiceReview.objects.filter(
        service__in=vendor_services
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Daily booking data for chart
    daily_data = []
    current_date = start_date
    while current_date <= end_date:
        daily_bookings = bookings.filter(created_at__date=current_date).count()
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'bookings': daily_bookings
        })
        current_date += timedelta(days=1)
    
    context = {
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'pending_bookings': pending_bookings,
        'total_revenue': total_revenue,
        'completion_rate': round(completion_rate, 1),
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'daily_data': daily_data,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'vendors/analytics.html', context)


@login_required
def vendor_availability(request):
    """Manage vendor availability schedule"""
    
    vendor_profile, created = VendorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'business_name': f"{request.user.get_full_name()}'s Services",
            'business_email': request.user.email,
            'business_phone': request.user.phone or '',
            'business_type': 'individual',
            'service_areas': 'Qatar',
        }
    )
    
    availability_schedule = VendorAvailability.objects.filter(vendor=vendor_profile)
    blackout_dates = VendorBlackoutDate.objects.filter(vendor=vendor_profile)
    
    context = {
        'vendor_profile': vendor_profile,
        'availability_schedule': availability_schedule,
        'blackout_dates': blackout_dates,
    }
    
    return render(request, 'vendors/availability.html', context)


@login_required
def vendor_documents(request):
    """Manage vendor documents and verification"""
    
    vendor_profile, created = VendorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'business_name': f"{request.user.get_full_name()}'s Services",
            'business_email': request.user.email,
            'business_phone': request.user.phone or '',
            'business_type': 'individual',
            'service_areas': 'Qatar',
        }
    )
    
    documents = VendorDocument.objects.filter(vendor=vendor_profile)
    
    if request.method == 'POST':
        form = VendorDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.vendor = vendor_profile
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('vendors:documents')
    else:
        form = VendorDocumentForm()
    
    context = {
        'vendor_profile': vendor_profile,
        'documents': documents,
        'form': form,
    }
    
    return render(request, 'vendors/documents.html', context)


@login_required
def vendor_payments(request):
    """View vendor payment history"""
    
    vendor_profile, created = VendorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'business_name': f"{request.user.get_full_name()}'s Services",
            'business_email': request.user.email,
            'business_phone': request.user.phone or '',
            'business_type': 'individual',
            'service_areas': 'Qatar',
        }
    )
    
    payments = VendorPayment.objects.filter(vendor=vendor_profile).order_by('-created_date')
    
    # Calculate totals
    total_earnings = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    pending_payments = payments.filter(status='pending').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    context = {
        'vendor_profile': vendor_profile,
        'payments': payments,
        'total_earnings': total_earnings,
        'pending_payments': pending_payments,
    }
    
    return render(request, 'vendors/payments.html', context)


@login_required
def update_booking_status(request, booking_id):
    """Update booking status (AJAX endpoint)"""
    
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        new_status = request.POST.get('status')
        
        # Check if this booking belongs to vendor's services
        vendor_services = Service.objects.filter(
            Q(name__icontains=request.user.get_full_name()) |
            Q(description__icontains=request.user.get_full_name())
        )
        
        if booking.service in vendor_services and new_status in dict(Booking.STATUS_CHOICES):
            old_status = booking.status
            booking.status = new_status
            booking.save()
            
            # Create status history entry
            from bookings.models import BookingStatusHistory
            BookingStatusHistory.objects.create(
                booking=booking,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                notes=f'Status updated by vendor to {new_status}'
            )
            
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
