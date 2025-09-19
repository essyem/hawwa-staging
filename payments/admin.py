from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Currency, PaymentMethod, Subscription, RecurringBilling, 
    PaymentReminder, FinancialForecast, ExchangeRateHistory
)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate_to_qar', 'is_active', 'last_updated']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = (
        ('Currency Information', {
            'fields': ('code', 'name', 'symbol')
        }),
        ('Exchange Rate', {
            'fields': ('exchange_rate_to_qar', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['code']
        return self.readonly_fields

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'provider', 'masked_number', 'is_default', 'is_active', 'created_at']
    list_filter = ['type', 'provider', 'is_default', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'provider']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Method Details', {
            'fields': ('user', 'type', 'provider')
        }),
        ('Card Information', {
            'fields': ('last_four_digits', 'expiry_month', 'expiry_year'),
            'description': 'For card-based payment methods only'
        }),
        ('Settings', {
            'fields': ('is_default', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def masked_number(self, obj):
        if obj.last_four_digits:
            return f"****{obj.last_four_digits}"
        return "-"
    masked_number.short_description = "Number"

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'name', 'service', 'status_badge', 'billing_cycle', 
        'effective_price_display', 'next_billing_date', 'days_remaining'
    ]
    list_filter = ['status', 'billing_cycle', 'currency', 'is_auto_renew']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'name', 'service__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'effective_price_display', 'days_remaining']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'service', 'name', 'description')
        }),
        ('Billing Configuration', {
            'fields': ('billing_cycle', 'base_price', 'currency', 'discount_percentage', 'payment_method')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date', 'trial_end_date')
        }),
        ('Billing Schedule', {
            'fields': ('next_billing_date', 'last_billing_date')
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_auto_renew')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'effective_price_display', 'days_remaining'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'trial': '#17a2b8',
            'active': '#28a745',
            'past_due': '#ffc107',
            'cancelled': '#dc3545',
            'expired': '#6c757d',
            'suspended': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def effective_price_display(self, obj):
        effective_price = obj.get_effective_price()
        qar_price = obj.get_price_in_qar()
        
        if obj.currency.code == 'QAR':
            return f"QAR {effective_price}"
        else:
            return f"{obj.currency.symbol}{effective_price} (QAR {qar_price:.2f})"
    effective_price_display.short_description = "Effective Price"

    def days_remaining(self, obj):
        days = obj.days_until_next_billing()
        if days is None:
            return "-"
        
        if days == 0:
            return format_html('<span style="color: red; font-weight: bold;">Due Today</span>')
        elif days <= 3:
            return format_html('<span style="color: orange; font-weight: bold;">{} days</span>', days)
        else:
            return f"{days} days"
    days_remaining.short_description = "Days to Next Billing"

    actions = ['suspend_subscriptions', 'reactivate_subscriptions']

    def suspend_subscriptions(self, request, queryset):
        count = 0
        for subscription in queryset:
            if subscription.status in ['active', 'trial']:
                subscription.suspend("Suspended by admin")
                count += 1
        self.message_user(request, f"Successfully suspended {count} subscriptions.")
    suspend_subscriptions.short_description = "Suspend selected subscriptions"

    def reactivate_subscriptions(self, request, queryset):
        count = 0
        for subscription in queryset:
            if subscription.status == 'suspended':
                subscription.reactivate()
                count += 1
        self.message_user(request, f"Successfully reactivated {count} subscriptions.")
    reactivate_subscriptions.short_description = "Reactivate selected subscriptions"

@admin.register(RecurringBilling)
class RecurringBillingAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_link', 'amount_display', 'billing_period', 
        'status_badge', 'retry_info', 'processed_at'
    ]
    list_filter = ['status', 'currency', 'billing_period_start']
    search_fields = [
        'subscription__name', 'subscription__user__first_name', 
        'subscription__user__last_name', 'gateway_transaction_id'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Billing Information', {
            'fields': ('subscription', 'amount', 'currency')
        }),
        ('Billing Period', {
            'fields': ('billing_period_start', 'billing_period_end')
        }),
        ('Processing Status', {
            'fields': ('status', 'processed_at', 'payment_method')
        }),
        ('Gateway Integration', {
            'fields': ('gateway_transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Retry Logic', {
            'fields': ('retry_count', 'max_retries', 'next_retry_at')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'failure_reason'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def subscription_link(self, obj):
        url = reverse('admin:payments_subscription_change', args=[obj.subscription.pk])
        return format_html('<a href="{}">{}</a>', url, obj.subscription.name)
    subscription_link.short_description = "Subscription"

    def amount_display(self, obj):
        return f"{obj.currency.symbol}{obj.amount}"
    amount_display.short_description = "Amount"

    def billing_period(self, obj):
        return f"{obj.billing_period_start.date()} to {obj.billing_period_end.date()}"
    billing_period.short_description = "Period"

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'refunded': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def retry_info(self, obj):
        if obj.status == 'failed':
            return f"{obj.retry_count}/{obj.max_retries} retries"
        return "-"
    retry_info.short_description = "Retries"

@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'reminder_type', 'escalation_badge', 'scheduled_for', 
        'status_badge', 'channels_display', 'sent_at'
    ]
    list_filter = ['reminder_type', 'escalation_level', 'status', 'send_email', 'send_sms']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'subject']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_for'
    
    fieldsets = (
        ('Reminder Details', {
            'fields': ('user', 'subscription', 'billing_record')
        }),
        ('Reminder Configuration', {
            'fields': ('reminder_type', 'escalation_level', 'subject', 'message')
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'sent_at', 'status')
        }),
        ('Communication Channels', {
            'fields': ('send_email', 'send_sms', 'send_push')
        }),
        ('Tracking', {
            'fields': ('email_opened', 'email_clicked', 'response_received'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def escalation_badge(self, obj):
        colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
        color = colors[min(obj.escalation_level - 1, 3)]
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">Level {}</span>',
            color, obj.escalation_level
        )
    escalation_badge.short_description = "Level"

    def status_badge(self, obj):
        colors = {
            'scheduled': '#17a2b8',
            'sent': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def channels_display(self, obj):
        channels = []
        if obj.send_email:
            channels.append('📧')
        if obj.send_sms:
            channels.append('📱')
        if obj.send_push:
            channels.append('🔔')
        return ' '.join(channels) if channels else '-'
    channels_display.short_description = "Channels"

@admin.register(FinancialForecast)
class FinancialForecastAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'forecast_type', 'period_display', 'accuracy_badge', 
        'predicted_revenue_display', 'is_current', 'generated_date'
    ]
    list_filter = ['forecast_type', 'accuracy_level', 'is_active', 'generated_date']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'generated_date', 'last_updated']
    date_hierarchy = 'generated_date'
    
    fieldsets = (
        ('Forecast Information', {
            'fields': ('forecast_type', 'title', 'description')
        }),
        ('Time Period', {
            'fields': ('forecast_period_start', 'forecast_period_end')
        }),
        ('Analysis Results', {
            'fields': ('confidence_score', 'accuracy_level', 'predicted_revenue', 'predicted_growth_rate')
        }),
        ('Data & Methodology', {
            'fields': ('algorithm_used', 'data_points_used', 'historical_data', 'forecast_data'),
            'classes': ('collapse',)
        }),
        ('Risk Assessment', {
            'fields': ('risk_factors',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'generated_date', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    def period_display(self, obj):
        return f"{obj.forecast_period_start} to {obj.forecast_period_end}"
    period_display.short_description = "Forecast Period"

    def accuracy_badge(self, obj):
        colors = {
            'high': '#28a745',
            'medium': '#ffc107',
            'low': '#fd7e14',
            'experimental': '#dc3545'
        }
        color = colors.get(obj.accuracy_level, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_accuracy_level_display()
        )
    accuracy_badge.short_description = "Accuracy"

    def predicted_revenue_display(self, obj):
        if obj.predicted_revenue:
            return f"QAR {obj.predicted_revenue:,.2f}"
        return "-"
    predicted_revenue_display.short_description = "Predicted Revenue"

    def is_current(self, obj):
        current = obj.is_current()
        if current:
            return format_html('<span style="color: green;">✓ Current</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    is_current.short_description = "Status"

@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    list_display = ['currency', 'rate_to_qar', 'date_recorded', 'source']
    list_filter = ['currency', 'source', 'date_recorded']
    search_fields = ['currency__code', 'currency__name']
    readonly_fields = ['date_recorded']
    date_hierarchy = 'date_recorded'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['currency', 'date_recorded']
        return self.readonly_fields
