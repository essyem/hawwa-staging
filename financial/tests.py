from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from .models import Budget, BudgetLine, AccountingCategory, Expense, Invoice, InvoiceItem, LedgerAccount, JournalEntry, JournalLine


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
