from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from ..models import LedgerAccount, JournalEntry, JournalLine
from ..models import LedgerBalance


DEFAULT_ACCOUNTS = {
    'cash': '1000',
    'revenue': '4000',
    'expense': '5000',
}


def _get_or_create_account(code, name):
    # Determine sensible default account_type for common codes
    ACCOUNT_TYPE_BY_CODE = {
        DEFAULT_ACCOUNTS['cash']: 'asset',
        DEFAULT_ACCOUNTS['revenue']: 'revenue',
        DEFAULT_ACCOUNTS['expense']: 'expense',
    }
    defaults = {'name': name}
    acct_type = ACCOUNT_TYPE_BY_CODE.get(code)
    if acct_type:
        defaults['account_type'] = acct_type
    acct, created = LedgerAccount.objects.get_or_create(code=code, defaults=defaults)
    return acct


def create_payment_journal(payment):
    """Create a journal entry for a completed payment.

    Debit Cash, Credit Revenue
    """
    # Avoid duplicates by using reference
    ref = f"payment:{payment.id}"
    if JournalEntry.objects.filter(reference=ref).exists():
        return None

    cash_code = DEFAULT_ACCOUNTS['cash']
    rev_code = DEFAULT_ACCOUNTS['revenue']

    cash_acct = _get_or_create_account(cash_code, 'Cash')
    rev_acct = _get_or_create_account(rev_code, 'Revenue')

    with transaction.atomic():
        je = JournalEntry.objects.create(reference=ref, date=payment.payment_date.date() if hasattr(payment.payment_date, 'date') else timezone.now().date(), narration=f"Payment {payment.id}", created_by=payment.processed_by)
        # Debit Cash
        jl_debit = JournalLine.objects.create(entry=je, account=cash_acct, debit=Decimal(payment.amount), credit=Decimal('0.00'), narration=f"Payment {payment.id}")
        # Credit Revenue
        jl_credit = JournalLine.objects.create(entry=je, account=rev_acct, debit=Decimal('0.00'), credit=Decimal(payment.amount), narration=f"Payment {payment.id}")
        # Update balances
        _apply_line_to_balance(jl_debit)
        _apply_line_to_balance(jl_credit)
        # Validate
        if not je.is_balanced():
            raise ValueError('Created journal entry not balanced')
    return je


def create_expense_journal(expense):
    """Create a journal entry when an expense is paid.

    Debit Expense account, Credit Cash
    """
    ref = f"expense:{expense.id}"
    if JournalEntry.objects.filter(reference=ref).exists():
        return None

    cash_code = DEFAULT_ACCOUNTS['cash']
    exp_code = DEFAULT_ACCOUNTS['expense']

    cash_acct = _get_or_create_account(cash_code, 'Cash')
    exp_acct = _get_or_create_account(exp_code, 'Expenses')

    with transaction.atomic():
        je = JournalEntry.objects.create(reference=ref, date=expense.payment_date or timezone.now().date(), narration=f"Expense {expense.id}", created_by=expense.created_by)
        # Debit Expense
        jl_debit = JournalLine.objects.create(entry=je, account=exp_acct, debit=Decimal(expense.amount), credit=Decimal('0.00'), narration=f"Expense {expense.id}")
        # Credit Cash
        jl_credit = JournalLine.objects.create(entry=je, account=cash_acct, debit=Decimal('0.00'), credit=Decimal(expense.amount), narration=f"Expense {expense.id}")
        # Update balances
        _apply_line_to_balance(jl_debit)
        _apply_line_to_balance(jl_credit)
        if not je.is_balanced():
            raise ValueError('Created journal entry not balanced')
    return je


def _apply_line_to_balance(journal_line):
    """Apply a JournalLine to the materialized LedgerBalance."""
    acct = journal_line.account
    debit = Decimal(journal_line.debit)
    credit = Decimal(journal_line.credit)
    raw_amount = debit - credit

    lb, created = LedgerBalance.objects.select_for_update().get_or_create(account=acct, defaults={'balance': Decimal('0.00')})

    # Natural sign: Assets and Expenses have debit-normal balances (debit increases),
    # Liabilities, Equity, Revenue have credit-normal balances (credit increases).
    if acct.account_type in ('asset', 'expense'):
        # Increase balance by (debit - credit)
        lb.balance = Decimal(lb.balance) + raw_amount
    else:
        # For credit-normal accounts, balance := balance + (credit - debit)
        lb.balance = Decimal(lb.balance) + (credit - debit)

    lb.save()
