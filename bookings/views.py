from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from datetime import datetime, timedelta

from .models import Booking, BookingItem, BookingStatusHistory, BookingPayment
from .forms import (BookingForm, BookingItemForm, QuickBookingForm, 
                   BookingStatusForm, BookingPaymentForm, BookingSearchForm)

# Create your views here.

class BookingListView(LoginRequiredMixin, ListView):
    """
    Enhanced view for listing all bookings for the current user
    """
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Return bookings for the current user with search and filter
        """
        queryset = Booking.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Apply search and filters
        form = BookingSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            priority = form.cleaned_data.get('priority')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            
            if search:
                queryset = queryset.filter(
                    Q(booking_number__icontains=search) |
                    Q(service__name__icontains=search) |
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
                
            if priority:
                queryset = queryset.filter(priority=priority)
                
            if start_date:
                queryset = queryset.filter(start_date__gte=start_date)
                
            if end_date:
                queryset = queryset.filter(start_date__lte=end_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get booking statistics
        user_bookings = Booking.objects.filter(user=self.request.user)
        context['stats'] = {
            'total_count': user_bookings.count(),
            'pending_count': user_bookings.filter(status='pending').count(),
            'confirmed_count': user_bookings.filter(status='confirmed').count(),
            'completed_count': user_bookings.filter(status='completed').count(),
            'cancelled_count': user_bookings.filter(status='cancelled').count(),
            'in_progress_count': user_bookings.filter(status='in_progress').count(),
        }
        
        # Add search form
        context['search_form'] = BookingSearchForm(self.request.GET)
        
        # Recent bookings for quick access
        context['recent_bookings'] = user_bookings.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )[:5]
        
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    """
    Enhanced view for displaying booking details
    """
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        """
        Ensure users can only view their own bookings
        """
        return Booking.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add booking items
        context['booking_items'] = self.object.items.all()
        context['items_total'] = sum(item.get_total() for item in context['booking_items'])
        
        # Add status history
        context['status_history'] = self.object.status_history.all()[:10]
        
        # Add payment information
        context['payments'] = self.object.payments.all()
        context['total_paid'] = self.object.payments.filter(
            payment_status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Add forms for admin actions (if user has permissions)
        if self.request.user.is_staff:
            context['status_form'] = BookingStatusForm(instance=self.object)
            context['payment_form'] = BookingPaymentForm()
        
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):
    """
    Enhanced view for creating a new booking
    """
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_create.html'
    
    def get_initial(self):
        """
        Pre-fill form with service details if provided
        """
        initial = super().get_initial()
        service_id = self.kwargs.get('service_id')
        if service_id:
            from services.models import Service
            service = get_object_or_404(Service, pk=service_id)
            initial.update({
                'service': service,
                'start_date': timezone.now().date() + timedelta(days=1),
                'client_email': self.request.user.email,
            })
            
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Set the user and initialize booking
        """
        form.instance.user = self.request.user
        form.instance.status = 'draft'
        
        # Set base price from service
        if form.instance.service:
            form.instance.base_price = form.instance.service.price
            
        response = super().form_valid(form)
        
        # Create status history
        BookingStatusHistory.objects.create(
            booking=self.object,
            new_status='draft',
            changed_by=self.request.user,
            notes='Booking created'
        )
        
        messages.success(self.request, _('Booking created successfully! Review your details and submit when ready.'))
        return response
    
    def get_success_url(self):
        """
        Redirect to booking detail after successful creation
        """
        return reverse('bookings:booking_detail', kwargs={'pk': self.object.pk})


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Enhanced view for updating an existing booking
    """
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_update.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        """
        Ensure users can only update their own modifiable bookings
        """
        return Booking.objects.filter(
            user=self.request.user, 
            status__in=['draft', 'pending']
        )
    
    def form_valid(self, form):
        old_status = self.object.status
        response = super().form_valid(form)
        
        # Create status history if status changed
        if old_status != self.object.status:
            BookingStatusHistory.objects.create(
                booking=self.object,
                old_status=old_status,
                new_status=self.object.status,
                changed_by=self.request.user,
                notes='Booking updated'
            )
        
        messages.success(self.request, _('Booking updated successfully!'))
        return response


class BookingCancelView(LoginRequiredMixin, UpdateView):
    """
    Enhanced view for cancelling a booking
    """
    model = Booking
    template_name = 'bookings/booking_cancel.html'
    fields = ['notes']
    
    def get_queryset(self):
        """
        Ensure users can only cancel their own cancellable bookings
        """
        return Booking.objects.filter(
            user=self.request.user
        ).filter(
            Q(status__in=['draft', 'pending', 'confirmed']) &
            Q(start_date__gt=timezone.now().date())
        )
    
    def form_valid(self, form):
        """
        Set the status to cancelled and create history
        """
        old_status = form.instance.status
        form.instance.status = 'cancelled'
        
        response = super().form_valid(form)
        
        # Create status history
        BookingStatusHistory.objects.create(
            booking=self.object,
            old_status=old_status,
            new_status='cancelled',
            changed_by=self.request.user,
            notes=form.cleaned_data.get('notes', 'Booking cancelled by client')
        )
        
        # Send cancellation email
        self.object.send_status_update_email()
        
        messages.success(self.request, _('Booking cancelled successfully.'))
        return response
    
    def get_success_url(self):
        return reverse('bookings:booking_detail', kwargs={'pk': self.object.pk})


@login_required
def submit_booking(request, booking_id):
    """
    Submit a draft booking for processing
    """
    booking = get_object_or_404(
        Booking, 
        pk=booking_id, 
        user=request.user, 
        status='draft'
    )
    
    if request.method == 'POST':
        # Update status to pending
        old_status = booking.status
        booking.status = 'pending'
        booking.save()
        
        # Create status history
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='pending',
            changed_by=request.user,
            notes='Booking submitted for processing'
        )
        
        # Send confirmation email
        booking.send_confirmation_email()
        
        messages.success(request, _('Booking submitted successfully! We will review and confirm shortly.'))
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    return render(request, 'bookings/booking_submit.html', {'booking': booking})


@login_required
def book_service(request, service_id):
    """
    Enhanced view for booking a specific service
    """
    from services.models import Service
    service = get_object_or_404(Service, pk=service_id)
    
    if request.method == 'POST':
        form = QuickBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.service = service
            booking.status = 'draft'
            booking.base_price = service.price
            booking.end_date = booking.start_date  # Default to same day
            booking.save()
            
            # Create status history
            BookingStatusHistory.objects.create(
                booking=booking,
                new_status='draft',
                changed_by=request.user,
                notes='Quick booking created'
            )
            
            messages.success(request, _('Service booking created! Complete your details to submit.'))
            return redirect('bookings:booking_update', pk=booking.pk)
    else:
        form = QuickBookingForm(initial={
            'service': service,
            'start_date': timezone.now().date() + timedelta(days=1),
            'start_time': timezone.now().time().replace(minute=0, second=0, microsecond=0)
        })
    
    context = {
        'form': form,
        'service': service
    }
    return render(request, 'bookings/book_service.html', context)


@require_POST
@login_required
def add_booking_item(request, booking_id):
    """
    Ajax view for adding an item to a booking
    """
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if not booking.can_be_modified():
        return JsonResponse({'success': False, 'error': 'Booking cannot be modified'})
    
    form = BookingItemForm(request.POST)
    
    if form.is_valid():
        item = form.save(commit=False)
        item.booking = booking
        item.save()
        
        # Recalculate booking total
        booking.calculate_total_price()
        booking.save()
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'price': str(item.price),
            'total': str(item.get_total()),
            'booking_total': str(booking.total_price)
        })
    
    return JsonResponse({'success': False, 'errors': form.errors})


@require_POST
@login_required
def remove_booking_item(request, booking_id, item_id):
    """
    Ajax view for removing an item from a booking
    """
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    item = get_object_or_404(BookingItem, pk=item_id, booking=booking)
    
    if not booking.can_be_modified():
        return JsonResponse({'success': False, 'error': 'Booking cannot be modified'})
    
    item.delete()
    
    # Recalculate booking total
    booking.calculate_total_price()
    booking.save()
    
    return JsonResponse({
        'success': True,
        'booking_total': str(booking.total_price)
    })


class BookingDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view showing booking overview and statistics
    """
    template_name = 'bookings/booking_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_bookings = Booking.objects.filter(user=self.request.user)
        
        # Overview statistics
        context['overview'] = {
            'total_bookings': user_bookings.count(),
            'active_bookings': user_bookings.filter(status__in=['pending', 'confirmed', 'in_progress']).count(),
            'completed_bookings': user_bookings.filter(status='completed').count(),
            'upcoming_bookings': user_bookings.filter(
                start_date__gte=timezone.now().date(),
                status__in=['confirmed', 'pending']
            ).count(),
        }
        
        # Recent activity
        context['recent_bookings'] = user_bookings.order_by('-created_at')[:5]
        
        # Upcoming bookings
        context['upcoming_bookings'] = user_bookings.filter(
            start_date__gte=timezone.now().date(),
            status__in=['confirmed', 'pending']
        ).order_by('start_date')[:5]
        
        # Monthly statistics
        current_month = timezone.now().replace(day=1)
        context['monthly_stats'] = {
            'this_month': user_bookings.filter(created_at__gte=current_month).count(),
            'completed_this_month': user_bookings.filter(
                completed_at__gte=current_month
            ).count(),
        }
        
        return context
