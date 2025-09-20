from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

class AccountingCategory(models.Model):
    """Categories for financial transactions and accounting."""
    name = models.CharField(_("Category Name"), max_length=100)
    code = models.CharField(_("Category Code"), max_length=20, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_cogs = models.BooleanField("Is COGS", default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Accounting Category")
        verbose_name_plural = _("Accounting Categories")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class TaxRate(models.Model):
    """Tax rates for different services and regions."""
    name = models.CharField(_("Tax Name"), max_length=100)
    rate = models.DecimalField(_("Tax Rate (%)"), max_digits=5, decimal_places=2, 
                              validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(_("Active"), default=True)
    effective_from = models.DateField(_("Effective From"))
    effective_to = models.DateField(_("Effective To"), null=True, blank=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.name} ({self.rate}%)"
    
    def is_current(self):
        """Check if tax rate is currently effective."""
        today = timezone.now().date()
        if self.effective_to:
            return self.effective_from <= today <= self.effective_to
        return self.effective_from <= today

class Invoice(models.Model):
    """Comprehensive invoice management for the Hawwa platform."""
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('paid', _('Paid')),
        ('partially_paid', _('Partially Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )
    
    INVOICE_TYPE_CHOICES = (
        ('booking', _('Booking Invoice')),
        ('service', _('Service Invoice')),
        ('subscription', _('Subscription Invoice')),
        ('addon', _('Add-on Invoice')),
        ('custom', _('Custom Invoice')),
    )
    
    # Basic Information
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, editable=False)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, 
                               related_name='invoices', verbose_name=_("Booking"), null=True, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='invoices', verbose_name=_("Customer"))
    
    # Invoice Details
    invoice_type = models.CharField(_("Invoice Type"), max_length=20, choices=INVOICE_TYPE_CHOICES, default='booking')
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    invoice_date = models.DateField(_("Invoice Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"))
    sent_date = models.DateTimeField(_("Sent Date"), null=True, blank=True)
    paid_date = models.DateTimeField(_("Paid Date"), null=True, blank=True)
    
    # Financial Details
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_due = models.DecimalField(_("Balance Due"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Additional Information
    notes = models.TextField(_("Notes"), blank=True)
    internal_notes = models.TextField(_("Internal Notes"), blank=True)
    terms_and_conditions = models.TextField(_("Terms and Conditions"), blank=True)
    
    # Billing Address
    billing_name = models.CharField(_("Billing Name"), max_length=255)
    billing_email = models.EmailField(_("Billing Email"))
    billing_phone = models.CharField(_("Billing Phone"), max_length=20, blank=True)
    billing_address = models.TextField(_("Billing Address"))
    billing_city = models.CharField(_("Billing City"), max_length=100)
    billing_state = models.CharField(_("Billing State"), max_length=100, blank=True)
    billing_postal_code = models.CharField(_("Billing Postal Code"), max_length=20)
    billing_country = models.CharField(_("Billing Country"), max_length=100, default="Qatar")
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, related_name='created_invoices', verbose_name=_("Created By"))
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['customer']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        if not self.due_date:
            self.due_date = self.invoice_date + timedelta(days=30)
        
        # Auto-populate billing info from customer if not provided
        if not self.billing_name and self.customer:
            self.billing_name = self.customer.get_full_name() or self.customer.email
            self.billing_email = self.customer.email
            self.billing_phone = self.customer.phone or ''
            self.billing_address = self.customer.address or ''
            self.billing_city = self.customer.city or ''
            self.billing_state = self.customer.state or ''
            self.billing_postal_code = self.customer.postal_code or ''
            self.billing_country = self.customer.country or 'Qatar'
        
        # Calculate totals
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate a unique invoice number."""
        today = timezone.now()
        prefix = f"INV-{today.strftime('%Y%m')}"
        
        # Get the last invoice number for this month
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}-{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals based on line items."""
        # Check if invoice has a primary key (is saved to database)
        if not self.pk:
            # If not saved yet, skip calculation
            return
            
        line_items = self.items.all()
        
        self.subtotal = sum(item.total_amount for item in line_items)
        
        # Calculate tax (if tax rate is applied)
        if hasattr(self, '_tax_rate'):
            self.tax_amount = (self.subtotal * self._tax_rate) / 100
        
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.balance_due = self.total_amount - self.paid_amount
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.get_full_name()} - QAR {self.total_amount}"
    
    def get_absolute_url(self):
        return reverse('financial:invoice_detail', kwargs={'pk': self.pk})
    
    def is_overdue(self):
        """Check if invoice is overdue."""
        return self.due_date < timezone.now().date() and self.status not in ['paid', 'cancelled', 'refunded']
    
    def mark_as_sent(self, user=None):
        """Mark invoice as sent."""
        self.status = 'sent'
        self.sent_date = timezone.now()
        if user:
            # Log the action (could be implemented with Django's admin logging)
            pass
        self.save()
    
    def mark_as_paid(self, amount=None, user=None):
        """Mark invoice as paid."""
        if amount is None:
            amount = self.balance_due
        
        self.paid_amount += amount
        self.balance_due = self.total_amount - self.paid_amount
        
        if self.balance_due <= 0:
            self.status = 'paid'
            self.paid_date = timezone.now()
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        
        self.save()

class InvoiceItem(models.Model):
    """Individual line items for invoices."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, 
                               related_name='items', verbose_name=_("Invoice"))
    service = models.ForeignKey('services.Service', on_delete=models.SET_NULL,
                               null=True, blank=True, verbose_name=_("Service"))
    
    # Item Details
    description = models.CharField(_("Description"), max_length=255)
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(_("Discount %"), max_digits=5, decimal_places=2, 
                                            default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cost_amount = models.DecimalField("Cost Amount", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    # Currency for the cost. If None, assume same as invoice/base currency (QAR)
    cost_currency = models.CharField("Cost Currency", max_length=10, default='QAR')
    
    # Accounting
    category = models.ForeignKey(AccountingCategory, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name=_("Category"))
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    line_order = models.PositiveIntegerField(_("Line Order"), default=0)
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
        ordering = ['line_order', 'created_at']
    
    def save(self, *args, **kwargs):
        # Calculate total amount using Decimal arithmetic
        discount_decimal = Decimal(str(self.discount_percentage)) / Decimal('100')
        discounted_price = self.unit_price * (Decimal('1') - discount_decimal)
        self.total_amount = self.quantity * discounted_price
        # Auto-populate cost_amount from linked service if not explicitly set
        try:
            if (not self.cost_amount or Decimal(self.cost_amount) == Decimal('0.00')) and self.service:
                # Prefer service.cost when available, otherwise fall back to service.price
                svc = self.service
                svc_cost = getattr(svc, 'cost', None)
                if svc_cost is None or Decimal(svc_cost) == Decimal('0.00'):
                    svc_cost = getattr(svc, 'price', Decimal('0.00'))
                # Multiply by quantity to get total cost for the line
                self.cost_amount = (Decimal(svc_cost) * self.quantity)
                # Assume service currency is QAR for now; future: store Service.currency
                self.cost_currency = getattr(svc, 'currency', 'QAR')
        except Exception:
            # Fail-safe: don't break save if service lookup fails
            pass
        super().save(*args, **kwargs)
        
        # Update invoice totals
        if self.invoice_id:
            self.invoice.calculate_totals()
            self.invoice.save()
    
    def __str__(self):
        return f"{self.description} - QAR {self.total_amount}"

class Payment(models.Model):
    """Track payments received for invoices."""
    PAYMENT_METHOD_CHOICES = (
        ('cash', _('Cash')),
        ('bank_transfer', _('Bank Transfer')),
        ('credit_card', _('Credit Card')),
        ('debit_card', _('Debit Card')),
        ('online_payment', _('Online Payment')),
        ('cheque', _('Cheque')),
        ('other', _('Other')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                               related_name='payments', verbose_name=_("Invoice"))
    
    # Payment Details
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(_("Payment Status"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment Information
    transaction_reference = models.CharField(_("Transaction Reference"), max_length=100, blank=True)
    payment_gateway = models.CharField(_("Payment Gateway"), max_length=50, blank=True)
    gateway_transaction_id = models.CharField(_("Gateway Transaction ID"), max_length=100, blank=True)
    
    # Dates
    payment_date = models.DateTimeField(_("Payment Date"), default=timezone.now)
    processed_date = models.DateTimeField(_("Processed Date"), null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(_("Notes"), blank=True)
    receipt_sent = models.BooleanField(_("Receipt Sent"), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name=_("Processed By"))
    
    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-payment_date']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice payment status
        if self.payment_status == 'completed':
            self.invoice.mark_as_paid(self.amount)
    
    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"
    
    def mark_as_completed(self, user=None):
        """Mark payment as completed."""
        self.payment_status = 'completed'
        self.processed_date = timezone.now()
        if user:
            self.processed_by = user
        self.save()

class Expense(models.Model):
    """Track business expenses."""
    EXPENSE_TYPE_CHOICES = (
        ('operational', _('Operational')),
        ('marketing', _('Marketing')),
        ('equipment', _('Equipment')),
        ('supplies', _('Supplies')),
        ('utilities', _('Utilities')),
        ('travel', _('Travel')),
        ('professional_services', _('Professional Services')),
        ('other', _('Other')),
    )
    
    # Basic Information
    description = models.CharField(_("Description"), max_length=255)
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    expense_type = models.CharField(_("Expense Type"), max_length=30, choices=EXPENSE_TYPE_CHOICES)
    category = models.ForeignKey(AccountingCategory, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name=_("Category"))
    
    # Vendor/Supplier Information
    vendor_name = models.CharField(_("Vendor Name"), max_length=255, blank=True)
    vendor_email = models.EmailField(_("Vendor Email"), blank=True)
    vendor_phone = models.CharField(_("Vendor Phone"), max_length=20, blank=True)
    
    # Dates and Status
    expense_date = models.DateField(_("Expense Date"), default=timezone.now)
    is_approved = models.BooleanField(_("Approved"), default=False)
    is_paid = models.BooleanField(_("Paid"), default=False)
    payment_date = models.DateField(_("Payment Date"), null=True, blank=True)
    
    # Documentation
    receipt_image = models.ImageField(_("Receipt Image"), upload_to='expenses/receipts/', blank=True, null=True)
    invoice_file = models.FileField(_("Invoice File"), upload_to='expenses/invoices/', blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  null=True, verbose_name=_("Created By"))
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='approved_expenses', verbose_name=_("Approved By"))
    
    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.description} - QAR {self.amount}"
    
    def approve(self, user):
        """Approve the expense."""
        self.is_approved = True
        self.approved_by = user
        self.save()


class CurrencyRate(models.Model):
    """Simple historical currency rate table for converting amounts between currencies.

    rate is the multiplier to convert 1 unit of `from_currency` into `to_currency`.
    Example: from_currency='USD', to_currency='QAR', rate=3.64 means 1 USD = 3.64 QAR.
    """
    from_currency = models.CharField("From Currency", max_length=10)
    to_currency = models.CharField("To Currency", max_length=10)
    rate = models.DecimalField("Rate", max_digits=20, decimal_places=8)
    valid_from = models.DateField("Valid From", default=timezone.now)
    valid_to = models.DateField("Valid To", null=True, blank=True)

    class Meta:
        verbose_name = "Currency Rate"
        verbose_name_plural = "Currency Rates"
        indexes = [models.Index(fields=['from_currency', 'to_currency', 'valid_from'])]

    def __str__(self):
        return f"1 {self.from_currency} → {self.rate} {self.to_currency} (from {self.valid_from})"
    
    def mark_as_paid(self):
        """Mark expense as paid."""
        self.is_paid = True
        self.payment_date = timezone.now().date()
        self.save()


class Budget(models.Model):
    """Budget header representing a budget period and owner."""
    name = models.CharField("Budget Name", max_length=200)
    start_date = models.DateField("Start Date")
    end_date = models.DateField("End Date")
    currency = models.CharField("Currency", max_length=10, default='QAR')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='budgets_created')
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    def total_allocated(self):
        return self.lines.aggregate(total=models.Sum('amount'))['total'] or 0

    def total_spent(self):
        # Sum expenses and invoice items that fall within budget period
        expense_sum = Expense.objects.filter(
            expense_date__gte=self.start_date,
            expense_date__lte=self.end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        # InvoiceItem total_amount via related Invoice date
        invoice_sum = InvoiceItem.objects.filter(
            invoice__invoice_date__gte=self.start_date,
            invoice__invoice_date__lte=self.end_date
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0

        return expense_sum + invoice_sum

    def remaining(self):
        return (self.total_allocated() or 0) - (self.total_spent() or 0)


class BudgetLine(models.Model):
    """Individual budget line tied to a Budget and optionally a category."""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lines')
    name = models.CharField("Line Name", max_length=200)
    category = models.ForeignKey(AccountingCategory, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='budget_lines')
    amount = models.DecimalField("Amount", max_digits=12, decimal_places=2)
    notes = models.TextField("Notes", blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Budget Line"
        verbose_name_plural = "Budget Lines"
        ordering = ['-amount']

    def __str__(self):
        return f"{self.name} - {self.amount} {self.budget.currency}"

    def spent(self):
        """Calculate spent amount for this line by category within budget period."""
        if not self.category:
            return 0

        expense_sum = Expense.objects.filter(
            category=self.category,
            expense_date__gte=self.budget.start_date,
            expense_date__lte=self.budget.end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        invoice_sum = InvoiceItem.objects.filter(
            category=self.category,
            invoice__invoice_date__gte=self.budget.start_date,
            invoice__invoice_date__lte=self.budget.end_date
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0

        return expense_sum + invoice_sum


class LedgerAccount(models.Model):
    """A ledger account for double-entry bookkeeping."""
    code = models.CharField("Account Code", max_length=32, unique=True)
    name = models.CharField("Account Name", max_length=200)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    ACCOUNT_TYPE_CHOICES = (
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    )
    account_type = models.CharField("Account Type", max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='asset')
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Ledger Account"
        verbose_name_plural = "Ledger Accounts"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """A journal entry grouping one or more journal lines."""
    reference = models.CharField("Reference", max_length=100, blank=True)
    date = models.DateField("Date", default=timezone.now)
    narration = models.TextField("Narration", blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"JE-{self.pk} {self.reference or ''} {self.date}"

    def total_debits(self):
        return self.lines.aggregate(total=models.Sum('debit'))['total'] or 0

    def total_credits(self):
        return self.lines.aggregate(total=models.Sum('credit'))['total'] or 0

    def is_balanced(self):
        return Decimal(str(self.total_debits())) == Decimal(str(self.total_credits()))

    def post(self):
        """Mark entry as posted. For now this is a placeholder for future ledger balance updates."""
        if not self.is_balanced():
            raise ValueError('JournalEntry is not balanced')
        # In a full implementation, posting would create/update ledger balances.
        return True


class JournalLine(models.Model):
    """A single debit/credit line belonging to a JournalEntry."""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name='lines')
    debit = models.DecimalField("Debit", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField("Credit", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    narration = models.CharField("Narration", max_length=200, blank=True)

    class Meta:
        verbose_name = "Journal Line"
        verbose_name_plural = "Journal Lines"

    def clean(self):
        # Ensure debit and credit are not both set
        if self.debit > 0 and self.credit > 0:
            raise ValueError('JournalLine cannot have both debit and credit greater than 0')

    def __str__(self):
        return f"{self.account.code} D:{self.debit} C:{self.credit}"


class LedgerBalance(models.Model):
    """Materialized per-account balance for quick queries and trial balance reports."""
    account = models.OneToOneField(LedgerAccount, on_delete=models.CASCADE, related_name='balance')
    balance = models.DecimalField("Balance", max_digits=18, decimal_places=2, default=Decimal('0.00'))
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Ledger Balance"
        verbose_name_plural = "Ledger Balances"

    def __str__(self):
        return f"{self.account.code} - {self.balance}"
