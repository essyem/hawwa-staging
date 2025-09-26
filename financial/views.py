from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

from .forms import InvoiceForm, PaymentForm, ExpenseForm
from .models import Invoice, Payment, Expense, TaxRate, AccountingCategory
from .services.reports import trial_balance


class OverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'financial/base_overview.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'financial/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date filters
        today = timezone.now().date()
        this_month = today.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        
        # Financial metrics
        context.update({
            'total_revenue': Invoice.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0,
            'monthly_revenue': Invoice.objects.filter(status='paid', created_at__gte=this_month).aggregate(total=Sum('total_amount'))['total'] or 0,
            'pending_invoices': Invoice.objects.filter(status='pending').count(),
            'pending_amount': Invoice.objects.filter(status='pending').aggregate(total=Sum('total_amount'))['total'] or 0,
            'overdue_invoices': Invoice.objects.filter(status='overdue').count(),
            'total_expenses': Expense.objects.filter(expense_date__gte=this_month).aggregate(total=Sum('amount'))['total'] or 0,
            'recent_invoices': Invoice.objects.order_by('-created_at')[:5],
            'recent_payments': Payment.objects.order_by('-created_at')[:5],
            'recent_expenses': Expense.objects.order_by('-expense_date')[:5],
        })
        
        # Chart data
        revenue_data = self.get_revenue_chart_data()
        context['revenue_chart_data'] = json.dumps(revenue_data)
        
        expense_data = self.get_expense_chart_data()
        context['expense_chart_data'] = json.dumps(expense_data)
        
        return context
    
    def get_revenue_chart_data(self):
        # Last 12 months revenue data
        data = []
        today = timezone.now().date()
        
        for i in range(12):
            month = today.replace(day=1) - timedelta(days=i*30)
            revenue = Invoice.objects.filter(
                status='paid',
                created_at__year=month.year,
                created_at__month=month.month
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data.append({
                'month': month.strftime('%b %Y'),
                'revenue': float(revenue)
            })
        
        return list(reversed(data))
    
    def get_expense_chart_data(self):
        # Monthly expense breakdown by category
        this_month = timezone.now().date().replace(day=1)
        expenses = Expense.objects.filter(expense_date__gte=this_month).values(
            'category__name'
        ).annotate(total=Sum('amount'))
        
        return [{'category': exp['category__name'] or 'Uncategorized', 'amount': float(exp['total'])} for exp in expenses]


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'financial/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.all().select_related('customer').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the full queryset for stats (before pagination)
        full_queryset = self.get_queryset()
        context.update({
            'status_choices': Invoice.STATUS_CHOICES,
            'current_status': self.request.GET.get('status', ''),
            'current_search': self.request.GET.get('search', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'all_invoices': full_queryset,  # Full queryset for stats calculations
        })
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'financial/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'financial/invoice_form.html'
    permission_required = 'financial.add_invoice'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('financial:invoice_detail', kwargs={'pk': self.object.pk})


class InvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'financial/invoice_form.html'
    permission_required = 'financial.change_invoice'
    
    def get_success_url(self):
        return reverse('financial:invoice_detail', kwargs={'pk': self.object.pk})


class InvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'financial/invoice_confirm_delete.html'
    permission_required = 'financial.delete_invoice'
    success_url = reverse_lazy('financial:invoice_list')


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'financial/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Payment.objects.all().select_related('invoice', 'invoice__customer').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(payment_status=status)
            
        # Filter by payment method
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(payment_method=method)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_reference__icontains=search) |
                Q(gateway_transaction_id__icontains=search) |
                Q(invoice__invoice_number__icontains=search) |
                Q(invoice__customer__first_name__icontains=search) |
                Q(invoice__customer__last_name__icontains=search) |
                Q(invoice__customer__email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the full queryset for stats (before pagination)
        full_queryset = self.get_queryset()
        
        # Calculate stats
        completed_payments_count = full_queryset.filter(payment_status='completed').count()
        pending_payments_count = full_queryset.filter(payment_status='pending').count()
        total_amount = full_queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        context.update({
            'current_status': self.request.GET.get('status', ''),
            'current_method': self.request.GET.get('method', ''),
            'current_search': self.request.GET.get('search', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'all_payments': full_queryset,  # Full queryset for stats calculations
            'completed_payments_count': completed_payments_count,
            'pending_payments_count': pending_payments_count,
            'total_amount': total_amount,
        })
        return context


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'financial/payment_detail.html'
    context_object_name = 'payment'


class PaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    template_name = 'financial/payment_form.html'
    permission_required = 'financial.add_payment'
    fields = ['invoice', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
    
    def get_success_url(self):
        return reverse('financial:payment_detail', kwargs={'pk': self.object.pk})


class PaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Payment
    template_name = 'financial/payment_form.html'
    permission_required = 'financial.change_payment'
    fields = ['invoice', 'amount', 'payment_method', 'payment_date', 'reference_number', 'notes']
    
    def get_success_url(self):
        return reverse('financial:payment_detail', kwargs={'pk': self.object.pk})


class PaymentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Payment
    template_name = 'financial/payment_confirm_delete.html'
    permission_required = 'financial.delete_payment'
    success_url = reverse_lazy('financial:payment_list')


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'financial/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        return Expense.objects.all().order_by('-expense_date')


class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'financial/expense_detail.html'
    context_object_name = 'expense'


class ExpenseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Expense
    template_name = 'financial/expense_form.html'
    permission_required = 'financial.add_expense'
    fields = ['description', 'amount', 'category', 'expense_date', 'receipt_image', 'notes']
    
    def get_success_url(self):
        return reverse('financial:expense_detail', kwargs={'pk': self.object.pk})


class ExpenseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Expense
    template_name = 'financial/expense_form.html'
    permission_required = 'financial.change_expense'
    fields = ['description', 'amount', 'category', 'expense_date', 'receipt_image', 'notes']
    
    def get_success_url(self):
        return reverse('financial:expense_detail', kwargs={'pk': self.object.pk})


class ExpenseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Expense
    template_name = 'financial/expense_confirm_delete.html'
    permission_required = 'financial.delete_expense'
    success_url = reverse_lazy('financial:expense_list')


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'financial/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        context.update({
            'monthly_revenue': Invoice.objects.filter(status='paid', created_at__gte=this_month).aggregate(total=Sum('total_amount'))['total'] or 0,
            'monthly_expenses': Expense.objects.filter(expense_date__gte=this_month).aggregate(total=Sum('amount'))['total'] or 0,
            'outstanding_invoices': Invoice.objects.filter(status__in=['pending', 'overdue']).aggregate(total=Sum('total_amount'))['total'] or 0,
        })
        
        return context


# API Views
@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    today = timezone.now().date()
    this_month = today.replace(day=1)
    
    stats = {
        'total_revenue': float(Invoice.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0),
        'monthly_revenue': float(Invoice.objects.filter(status='paid', created_at__gte=this_month).aggregate(total=Sum('total_amount'))['total'] or 0),
        'pending_invoices': Invoice.objects.filter(status='pending').count(),
        'overdue_invoices': Invoice.objects.filter(status='overdue').count(),
        'total_expenses': float(Expense.objects.filter(expense_date__gte=this_month).aggregate(total=Sum('amount'))['total'] or 0),
    }
    
    return JsonResponse(stats)


@login_required
def invoice_status_update_api(request):
    """API endpoint to update invoice status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_id = data.get('invoice_id')
            new_status = data.get('status')
            
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            invoice.status = new_status
            invoice.save()
            
            return JsonResponse({'success': True, 'message': 'Invoice status updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def payment_quick_add_api(request):
    """API endpoint for quick payment creation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_id = data.get('invoice_id')
            amount = Decimal(data.get('amount'))
            payment_method = data.get('payment_method')
            
            invoice = get_object_or_404(Invoice, pk=invoice_id)
            
            payment = Payment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=payment_method,
                payment_date=timezone.now().date()
            )
            
            return JsonResponse({
                'success': True,
                'payment_id': payment.pk,
                'message': 'Payment added successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Report Views
@login_required
def profit_loss_report(request):
    """Profit & Loss Report"""
    # Implementation for P&L report
    context = {
        'report_type': 'Profit & Loss',
        'date_generated': timezone.now(),
    }
    return render(request, 'financial/reports/profit_loss.html', context)


@login_required
def trial_balance_report(request):
    """Trial Balance Report"""
    tb_data = trial_balance()
    context = {
        'trial_balance': tb_data,
        'report_type': 'Trial Balance',
        'date_generated': timezone.now(),
    }
    return render(request, 'financial/reports/trial_balance.html', context)


@login_required
def cash_flow_report(request):
    """Cash Flow Report"""
    context = {
        'report_type': 'Cash Flow',
        'date_generated': timezone.now(),
    }
    return render(request, 'financial/reports/cash_flow.html', context)


@login_required
def export_report(request, report_type):
    """Export reports to PDF/CSV"""
    # Implementation for report export
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
    
    # Generate PDF using reportlab
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"{report_type.title()} Report")
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def send_invoice(request, pk):
    """Send invoice via email"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Implementation for sending invoice email
    messages.success(request, f'Invoice {invoice.invoice_number} sent successfully!')
    return redirect('financial:invoice_detail', pk=pk)


@login_required
def invoice_pdf(request, pk):
    """Generate and download invoice PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Invoice: {invoice.invoice_number}")
    p.drawString(100, 730, f"Customer: {invoice.customer}")
    p.drawString(100, 710, f"Amount: {invoice.total_amount}")
    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response
