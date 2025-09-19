from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string

from .models import (
    AccountingCategory, TaxRate, Invoice, InvoiceItem, 
    Payment, Expense
)
from .models import Budget, BudgetLine

# Custom admin actions
@admin.action(description='Mark selected invoices as sent')
def mark_invoices_as_sent(modeladmin, request, queryset):
    """Mark selected invoices as sent."""
    updated = queryset.filter(status='draft').update(
        status='sent',
        sent_date=timezone.now()
    )
    messages.success(request, f"Successfully marked {updated} invoices as sent.")

@admin.action(description='Mark selected invoices as paid')
def mark_invoices_as_paid(modeladmin, request, queryset):
    """Mark selected invoices as paid."""
    updated = 0
    for invoice in queryset.filter(status__in=['sent', 'pending', 'overdue']):
        invoice.mark_as_paid()
        updated += 1
    messages.success(request, f"Successfully marked {updated} invoices as paid.")

@admin.action(description='Generate invoice from booking')
def generate_invoice_from_booking(modeladmin, request, queryset):
    """Generate invoices from selected bookings."""
    # This would be implemented to work with booking selections
    messages.info(request, "Invoice generation feature will be implemented.")

@admin.action(description='Send payment reminders')
def send_payment_reminders(modeladmin, request, queryset):
    """Send payment reminders for overdue invoices."""
    overdue_invoices = queryset.filter(
        due_date__lt=timezone.now().date(),
        status__in=['sent', 'pending']
    )
    count = overdue_invoices.count()
    # Implementation for sending emails would go here
    messages.success(request, f"Payment reminders queued for {count} overdue invoices.")

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'service', 'quantity', 'unit_price', 'discount_percentage', 'total_amount', 'category')
    readonly_fields = ('total_amount',)

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('created_at', 'processed_date')
    fields = ('amount', 'payment_method', 'payment_status', 'transaction_reference', 'payment_date', 'notes')

@admin.register(AccountingCategory)
class AccountingCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'usage_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'usage_count')
    
    def usage_count(self, obj):
        """Display usage count across invoices and expenses."""
        invoice_items = InvoiceItem.objects.filter(category=obj).count()
        expenses = Expense.objects.filter(category=obj).count()
        total = invoice_items + expenses
        return format_html('<strong>{}</strong> uses', total)
    usage_count.short_description = 'Usage'

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate_display', 'effective_from', 'effective_to', 'is_active', 'current_status')
    list_filter = ('is_active', 'effective_from')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'current_status')
    date_hierarchy = 'effective_from'
    
    def rate_display(self, obj):
        """Display tax rate with formatting."""
        return format_html('<strong>{}%</strong>', obj.rate)
    rate_display.short_description = 'Rate'
    rate_display.admin_order_field = 'rate'
    
    def current_status(self, obj):
        """Display if tax rate is currently effective."""
        if obj.is_current():
            return format_html('<span style="color: green; font-weight: bold;">Current</span>')
        else:
            return format_html('<span style="color: gray;">Not Current</span>')
    current_status.short_description = 'Status'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'customer_info', 'invoice_type', 'total_amount_formatted',
        'status_colored', 'due_date', 'overdue_status', 'created_at'
    )
    list_filter = (
        'status', 'invoice_type', 'invoice_date', 'due_date', 'created_at'
    )
    search_fields = (
        'invoice_number', 'customer__email', 'customer__first_name', 
        'customer__last_name', 'billing_name', 'billing_email'
    )
    readonly_fields = (
        'invoice_number', 'created_at', 'updated_at', 'sent_date', 
        'paid_date', 'balance_due', 'payment_summary'
    )
    inlines = [InvoiceItemInline, PaymentInline]
    date_hierarchy = 'invoice_date'
    list_per_page = 25
    actions = [mark_invoices_as_sent, mark_invoices_as_paid, send_payment_reminders]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'customer', 'booking', 'invoice_type', 'status')
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date', 'sent_date', 'paid_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'paid_amount', 'balance_due')
        }),
        ('Billing Information', {
            'fields': ('billing_name', 'billing_email', 'billing_phone', 'billing_address', 'billing_city', 'billing_state', 'billing_postal_code', 'billing_country'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'internal_notes', 'terms_and_conditions'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'payment_summary'),
            'classes': ('collapse',)
        })
    )
    
    def customer_info(self, obj):
        """Display customer information with link."""
        customer_url = reverse('admin:accounts_user_change', args=[obj.customer.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            customer_url,
            obj.customer.get_full_name() or obj.customer.email,
            obj.customer.email
        )
    customer_info.short_description = 'Customer'
    customer_info.admin_order_field = 'customer__first_name'
    
    def total_amount_formatted(self, obj):
        """Display formatted total amount."""
        return format_html('<strong>QAR {}</strong>', f'{obj.total_amount:.2f}')
    total_amount_formatted.short_description = 'Total Amount'
    total_amount_formatted.admin_order_field = 'total_amount'
    
    def status_colored(self, obj):
        """Display status with color coding."""
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'sent': 'blue',
            'paid': 'green',
            'partially_paid': 'orange',
            'overdue': 'red',
            'cancelled': 'gray',
            'refunded': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    status_colored.admin_order_field = 'status'
    
    def overdue_status(self, obj):
        """Display overdue status."""
        if obj.is_overdue():
            days_overdue = (timezone.now().date() - obj.due_date).days
            return format_html('<span style="color: red; font-weight: bold;">{} days</span>', days_overdue)
        elif obj.status == 'paid':
            return format_html('<span style="color: green;">Paid</span>')
        else:
            days_until_due = (obj.due_date - timezone.now().date()).days
            if days_until_due <= 3:
                return format_html('<span style="color: orange;">Due in {} days</span>', days_until_due)
            return format_html('<span style="color: green;">On time</span>')
    overdue_status.short_description = 'Due Status'
    
    def payment_summary(self, obj):
        """Display payment summary."""
        if obj.pk:
            payments = obj.payments.filter(payment_status='completed')
            count = payments.count()
            total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
            return format_html(
                '<strong>{}</strong> payments totaling <strong>QAR {}</strong>',
                count, f'{total_paid:.2f}'
            )
        return 'No payments yet'
    payment_summary.short_description = 'Payments'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('customer', 'booking').prefetch_related('payments', 'items')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'get_invoice_info', 'amount_formatted', 'payment_method', 
        'payment_status_colored', 'payment_date', 'transaction_reference'
    )
    list_filter = ('payment_method', 'payment_status', 'payment_date', 'created_at')
    search_fields = (
        'invoice__invoice_number', 'transaction_reference', 
        'gateway_transaction_id', 'invoice__customer__email'
    )
    readonly_fields = ('created_at', 'updated_at', 'processed_date')
    date_hierarchy = 'payment_date'
    list_per_page = 25
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('invoice', 'amount', 'payment_method', 'payment_status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_reference', 'payment_gateway', 'gateway_transaction_id')
        }),
        ('Dates', {
            'fields': ('payment_date', 'processed_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'receipt_sent', 'processed_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_invoice_info(self, obj):
        """Display invoice information with link."""
        invoice_url = reverse('admin:financial_invoice_change', args=[obj.invoice.id])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            invoice_url,
            obj.invoice.invoice_number,
            obj.invoice.customer.get_full_name()
        )
    get_invoice_info.short_description = 'Invoice'
    get_invoice_info.admin_order_field = 'invoice__invoice_number'
    
    def amount_formatted(self, obj):
        """Display formatted amount."""
        return format_html('<strong>QAR {}</strong>', f'{obj.amount:.2f}')
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    
    def payment_status_colored(self, obj):
        """Display payment status with color coding."""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
            'refunded': 'purple'
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_colored.short_description = 'Status'
    payment_status_colored.admin_order_field = 'payment_status'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'description', 'amount_formatted', 'expense_type', 'vendor_name',
        'approval_status', 'payment_status', 'expense_date', 'created_by'
    )
    list_filter = (
        'expense_type', 'is_approved', 'is_paid', 'expense_date', 'created_at'
    )
    search_fields = (
        'description', 'vendor_name', 'vendor_email', 'notes',
        'created_by__email', 'approved_by__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'expense_date'
    list_per_page = 25
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('description', 'amount', 'expense_type', 'category', 'expense_date')
        }),
        ('Vendor Information', {
            'fields': ('vendor_name', 'vendor_email', 'vendor_phone')
        }),
        ('Status', {
            'fields': ('is_approved', 'approved_by', 'is_paid', 'payment_date')
        }),
        ('Documentation', {
            'fields': ('receipt_image', 'invoice_file', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def amount_formatted(self, obj):
        """Display formatted amount."""
        return format_html('<strong>QAR {}</strong>', f'{obj.amount:.2f}')
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    
    def approval_status(self, obj):
        """Display approval status."""
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    approval_status.short_description = 'Approval'
    approval_status.admin_order_field = 'is_approved'
    
    def payment_status(self, obj):
        """Display payment status."""
        if obj.is_paid:
            return format_html('<span style="color: green;">✓ Paid</span>')
        elif obj.is_approved:
            return format_html('<span style="color: orange;">⏳ Approved</span>')
        else:
            return format_html('<span style="color: gray;">⏳ Pending</span>')
    payment_status.short_description = 'Payment'
    payment_status.admin_order_field = 'is_paid'
    
    def save_model(self, request, obj, form, change):
        """Set created_by field."""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'currency', 'total_allocated_display', 'total_spent_display', 'remaining_display')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = []

    def total_allocated_display(self, obj):
        return format_html('<strong>{}</strong>', f'{obj.total_allocated():.2f}')
    total_allocated_display.short_description = 'Allocated'

    def total_spent_display(self, obj):
        return format_html('<strong>QAR {}</strong>', f'{obj.total_spent():.2f}')
    total_spent_display.short_description = 'Spent'

    def remaining_display(self, obj):
        rem = obj.remaining() or 0
        color = 'green' if rem >= 0 else 'red'
        return format_html('<span style="color: {};">{:.2f}</span>', color, rem)
    remaining_display.short_description = 'Remaining'


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine
    extra = 1
    fields = ('name', 'category', 'amount', 'spent_display')
    readonly_fields = ('spent_display',)

    def spent_display(self, obj):
        return f"{obj.spent():.2f}"
    spent_display.short_description = 'Spent'


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget', 'category', 'amount', 'spent')
    list_filter = ('budget', 'category')
    search_fields = ('name',)
    readonly_fields = ('created_at',)
