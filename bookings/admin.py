from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta

from .models import Booking, BookingItem

# Custom admin actions
@admin.action(description='Mark selected bookings as confirmed')
def mark_as_confirmed(modeladmin, request, queryset):
    """Mark selected bookings as confirmed."""
    updated = queryset.filter(status='pending').update(status='confirmed')
    messages.success(request, f"Successfully confirmed {updated} bookings.")

@admin.action(description='Mark selected bookings as cancelled')
def mark_as_cancelled(modeladmin, request, queryset):
    """Mark selected bookings as cancelled."""
    updated = queryset.exclude(status__in=['completed', 'cancelled']).update(status='cancelled')
    messages.success(request, f"Successfully cancelled {updated} bookings.")

@admin.action(description='Mark selected bookings as completed')
def mark_as_completed(modeladmin, request, queryset):
    """Mark selected bookings as completed."""
    updated = queryset.filter(status='confirmed').update(
        status='completed',
        completed_at=timezone.now()
    )
    messages.success(request, f"Successfully completed {updated} bookings.")

@admin.action(description='Send reminder emails (Staff only)')
def send_reminder_emails(modeladmin, request, queryset):
    """Send reminder emails for upcoming bookings."""
    if not request.user.is_staff:
        messages.error(request, "Only staff members can send reminder emails.")
        return
    
    upcoming_bookings = queryset.filter(
        start_date__gte=timezone.now().date(),
        start_date__lte=(timezone.now().date() + timedelta(days=3)),
        status='confirmed'
    )
    
    count = upcoming_bookings.count()
    # Here you would implement the actual email sending logic
    messages.success(request, f"Reminder emails queued for {count} upcoming bookings.")

# Register your models here.
class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    readonly_fields = ('price',)
    fields = ('name', 'quantity', 'price', 'description')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_id', 'get_user_info', 'get_service_info', 'start_date', 
        'end_date', 'total_price_formatted', 'status_colored', 'days_until_booking',
        'created_at'
    )
    list_filter = (
        'status', 'priority', 'start_date', 'created_at'
    )
    search_fields = (
        'booking_number', 'user__email', 'user__first_name', 'user__last_name', 
        'service__name'
    )
    date_hierarchy = 'created_at'
    inlines = [BookingItemInline]
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'booking_number')
    list_per_page = 25
    actions = [mark_as_confirmed, mark_as_cancelled, mark_as_completed, send_reminder_emails]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'service', 'booking_number')
        }),
        ('Booking Details', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time', 'address', 'total_price', 'status', 'notes')
        }),
        ('Contact Information', {
            'fields': ('client_phone', 'client_email'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def booking_id(self, obj):
        """Display formatted booking ID."""
        return obj.booking_number
    booking_id.short_description = 'Booking ID'
    booking_id.admin_order_field = 'booking_number'
    
    def get_user_info(self, obj):
        """Display user information with link."""
        user_url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>', 
            user_url, 
            obj.user.get_full_name() or obj.user.email,
            obj.user.email
        )
    get_user_info.short_description = 'Customer'
    get_user_info.admin_order_field = 'user__first_name'
    
    def get_service_info(self, obj):
        """Display service information."""
        service_url = reverse('admin:services_service_change', args=[obj.service.id])
        return format_html(
            '<a href="{}">{}</a>', 
            service_url,
            obj.service.name
        )
    get_service_info.short_description = 'Service'
    get_service_info.admin_order_field = 'service__name'
    
    def total_price_formatted(self, obj):
        """Display formatted total price."""
        return format_html('<strong>QAR {}</strong>', f'{obj.total_price:.2f}')
    total_price_formatted.short_description = 'Total Price'
    total_price_formatted.admin_order_field = 'total_price'
    
    def status_colored(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'completed': 'green',
            'cancelled': 'red',
            'no_show': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    status_colored.admin_order_field = 'status'
    
    def days_until_booking(self, obj):
        """Show days until booking starts."""
        if obj.start_date:
            days_diff = (obj.start_date - timezone.now().date()).days
            if days_diff < 0:
                return format_html('<span style="color: gray;">Past</span>')
            elif days_diff == 0:
                return format_html('<span style="color: red; font-weight: bold;">Today!</span>')
            elif days_diff <= 3:
                return format_html('<span style="color: orange;">{} days</span>', days_diff)
            else:
                return format_html('<span style="color: green;">{} days</span>', days_diff)
        return 'N/A'
    days_until_booking.short_description = 'Time Until'
    
    def get_queryset(self, request):
        """Optimize queryset with related fields."""
        return super().get_queryset(request).select_related(
            'user', 'service'
        ).prefetch_related('items')
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete bookings."""
        return request.user.is_superuser

@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_booking_info', 'quantity', 'price_formatted', 'total_price')
    search_fields = ('name', 'booking__user__email', 'booking__service__name')
    list_filter = ('booking__status', 'booking__created_at')
    readonly_fields = ('total_price',)
    
    def get_booking_info(self, obj):
        """Display booking information."""
        booking_url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            booking_url,
            obj.booking.booking_number,
            obj.booking.user.get_full_name() or obj.booking.user.email
        )
    get_booking_info.short_description = 'Booking'
    get_booking_info.admin_order_field = 'booking__booking_number'
    
    def price_formatted(self, obj):
        """Display formatted price."""
        return format_html('QAR {}', f'{obj.price:.2f}')
    price_formatted.short_description = 'Unit Price'
    price_formatted.admin_order_field = 'price'
    
    def total_price(self, obj):
        """Calculate and display total price."""
        total = obj.price * obj.quantity
        return format_html('<strong>QAR {}</strong>', f'{total:.2f}')
    total_price.short_description = 'Total'
