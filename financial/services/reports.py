from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from ..models import Invoice, InvoiceItem, Payment, Expense

from ..models import LedgerBalance, LedgerAccount


def profit_and_loss(start_date, end_date):
    """Return a simple Profit & Loss summary for the period.

    Returns dict: { 'revenue': Decimal, 'costs': Decimal, 'expenses': Decimal, 'gross_profit': Decimal, 'net_profit': Decimal }
    """
    # Revenue: sum of invoice items for invoices in period
    invoice_sum = InvoiceItem.objects.filter(
        invoice__invoice_date__gte=start_date,
        invoice__invoice_date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Costs: placeholder - invoices may have cost-of-goods lines marked by category or negative amounts
    # For now assume costs = 0.00 (extend later to support cost categories)
    costs = Decimal('0.00')

    # Expenses: sum of Expense.amount in period
    expense_sum = Expense.objects.filter(
        expense_date__gte=start_date,
        expense_date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    revenue = Decimal(invoice_sum)
    expenses = Decimal(expense_sum)
    gross_profit = revenue - costs
    net_profit = gross_profit - expenses

    return {
        'revenue': revenue,
        'costs': costs,
        'expenses': expenses,
        'gross_profit': gross_profit,
        'net_profit': net_profit
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
