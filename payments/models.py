from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta

User = get_user_model()

class Currency(models.Model):
    """Multi-currency support model"""
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 currency code (e.g., USD, EUR, QAR)")
    name = models.CharField(max_length=50, help_text="Currency full name")
    symbol = models.CharField(max_length=5, help_text="Currency symbol (e.g., $, €, ﷼)")
    exchange_rate_to_qar = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=Decimal('1.0000'),
        help_text="Exchange rate to Qatari Riyal (base currency)"
    )
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} - {self.name}"

    def convert_to_qar(self, amount):
        """Convert amount from this currency to QAR"""
        return amount * self.exchange_rate_to_qar

    def convert_from_qar(self, qar_amount):
        """Convert QAR amount to this currency"""
        if self.exchange_rate_to_qar == 0:
            return Decimal('0.00')
        return qar_amount / self.exchange_rate_to_qar

class PaymentMethod(models.Model):
    """Enhanced payment method management"""
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('digital_wallet', 'Digital Wallet'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('crypto', 'Cryptocurrency'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    provider = models.CharField(max_length=50, help_text="e.g., Visa, MasterCard, PayPal")
    last_four_digits = models.CharField(max_length=4, blank=True, help_text="Last 4 digits for cards")
    expiry_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    expiry_year = models.IntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        if self.last_four_digits:
            return f"{self.provider} ****{self.last_four_digits}"
        return f"{self.provider} {self.type}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default payment method per user
            PaymentMethod.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class Subscription(models.Model):
    """Advanced subscription management"""
    BILLING_CYCLES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('trial', 'Trial Period'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='subscriptions')
    
    # Subscription Details
    name = models.CharField(max_length=100, help_text="Subscription plan name")
    description = models.TextField(blank=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField()
    last_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    is_auto_renew = models.BooleanField(default=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional subscription data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['next_billing_date']),
            models.Index(fields=['service', 'status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name} ({self.status})"

    def get_effective_price(self):
        """Calculate price after discount"""
        discount_amount = (self.base_price * self.discount_percentage) / 100
        return self.base_price - discount_amount

    def get_price_in_qar(self):
        """Get subscription price in QAR"""
        effective_price = self.get_effective_price()
        return self.currency.convert_to_qar(effective_price)

    def is_trial_active(self):
        """Check if trial period is still active"""
        if not self.trial_end_date:
            return False
        return timezone.now() <= self.trial_end_date

    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['trial', 'active']

    def days_until_next_billing(self):
        """Calculate days until next billing"""
        if not self.next_billing_date:
            return None
        delta = self.next_billing_date - timezone.now()
        return delta.days if delta.days >= 0 else 0

    def calculate_next_billing_date(self):
        """Calculate next billing date based on cycle"""
        current_date = self.next_billing_date or timezone.now()
        
        if self.billing_cycle == 'daily':
            return current_date + timedelta(days=1)
        elif self.billing_cycle == 'weekly':
            return current_date + timedelta(weeks=1)
        elif self.billing_cycle == 'monthly':
            return current_date + timedelta(days=30)
        elif self.billing_cycle == 'quarterly':
            return current_date + timedelta(days=90)
        elif self.billing_cycle == 'yearly':
            return current_date + timedelta(days=365)
        
        return current_date

    def suspend(self, reason=""):
        """Suspend subscription"""
        self.status = 'suspended'
        self.metadata['suspension_reason'] = reason
        self.metadata['suspended_at'] = timezone.now().isoformat()
        self.save()

    def reactivate(self):
        """Reactivate suspended subscription"""
        if self.status == 'suspended':
            self.status = 'active'
            self.metadata.pop('suspension_reason', None)
            self.metadata.pop('suspended_at', None)
            self.save()

class RecurringBilling(models.Model):
    """Automated recurring billing management"""
    BILLING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='billing_records')
    
    # Billing Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    billing_period_start = models.DateTimeField()
    billing_period_end = models.DateTimeField()
    
    # Processing
    status = models.CharField(max_length=20, choices=BILLING_STATUS, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    
    # Payment Gateway Integration
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Retry Logic
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['billing_period_start', 'billing_period_end']),
            models.Index(fields=['next_retry_at']),
        ]

    def __str__(self):
        return f"Billing {self.subscription.name} - {self.amount} {self.currency.code} ({self.status})"

    def can_retry(self):
        """Check if billing can be retried"""
        return (
            self.status == 'failed' and 
            self.retry_count < self.max_retries and
            self.next_retry_at and
            timezone.now() >= self.next_retry_at
        )

    def schedule_retry(self, delay_hours=24):
        """Schedule next retry attempt"""
        if self.retry_count < self.max_retries:
            self.next_retry_at = timezone.now() + timedelta(hours=delay_hours)
            self.save()

    def mark_completed(self, transaction_id="", gateway_response=None):
        """Mark billing as completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.gateway_transaction_id = transaction_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()

        # Update subscription
        self.subscription.last_billing_date = self.processed_at
        self.subscription.next_billing_date = self.subscription.calculate_next_billing_date()
        self.subscription.save()

    def mark_failed(self, error_message="", failure_reason=""):
        """Mark billing as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.failure_reason = failure_reason
        self.retry_count += 1
        
        # Schedule retry if possible
        if self.retry_count < self.max_retries:
            retry_delay = 24 * self.retry_count  # Exponential backoff
            self.schedule_retry(retry_delay)
        
        self.save()

class PaymentReminder(models.Model):
    """Automated payment reminder system"""
    REMINDER_TYPES = [
        ('upcoming_payment', 'Upcoming Payment'),
        ('overdue_payment', 'Overdue Payment'),
        ('failed_payment', 'Failed Payment'),
        ('trial_ending', 'Trial Ending'),
        ('subscription_expiring', 'Subscription Expiring'),
    ]

    REMINDER_STATUS = [
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    ESCALATION_LEVELS = [
        (1, 'First Reminder'),
        (2, 'Second Reminder'),
        (3, 'Final Notice'),
        (4, 'Account Suspension Notice'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_reminders')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payment_reminders', null=True, blank=True)
    billing_record = models.ForeignKey(RecurringBilling, on_delete=models.CASCADE, null=True, blank=True)
    
    # Reminder Details
    reminder_type = models.CharField(max_length=30, choices=REMINDER_TYPES)
    escalation_level = models.IntegerField(choices=ESCALATION_LEVELS, default=1)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Scheduling
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=REMINDER_STATUS, default='scheduled')
    
    # Communication Channels
    send_email = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=False)
    
    # Tracking
    email_opened = models.BooleanField(default=False)
    email_clicked = models.BooleanField(default=False)
    response_received = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_for', 'status']),
            models.Index(fields=['reminder_type', 'escalation_level']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_reminder_type_display()} (Level {self.escalation_level})"

    def is_due(self):
        """Check if reminder is due for sending"""
        return (
            self.status == 'scheduled' and
            timezone.now() >= self.scheduled_for
        )

    def mark_sent(self):
        """Mark reminder as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()

    def mark_failed(self, error_message=""):
        """Mark reminder as failed"""
        self.status = 'failed'
        self.metadata['error_message'] = error_message
        self.metadata['failed_at'] = timezone.now().isoformat()
        self.save()

    def schedule_escalation(self, days_delay=3):
        """Schedule next escalation level"""
        if self.escalation_level < 4:
            next_reminder = PaymentReminder.objects.create(
                user=self.user,
                subscription=self.subscription,
                billing_record=self.billing_record,
                reminder_type=self.reminder_type,
                escalation_level=self.escalation_level + 1,
                subject=f"URGENT: {self.subject}",
                message=self.message,
                scheduled_for=timezone.now() + timedelta(days=days_delay),
                send_email=self.send_email,
                send_sms=True,  # Escalate to SMS
                send_push=self.send_push,
            )
            return next_reminder
        return None

class FinancialForecast(models.Model):
    """Financial forecasting and analytics"""
    FORECAST_TYPES = [
        ('revenue', 'Revenue Forecast'),
        ('cash_flow', 'Cash Flow Forecast'),
        ('subscription_growth', 'Subscription Growth'),
        ('churn_prediction', 'Churn Prediction'),
        ('seasonal_trends', 'Seasonal Trends'),
    ]

    ACCURACY_LEVELS = [
        ('high', 'High (90%+)'),
        ('medium', 'Medium (70-89%)'),
        ('low', 'Low (50-69%)'),
        ('experimental', 'Experimental (<50%)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Forecast Details
    forecast_type = models.CharField(max_length=30, choices=FORECAST_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Time Period
    forecast_period_start = models.DateField()
    forecast_period_end = models.DateField()
    generated_date = models.DateTimeField(auto_now_add=True)
    
    # Data and Results
    historical_data = models.JSONField(default=dict, help_text="Historical data used for forecast")
    forecast_data = models.JSONField(default=dict, help_text="Forecast results and predictions")
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    accuracy_level = models.CharField(max_length=20, choices=ACCURACY_LEVELS)
    
    # Financial Metrics
    predicted_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    predicted_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    risk_factors = models.JSONField(default=list, help_text="Identified risk factors")
    
    # Methodology
    algorithm_used = models.CharField(max_length=50, default="Linear Regression")
    data_points_used = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-generated_date']
        indexes = [
            models.Index(fields=['forecast_type', 'is_active']),
            models.Index(fields=['forecast_period_start', 'forecast_period_end']),
        ]

    def __str__(self):
        return f"{self.title} ({self.forecast_period_start} to {self.forecast_period_end})"

    def get_accuracy_percentage(self):
        """Get accuracy as percentage"""
        return float(self.confidence_score)

    def is_current(self):
        """Check if forecast is still current"""
        return (
            self.is_active and
            timezone.now().date() <= self.forecast_period_end
        )

    def calculate_variance(self, actual_value):
        """Calculate variance between predicted and actual values"""
        if not self.predicted_revenue:
            return None
        
        variance = abs(float(actual_value) - float(self.predicted_revenue))
        variance_percentage = (variance / float(self.predicted_revenue)) * 100
        return {
            'absolute_variance': variance,
            'percentage_variance': variance_percentage,
            'accuracy': max(0, 100 - variance_percentage)
        }

class ExchangeRateHistory(models.Model):
    """Track historical exchange rates for reporting"""
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rate_history')
    rate_to_qar = models.DecimalField(max_digits=10, decimal_places=4)
    date_recorded = models.DateField(auto_now_add=True)
    source = models.CharField(max_length=50, default="Manual", help_text="Rate source (API, Manual, etc.)")
    
    class Meta:
        ordering = ['-date_recorded']
        unique_together = ['currency', 'date_recorded']
        indexes = [
            models.Index(fields=['currency', 'date_recorded']),
        ]

    def __str__(self):
        return f"{self.currency.code} - {self.rate_to_qar} QAR ({self.date_recorded})"
