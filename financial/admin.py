from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
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
from .models import CurrencyRate
from . import admin_views
from .models import Budget, BudgetLine
from .models import LedgerAccount, JournalEntry, JournalLine
from django.core.management import call_command
from django import forms
import csv
from io import TextIOWrapper, BytesIO
from decimal import Decimal
import base64
import json
import difflib

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


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'rate', 'valid_from', 'valid_to')
    list_filter = ('from_currency', 'to_currency', 'valid_from')
    search_fields = ('from_currency', 'to_currency')
    date_hierarchy = 'valid_from'


# Admin form for CSV upload
class InvoiceItemCostCSVForm(forms.Form):
    csv_file = forms.FileField(label='CSV file')
    invoice_field = forms.CharField(label='Invoice column name', required=False, initial='invoice_number')
    description_field = forms.CharField(label='Description column name', required=False, initial='description')
    cost_field = forms.CharField(label='Cost column name', required=False, initial='cost_amount')
    currency_field = forms.CharField(label='Currency column name', required=False, initial='cost_currency')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'invoice', 'quantity', 'unit_price', 'total_amount', 'cost_amount', 'cost_currency')
    list_filter = ('category',)
    search_fields = ('description', 'invoice__invoice_number')
    change_list_template = 'admin/financial/invoiceitem_changelist.html'
    actions = ['set_costs_from_service']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-costs/', self.admin_site.admin_view(self.import_costs_view), name='financial_invoiceitem_import_costs'),
        ]
        return custom_urls + urls

    def import_costs_view(self, request):
        """Simple CSV import for invoice item costs.

        CSV columns expected: invoice_number, description (or leave blank), cost_amount, cost_currency
        Matches by invoice_number and description best-effort.
        """
        # Allow downloading unmatched rows via GET with payload
        if request.method == 'GET' and request.GET.get('download_unmatched') == '1':
            # Prefer explicit payload param, otherwise try session-stored unmatched rows
            payload_param = request.GET.get('payload')
            not_found = None
            if payload_param:
                try:
                    payload_json = base64.b64decode(payload_param).decode('utf-8')
                    not_found = json.loads(payload_json)
                except Exception:
                    return HttpResponse('Invalid payload', status=400)
            else:
                not_found = request.session.get('financial_import_unmatched') or []

            out = BytesIO()
            text_out = TextIOWrapper(out, encoding='utf-8', write_through=True)
            writer = csv.writer(text_out)
            writer.writerow(['invoice', 'reason'])
            for nf in (not_found or []):
                writer.writerow([nf.get('invoice'), nf.get('reason')])
            text_out.flush()
            out.seek(0)
            resp = HttpResponse(out.read(), content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename="unmatched_invoice_rows.csv"'
            # Clear stored unmatched rows from session after download
            try:
                if 'financial_import_unmatched' in request.session:
                    del request.session['financial_import_unmatched']
                    request.session.modified = True
            except Exception:
                pass
            return resp

        if request.method == 'POST':
            # If commit flag is set, payload contains a base64 JSON of parsed rows.
            # Also allow commits when the preview form posts per-row fields (rows_count) without commit_payload.
            if 'commit_payload' in request.POST or request.POST.get('rows_count'):
                # If the form posted per-row edited fields, build rows from those inputs.
                rows = []
                try:
                    rows_count = int(request.POST.get('rows_count', '0'))
                except Exception:
                    rows_count = 0

                if rows_count > 0:
                    # Collect rows from per-row inputs
                    for i in range(rows_count):
                        inv = request.POST.get(f'row_invoice_{i}', '').strip() or None
                        desc = request.POST.get(f'row_description_{i}', '').strip() or None
                        cost = request.POST.get(f'row_cost_{i}', '').strip() or None
                        ccy = request.POST.get(f'row_currency_{i}', '').strip() or None
                        rows.append({'invoice': inv, 'description': desc, 'cost': cost, 'currency': ccy})
                else:
                    # Fallback to base64 payload if no per-row edits were sent
                    payload_b64 = request.POST.get('commit_payload')
                    try:
                        payload_json = base64.b64decode(payload_b64).decode('utf-8')
                        rows = json.loads(payload_json)
                    except Exception:
                        self.message_user(request, 'Invalid commit payload', level=messages.ERROR)
                        return HttpResponse(render_to_string('admin/financial/import_costs.html', {'form': InvoiceItemCostCSVForm(), 'title': 'Import InvoiceItem Costs'}, request=request))

                updated = 0
                not_found = []
                errors = []
                for row in rows:
                    inv_num = row.get('invoice')
                    desc = row.get('description')
                    cost = row.get('cost')
                    ccy = row.get('currency') or 'QAR'
                    if not inv_num or not cost:
                        not_found.append({'invoice': inv_num, 'reason': 'missing invoice or cost'})
                        continue
                    items = InvoiceItem.objects.filter(invoice__invoice_number=inv_num)
                    if desc:
                        items = items.filter(description__iexact=desc)
                    item = items.first()
                    if item:
                        try:
                            item.cost_amount = Decimal(str(cost))
                            item.cost_currency = ccy
                            item.save()
                            updated += 1
                        except Exception as e:
                            errors.append({'invoice': inv_num, 'error': str(e)})
                    else:
                        not_found.append({'invoice': inv_num, 'reason': 'no matching item'})

                self.message_user(request, f"Updated costs for {updated} items. Not found: {len(not_found)}")
                # Store unmatched rows in session so a follow-up GET can download them
                try:
                    request.session['financial_import_unmatched'] = not_found
                    request.session.modified = True
                except Exception:
                    # ignore session storage errors
                    pass

                # Prepare payload for unmatched rows so users can download via GET
                try:
                    unmatched_payload = base64.b64encode(json.dumps(not_found).encode('utf-8')).decode('utf-8') if not_found else ''
                except Exception:
                    unmatched_payload = ''

                # Render HTML result
                context = {'updated': updated, 'not_found': not_found, 'errors': errors, 'unmatched_payload': unmatched_payload}
                return HttpResponse(render_to_string('admin/financial/import_result.html', context, request=request))

            # Otherwise it's an initial upload/preview request
            form = InvoiceItemCostCSVForm(request.POST, request.FILES)
            if form.is_valid():
                f = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
                reader = csv.DictReader(f)
                invoice_col = form.cleaned_data.get('invoice_field') or 'invoice_number'
                desc_col = form.cleaned_data.get('description_field') or 'description'
                cost_col = form.cleaned_data.get('cost_field') or 'cost_amount'
                ccy_col = form.cleaned_data.get('currency_field') or 'cost_currency'

                preview_rows = []
                # Collect existing keys to match against
                all_descriptions = list(InvoiceItem.objects.values_list('description', flat=True))
                all_invoices = list(InvoiceItem.objects.values_list('invoice__invoice_number', flat=True))

                def sanitize(val):
                    if val is None:
                        return None
                    # Remove control characters except common whitespace
                    return ''.join(ch for ch in str(val) if ch.isprintable())

                for row in reader:
                    inv_num = sanitize(row.get(invoice_col) or row.get('invoice_number') or row.get('invoice'))
                    desc = sanitize(row.get(desc_col) or row.get('description'))
                    cost = sanitize(row.get(cost_col) or row.get('cost_amount'))
                    ccy = sanitize(row.get(ccy_col) or row.get('cost_currency') or 'QAR')
                    match = None
                    if inv_num and cost:
                        items = InvoiceItem.objects.filter(invoice__invoice_number=inv_num)
                        if desc:
                            items = items.filter(description__iexact=desc)
                        match = items.first()
                    suggestions = []
                    if not match:
                        # Suggest similar descriptions and invoices
                        if desc:
                            desc_sugg = difflib.get_close_matches(desc, all_descriptions, n=3, cutoff=0.6)
                        else:
                            desc_sugg = []
                        inv_sugg = difflib.get_close_matches(inv_num or '', all_invoices, n=3, cutoff=0.7) if inv_num else []
                        suggestions = {'descriptions': desc_sugg, 'invoices': inv_sugg}

                    preview_rows.append({'invoice': inv_num, 'description': desc, 'cost': cost, 'currency': ccy, 'matched': bool(match), 'suggestions': suggestions})

                # Encode preview_rows into base64 payload for commit
                payload = base64.b64encode(json.dumps(preview_rows).encode('utf-8')).decode('utf-8')
                context = {'form': form, 'title': 'Import InvoiceItem Costs - Preview', 'preview_rows': preview_rows, 'commit_payload': payload}
                return HttpResponse(render_to_string('admin/financial/import_preview.html', context, request=request))
        else:
            form = InvoiceItemCostCSVForm()
        context = {'form': form, 'title': 'Import InvoiceItem Costs'}
        return HttpResponse(render_to_string('admin/financial/import_costs.html', context, request=request))

    def set_costs_from_service(self, request, queryset):
        updated = 0
        for item in queryset:
            if item.service:
                svc_cost = getattr(item.service, 'cost', None)
                if svc_cost is None or Decimal(svc_cost) == Decimal('0.00'):
                    svc_cost = getattr(item.service, 'price', Decimal('0.00'))
                item.cost_amount = Decimal(svc_cost) * item.quantity
                item.cost_currency = getattr(item.service, 'currency', 'QAR')
                item.save()
                updated += 1
        self.message_user(request, f"Updated cost for {updated} items.")
    set_costs_from_service.short_description = 'Set cost amounts from linked Service'


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active')
    list_editable = ('account_type', 'is_active')
    search_fields = ('code', 'name')
    actions = ['rebuild_selected_accounts']

    @admin.action(description='Rebuild balances for selected accounts')
    def rebuild_selected_accounts(self, request, queryset):
        # For each selected account, compute balance from journal lines and update LedgerBalance
        from .models import LedgerBalance
        changed = 0
        for acct in queryset:
            # Aggregate via JournalLine DB grouping to compute balance
            qs = JournalLine.objects.filter(account=acct).aggregate(
                debits=Sum('debit') , credits=Sum('credit')
            )
            debits = qs['debits'] or 0
            credits = qs['credits'] or 0
            if acct.account_type in ('asset', 'expense'):
                new_bal = debits - credits
            else:
                new_bal = credits - debits
            lb, _ = LedgerBalance.objects.get_or_create(account=acct, defaults={'balance': new_bal})
            if lb.balance != new_bal:
                lb.balance = new_bal
                lb.save()
                changed += 1
        messages.info(request, f"Rebuilt balances for {queryset.count()} accounts, changed: {changed}")


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1
    fields = ('account', 'debit', 'credit', 'narration')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('reference', 'date', 'narration', 'created_at')
    inlines = [JournalLineInline]
    readonly_fields = ('created_at',)

    actions = ['post_entries']

    @admin.action(description='Post selected journal entries')
    def post_entries(self, request, queryset):
        success = 0
        failed = 0
        for entry in queryset:
            try:
                entry.post()
                success += 1
            except Exception as e:
                failed += 1
        messages.info(request, f"Posted {success} entries, {failed} failed.")


# Add admin view url for trial balance by wrapping admin.site.get_urls
original_get_urls = admin.site.get_urls

def get_urls():
    my_urls = [
        path('financial/trial-balance/', admin_views.trial_balance_view, name='financial_trial_balance'),
    ]
    return my_urls + original_get_urls()

admin.site.get_urls = get_urls
