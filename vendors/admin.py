from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    VendorProfile, VendorDocument, VendorAvailability, 
    VendorBlackoutDate, VendorPayment, VendorAnalytics
)
import csv
from django.http import HttpResponse


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'user', 'status', 'verified', 'average_rating', 
        'total_bookings', 'completion_rate_display', 'joined_date'
    ]
    list_filter = ['status', 'verified', 'business_type', 'joined_date']
    search_fields = ['business_name', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['joined_date', 'last_active', 'total_bookings', 'completed_bookings', 'average_rating']
    
    fieldsets = (
        (_('User Account'), {
            'fields': ('user',)
        }),
        (_('Business Information'), {
            'fields': ('business_name', 'business_type', 'business_license', 'tax_id')
        }),
        (_('Contact Information'), {
            'fields': ('business_phone', 'business_email', 'website', 'service_areas')
        }),
        (_('Status & Verification'), {
            'fields': ('status', 'verified', 'verification_date')
        }),
        (_('Performance Metrics'), {
            'fields': ('average_rating', 'total_reviews', 'total_bookings', 'completed_bookings')
        }),
        (_('Financial'), {
            'fields': ('commission_rate', 'total_earnings')
        }),
        (_('Settings'), {
            'fields': ('auto_accept_bookings', 'notification_email', 'notification_sms')
        }),
        (_('Timestamps'), {
            'fields': ('joined_date', 'last_active')
        }),
    )
    
    def completion_rate_display(self, obj):
        """Display completion rate with color coding"""
        rate = obj.get_completion_rate()
        if rate >= 90:
            color = 'green'
        elif rate >= 75:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    completion_rate_display.short_description = _('Completion Rate')
    
    actions = ['verify_vendors', 'activate_vendors', 'suspend_vendors']

    def verify_vendors(self, request, queryset):
        """Bulk verify vendors"""
        updated = queryset.update(verified=True, verification_date=timezone.now())
        self.message_user(request, f'{updated} vendors verified successfully.')
    verify_vendors.short_description = _('Verify selected vendors')

    def activate_vendors(self, request, queryset):
        """Bulk activate vendors"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} vendors activated successfully.')
    activate_vendors.short_description = _('Activate selected vendors')

    def suspend_vendors(self, request, queryset):
        """Bulk suspend vendors"""
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} vendors suspended successfully.')
    suspend_vendors.short_description = _('Suspend selected vendors')


def _export_vendors_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendors_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Business Name', 'User', 'Status', 'Verified', 'Average Rating', 'Total Bookings', 'Joined Date'])

    for v in queryset.select_related('user'):
        writer.writerow([
            v.business_name,
            v.user.get_full_name() or v.user.email,
            v.status,
            'Yes' if v.verified else 'No',
            f'{v.average_rating:.2f}',
            v.total_bookings,
            v.joined_date,
        ])

    return response


def notify_vendors_stub(modeladmin, request, queryset):
    """Stub action to notify selected vendors (e.g., email/SMS)"""
    # In production, integrate with the notification system; here we just show a message
    count = queryset.count()
    modeladmin.message_user(request, f'Notification queued for {count} vendors (stub).')
notify_vendors_stub.short_description = _('Notify selected vendors (stub)')


def export_vendors_csv(modeladmin, request, queryset):
    return _export_vendors_csv(queryset)
export_vendors_csv.short_description = _('Export selected vendors to CSV')


@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'document_type', 'title', 'status', 'uploaded_date', 'is_expired_display']
    list_filter = ['document_type', 'status', 'uploaded_date']
    search_fields = ['vendor__business_name', 'title', 'vendor__user__email']
    readonly_fields = ['uploaded_date']
    
    fieldsets = (
        (_('Document Information'), {
            'fields': ('vendor', 'document_type', 'title', 'document_file', 'description')
        }),
        (_('Verification'), {
            'fields': ('status', 'verified_date', 'verified_by', 'notes')
        }),
        (_('Dates'), {
            'fields': ('uploaded_date', 'expiry_date')
        }),
    )
    
    def is_expired_display(self, obj):
        """Display expiry status with color coding"""
        if obj.expiry_date:
            if obj.is_expired():
                return format_html('<span style="color: red;">Expired</span>')
            elif obj.expiry_date <= timezone.now().date() + timezone.timedelta(days=30):
                return format_html('<span style="color: orange;">Expiring Soon</span>')
            else:
                return format_html('<span style="color: green;">Valid</span>')
        return '-'
    is_expired_display.short_description = _('Expiry Status')
    
    actions = ['approve_documents', 'reject_documents']
    
    def approve_documents(self, request, queryset):
        """Bulk approve documents"""
        updated = queryset.update(status='approved', verified_date=timezone.now(), verified_by=request.user)
        self.message_user(request, f'{updated} documents approved successfully.')
    approve_documents.short_description = _('Approve selected documents')
    
    def reject_documents(self, request, queryset):
        """Bulk reject documents"""
        updated = queryset.update(status='rejected', verified_date=timezone.now(), verified_by=request.user)
        self.message_user(request, f'{updated} documents rejected successfully.')
    reject_documents.short_description = _('Reject selected documents')


class VendorAvailabilityInline(admin.TabularInline):
    model = VendorAvailability
    extra = 7  # One for each day of the week


class VendorBlackoutDateInline(admin.TabularInline):
    model = VendorBlackoutDate
    extra = 1


@admin.register(VendorAvailability)
class VendorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    search_fields = ['vendor__business_name']


@admin.register(VendorBlackoutDate)
class VendorBlackoutDateAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'start_date', 'end_date', 'reason']
    list_filter = ['start_date', 'end_date']
    search_fields = ['vendor__business_name', 'reason']


@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'payment_type', 'amount', 'currency', 
        'status', 'period_start', 'period_end', 'payment_date'
    ]
    list_filter = ['payment_type', 'status', 'currency', 'payment_date']
    search_fields = ['vendor__business_name', 'reference_number']
    readonly_fields = ['created_date']
    
    fieldsets = (
        (_('Payment Information'), {
            'fields': ('vendor', 'payment_type', 'amount', 'currency')
        }),
        (_('Period'), {
            'fields': ('period_start', 'period_end')
        }),
        (_('Booking Details'), {
            'fields': ('booking_count', 'gross_amount', 'commission_rate')
        }),
        (_('Status'), {
            'fields': ('status', 'payment_date', 'reference_number')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_date',)
        }),
    )


@admin.register(VendorAnalytics)
class VendorAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'date', 'bookings_received', 'bookings_completed', 
        'revenue', 'average_rating'
    ]
    list_filter = ['date', 'vendor']
    search_fields = ['vendor__business_name']
    date_hierarchy = 'date'
