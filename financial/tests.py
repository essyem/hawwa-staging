from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from .models import Budget, BudgetLine, AccountingCategory, Expense, Invoice, InvoiceItem, LedgerAccount, JournalEntry, JournalLine, Payment
from .services.reports import profit_and_loss, cash_flow
from .services.posting import create_payment_journal, create_expense_journal


class BudgetTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(email='test@example.com', password='password')

		# Create an accounting category
		self.cat = AccountingCategory.objects.create(name='Operations', code='OPS')

		# Create a budget for this month
		today = date.today()
		start = today.replace(day=1)
		end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

		self.budget = Budget.objects.create(
			name='Monthly Ops', start_date=start, end_date=end, created_by=self.user
		)

		self.line = BudgetLine.objects.create(
			budget=self.budget, name='Ops Line', category=self.cat, amount=Decimal('10000.00')
		)

	def test_budget_allocated(self):
		self.assertEqual(self.budget.total_allocated(), Decimal('10000.00'))

	def test_budget_spent_from_expense(self):
		# Create an expense within budget period
		Expense.objects.create(
			description='Office Supplies', amount=Decimal('250.00'), expense_type='supplies',
			category=self.cat, expense_date=self.budget.start_date, created_by=self.user
		)

		self.assertEqual(self.budget.total_spent(), Decimal('250.00'))

	def test_budget_spent_from_invoice_items(self):
		# Create an invoice and invoice item within budget period
		invoice = Invoice.objects.create(
			invoice_number='TEST-1', customer=self.user, invoice_date=self.budget.start_date,
			due_date=self.budget.end_date, billing_name='Test', billing_email='test@example.com', billing_address='Addr', billing_city='City', billing_postal_code='0000'
		)
		InvoiceItem.objects.create(invoice=invoice, description='Service Fee', quantity=1, unit_price=Decimal('500.00'), category=self.cat)

		# Recalculate totals saved by invoice item save
		invoice.calculate_totals()
		invoice.save()

		self.assertEqual(self.budget.total_spent(), Decimal('500.00'))

	def test_budget_remaining(self):
		# Add an expense and check remaining
		Expense.objects.create(
			description='Small Expense', amount=Decimal('1000.00'), expense_type='operational',
			category=self.cat, expense_date=self.budget.start_date, created_by=self.user
		)
		rem = self.budget.remaining()
		self.assertEqual(rem, Decimal('9000.00'))


class LedgerTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(email='acct@example.com', password='password')
		# Create ledger accounts
		self.cash = LedgerAccount.objects.create(code='1000', name='Cash')
		self.revenue = LedgerAccount.objects.create(code='4000', name='Revenue')

	def test_journal_entry_balanced_post(self):
		je = JournalEntry.objects.create(reference='TXN-1', date=date.today(), narration='Test')
		JournalLine.objects.create(entry=je, account=self.cash, debit=Decimal('100.00'))
		JournalLine.objects.create(entry=je, account=self.revenue, credit=Decimal('100.00'))

		self.assertTrue(je.is_balanced())
		self.assertTrue(je.post())

	def test_journal_entry_unbalanced_fails(self):
		je = JournalEntry.objects.create(reference='TXN-2', date=date.today(), narration='Unbalanced')
		JournalLine.objects.create(entry=je, account=self.cash, debit=Decimal('100.00'))
		JournalLine.objects.create(entry=je, account=self.revenue, credit=Decimal('50.00'))

		self.assertFalse(je.is_balanced())
		with self.assertRaises(ValueError):
			je.post()


class ReportsTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(email='report@example.com', password='password')
		self.cat = AccountingCategory.objects.create(name='Service', code='SVC')
		today = date.today()
		start = today.replace(day=1)
		end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
		# Invoice and payment
		self.invoice = Invoice.objects.create(
			invoice_number='R-1', customer=self.user, invoice_date=start, due_date=end,
			billing_name='Rep', billing_email='report@example.com', billing_address='Addr', billing_city='City', billing_postal_code='0000'
		)
		InvoiceItem.objects.create(invoice=self.invoice, description='Service Fee', quantity=1, unit_price=Decimal('1200.00'), category=self.cat)
		# Mark payment completed
		Payment.objects.create(invoice=self.invoice, amount=Decimal('1200.00'), payment_method='bank_transfer', payment_status='completed', payment_date=start)

		# Expense paid
		Expense.objects.create(description='Hosting', amount=Decimal('200.00'), expense_type='operational', category=self.cat, expense_date=start, is_paid=True, payment_date=start, created_by=self.user)

	def test_profit_and_loss(self):
		today = date.today()
		start = today.replace(day=1)
		end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
		pl = profit_and_loss(start, end)
		self.assertEqual(pl['revenue'], Decimal('1200.00'))
		self.assertEqual(pl['expenses'], Decimal('200.00'))
		self.assertEqual(pl['net_profit'], Decimal('1000.00'))

	def test_cash_flow(self):
		today = date.today()
		start = today.replace(day=1)
		end = (start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
		cf = cash_flow(start, end)
		self.assertEqual(cf['cash_in'], Decimal('1200.00'))
		self.assertEqual(cf['cash_out'], Decimal('200.00'))
		self.assertEqual(cf['net_cash_flow'], Decimal('1000.00'))


class PostingSignalsTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(email='post@example.com', password='password')
		self.cat = AccountingCategory.objects.create(name='Service', code='SVC2')
		# Create initial ledger accounts if not present
		from .services.posting import _get_or_create_account
		_get_or_create_account('1000', 'Cash')
		_get_or_create_account('4000', 'Revenue')
		_get_or_create_account('5000', 'Expenses')

	def test_payment_triggers_journal(self):
		invoice = Invoice.objects.create(invoice_number='P-1', customer=self.user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
		payment = Payment.objects.create(invoice=invoice, amount=Decimal('300.00'), payment_method='bank_transfer', payment_status='completed', payment_date=timezone.now())
		# JournalEntry with reference payment:{id} created
		ref = f"payment:{payment.id}"
		je = JournalEntry.objects.filter(reference=ref).first()
		self.assertIsNotNone(je)
		self.assertTrue(je.is_balanced())

	def test_expense_triggers_journal(self):
		expense = Expense.objects.create(description='TestE', amount=Decimal('150.00'), expense_type='operational', category=self.cat, expense_date=date.today(), is_paid=True, payment_date=timezone.now(), created_by=self.user)
		ref = f"expense:{expense.id}"
		je = JournalEntry.objects.filter(reference=ref).first()
		self.assertIsNotNone(je)
		self.assertTrue(je.is_balanced())


class MaterializedBalanceTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(email='bal@example.com', password='password')
		from .services.posting import _get_or_create_account
		self.cash = _get_or_create_account('1000', 'Cash')
		self.rev = _get_or_create_account('4000', 'Revenue')

	def test_balances_updated_on_payment(self):
		invoice = Invoice.objects.create(invoice_number='MB-1', customer=self.user, invoice_date=date.today(), due_date=date.today(), billing_name='B', billing_email='b@x.com', billing_address='a', billing_city='c', billing_postal_code='000')
		payment = Payment.objects.create(invoice=invoice, amount=Decimal('500.00'), payment_method='bank_transfer', payment_status='completed', payment_date=timezone.now())
		# Check LedgerBalance
		from .models import LedgerBalance
		lb_cash = LedgerBalance.objects.get(account__code='1000')
		lb_rev = LedgerBalance.objects.get(account__code='4000')
		# Cash should have increased by 500, revenue decreased by -500 (credit)
		self.assertEqual(lb_cash.balance, Decimal('500.00'))
		self.assertEqual(lb_rev.balance, Decimal('-500.00'))

	def test_trial_balance_report(self):
		from .services.reports import trial_balance
		tb = trial_balance()
		self.assertIn('rows', tb)
		self.assertIn('total', tb)
