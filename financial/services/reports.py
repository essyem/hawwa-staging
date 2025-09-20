from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from ..models import Invoice, InvoiceItem, Payment, Expense
from ..models import LedgerBalance, LedgerAccount
from ..models import InvoiceItem, AccountingCategory
from .currency import convert_amount


def profit_and_loss(start_date, end_date, base_currency='QAR'):
    """Return a simple Profit & Loss summary for the period.

    Returns dict: { 'revenue': Decimal, 'costs': Decimal, 'expenses': Decimal, 'gross_profit': Decimal, 'net_profit': Decimal }
    """
    # Revenue: total and per-category revenue from invoice items for invoices in period
    invoice_sum = InvoiceItem.objects.filter(
        invoice__invoice_date__gte=start_date,
        invoice__invoice_date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Revenue grouped by category
    revenue_grouped = InvoiceItem.objects.filter(
        invoice__invoice_date__gte=start_date,
        invoice__invoice_date__lte=end_date,
    ).values('category__id', 'category__code', 'category__name').annotate(revenue=Sum('total_amount'))

    # Costs: per-category costs by summing invoice items marked as COGS and normalizing currency per line
    cogs_items = InvoiceItem.objects.filter(
        invoice__invoice_date__gte=start_date,
        invoice__invoice_date__lte=end_date,
        category__is_cogs=True
    ).values('category__id', 'category__code', 'category__name', 'cost_amount', 'cost_currency', 'invoice__invoice_date')

    costs = Decimal('0.00')
    costs_by_category = {}
    for item in cogs_items:
        cat_id = item.get('category__id')
        cat_code = item.get('category__code') or 'UNCAT'
        cat_name = item.get('category__name') or 'Uncategorized'
        amt = Decimal(item.get('cost_amount') or '0')
        from_ccy = item.get('cost_currency') or 'QAR'
        inv_date = item.get('invoice__invoice_date')
        converted = Decimal(convert_amount(amt, from_ccy, base_currency, date=inv_date))
        costs += converted
        key = (cat_id, cat_code, cat_name)
        costs_by_category.setdefault(key, Decimal('0.00'))
        costs_by_category[key] += converted

    # Expenses: sum of Expense.amount in period
    expense_sum = Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    revenue = Decimal(invoice_sum)
    expenses = Decimal(expense_sum)
    gross_profit = revenue - costs
    net_profit = gross_profit - expenses

    gross_margin_pct = (gross_profit / revenue * 100) if revenue and revenue != Decimal('0.00') else Decimal('0.00')

    # Build breakdown per category
    breakdown = {}
    # Start with revenue per category
    for r in revenue_grouped:
        key = (r.get('category__id'), r.get('category__code') or 'UNCAT', r.get('category__name') or 'Uncategorized')
        breakdown[key] = {
            'revenue': Decimal(r.get('revenue') or '0'),
            'costs': Decimal('0.00'),
            'gross': Decimal('0.00'),
            'gross_margin_pct': Decimal('0.00'),
        }

    # Add costs into breakdown
    for key, c_amt in costs_by_category.items():
        if key not in breakdown:
            breakdown[key] = {'revenue': Decimal('0.00'), 'costs': Decimal('0.00'), 'gross': Decimal('0.00'), 'gross_margin_pct': Decimal('0.00')}
        breakdown[key]['costs'] = c_amt
        breakdown[key]['gross'] = breakdown[key]['revenue'] - c_amt
        rev = breakdown[key]['revenue']
        breakdown[key]['gross_margin_pct'] = (breakdown[key]['gross'] / rev * 100) if rev and rev != Decimal('0.00') else Decimal('0.00')

    # Normalize breakdown keys to a nicer form
    breakdown_out = []
    for (cat_id, cat_code, cat_name), vals in breakdown.items():
        breakdown_out.append({
            'category_id': cat_id,
            'category_code': cat_code,
            'category_name': cat_name,
            'revenue': vals['revenue'],
            'costs': vals['costs'],
            'gross': vals['gross'],
            'gross_margin_pct': vals['gross_margin_pct'],
        })

    return {
        'base_currency': base_currency,
        'revenue': revenue,
        'costs': costs,
        'expenses': expenses,
        'gross_profit': gross_profit,
        'gross_margin_pct': gross_margin_pct,
        'net_profit': net_profit,
        'breakdown': breakdown_out,
    }


def cash_flow(start_date, end_date):
    """Return a simple cash flow summary for the period.

    Returns dict: { 'cash_in': Decimal, 'cash_out': Decimal, 'net_cash_flow': Decimal }
    """
    # Cash in: sum of completed payments in period
    cash_in = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        payment_status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Cash out: sum of expenses marked as paid in period
    cash_out = Expense.objects.filter(
        is_paid=True,
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    cash_in = Decimal(cash_in)
    cash_out = Decimal(cash_out)

    return {
        'cash_in': cash_in,
        'cash_out': cash_out,
        'net_cash_flow': cash_in - cash_out
    }


def trial_balance():
    """Return a list of accounts with their materialized balances for a trial balance."""
    rows = []
    for lb in LedgerBalance.objects.select_related('account').all().order_by('account__code'):
        rows.append({'code': lb.account.code, 'name': lb.account.name, 'balance': lb.balance})
    total = sum((row['balance'] for row in rows), Decimal('0.00'))
    return {'rows': rows, 'total': total}
