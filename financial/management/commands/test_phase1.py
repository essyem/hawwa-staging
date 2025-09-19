from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from decimal import Decimal

from accounts.models import User
from services.models import Service
from bookings.models import Booking
from financial.models import (
    AccountingCategory, TaxRate, Invoice, InvoiceItem, 
    Payment, Expense
)

class Command(BaseCommand):
    help = 'Test Phase 1 Financial Module implementation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample financial data for testing',
        )
        parser.add_argument(
            '--test-invoice-generation',
            action='store_true',
            help='Test automated invoice generation from bookings',
        )
        parser.add_argument(
            '--show-statistics',
            action='store_true',
            help='Show current financial statistics',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Hawwa Phase 1 Financial Module Test ==='))
        
        if options['create_sample_data']:
            self.create_sample_data()
        
        if options['test_invoice_generation']:
            self.test_invoice_generation()
            
        if options['show_statistics']:
            self.show_statistics()
        
        if not any(options.values()):
            self.show_help()
    
    def create_sample_data(self):
        """Create sample financial data for testing."""
        self.stdout.write(self.style.HTTP_INFO('Creating sample financial data...'))
        
        # Create accounting categories
        categories = [
            ('SRV001', 'Service Revenue', 'Revenue from service bookings'),
            ('EXP001', 'Operating Expenses', 'General operating expenses'),
            ('EXP002', 'Marketing Expenses', 'Marketing and advertising costs'),
        ]
        
        for code, name, desc in categories:
            category, created = AccountingCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if created:
                self.stdout.write(f'  ✓ Created category: {category}')
        
        # Create tax rates
        tax_rate, created = TaxRate.objects.get_or_create(
            name='Qatar VAT',
            defaults={
                'rate': Decimal('5.00'),
                'effective_from': timezone.now().date(),
                'description': 'Qatar Value Added Tax'
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created tax rate: {tax_rate}')
        
        # Create sample expense
        if not Expense.objects.exists():
            # Get or create a staff user for the expense
            staff_user = User.objects.filter(is_staff=True).first()
            if staff_user:
                expense = Expense.objects.create(
                    description='Office supplies and equipment',
                    amount=Decimal('1500.00'),
                    expense_type='operational',
                    vendor_name='Qatar Office Supplies Co.',
                    vendor_email='sales@qataroffice.com',
                    expense_date=timezone.now().date(),
                    created_by=staff_user,
                    category=AccountingCategory.objects.filter(code='EXP001').first()
                )
                self.stdout.write(f'  ✓ Created sample expense: {expense}')
        
        self.stdout.write(self.style.SUCCESS('Sample data creation completed!'))
    
    def test_invoice_generation(self):
        """Test automated invoice generation from bookings."""
        self.stdout.write(self.style.HTTP_INFO('Testing invoice generation...'))
        
        # Find bookings without invoices
        bookings_without_invoices = Booking.objects.filter(
            invoices__isnull=True,
            status='confirmed'
        )[:3]  # Test with first 3 confirmed bookings
        
        if not bookings_without_invoices.exists():
            self.stdout.write(self.style.WARNING('No confirmed bookings found without invoices.'))
            return
        
        service_category = AccountingCategory.objects.filter(code='SRV001').first()
        tax_rate = TaxRate.objects.filter(is_active=True).first()
        
        for booking in bookings_without_invoices:
            try:
                # Create invoice from booking
                invoice = Invoice.objects.create(
                    customer=booking.user,
                    booking=booking,
                    invoice_type='service',
                    status='draft',
                    invoice_date=timezone.now().date(),
                    due_date=timezone.now().date() + timedelta(days=30),
                    billing_name=booking.user.get_full_name() or booking.user.email,
                    billing_email=booking.user.email,
                    billing_address=getattr(booking, 'address', 'Address not provided'),
                    billing_city=getattr(booking, 'city', 'Doha'),
                    billing_postal_code=getattr(booking, 'postal_code', '00000'),
                    notes=f'Service booking: {booking.service.name}',
                    created_by=booking.user,
                    # Set basic amounts to avoid calculation issues
                    subtotal=booking.service.price,
                    total_amount=booking.service.price,
                    balance_due=booking.service.price
                )
                
                # Refresh from database to ensure we have the primary key
                invoice.refresh_from_db()
                
                # Create invoice item
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    description=f'{booking.service.name} - {booking.service.description}',
                    service=booking.service,
                    quantity=1,
                    unit_price=booking.service.price,
                    category=service_category
                )
                
                # Now recalculate totals properly
                invoice.calculate_totals()
                invoice.save()
                
                self.stdout.write(f'  ✓ Generated invoice {invoice.invoice_number} for booking {booking.id}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to generate invoice for booking {booking.id}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('Invoice generation test completed!'))
    
    def show_statistics(self):
        """Show current financial statistics."""
        self.stdout.write(self.style.HTTP_INFO('Current Financial Statistics:'))
        
        # Invoice statistics
        total_invoices = Invoice.objects.count()
        draft_invoices = Invoice.objects.filter(status='draft').count()
        sent_invoices = Invoice.objects.filter(status='sent').count()
        paid_invoices = Invoice.objects.filter(status='paid').count()
        
        total_revenue = Invoice.objects.filter(status='paid').aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        pending_revenue = Invoice.objects.filter(
            status__in=['sent', 'pending']
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        self.stdout.write(f'  📊 Total Invoices: {total_invoices}')
        self.stdout.write(f'     - Draft: {draft_invoices}')
        self.stdout.write(f'     - Sent: {sent_invoices}')
        self.stdout.write(f'     - Paid: {paid_invoices}')
        self.stdout.write(f'  💰 Total Revenue: QAR {total_revenue:.2f}')
        self.stdout.write(f'  ⏳ Pending Revenue: QAR {pending_revenue:.2f}')
        
        # Payment statistics
        total_payments = Payment.objects.count()
        completed_payments = Payment.objects.filter(payment_status='completed').count()
        
        self.stdout.write(f'  💳 Total Payments: {total_payments}')
        self.stdout.write(f'     - Completed: {completed_payments}')
        
        # Expense statistics
        total_expenses = Expense.objects.count()
        approved_expenses = Expense.objects.filter(is_approved=True).count()
        paid_expenses = Expense.objects.filter(is_paid=True).count()
        
        total_expense_amount = Expense.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.stdout.write(f'  📋 Total Expenses: {total_expenses}')
        self.stdout.write(f'     - Approved: {approved_expenses}')
        self.stdout.write(f'     - Paid: {paid_expenses}')
        self.stdout.write(f'  💸 Total Expense Amount: QAR {total_expense_amount:.2f}')
        
        # Categories and Tax Rates
        categories_count = AccountingCategory.objects.count()
        tax_rates_count = TaxRate.objects.count()
        
        self.stdout.write(f'  📂 Accounting Categories: {categories_count}')
        self.stdout.write(f'  📊 Tax Rates: {tax_rates_count}')
        
        self.stdout.write(self.style.SUCCESS('Statistics display completed!'))
    
    def show_help(self):
        """Show available commands."""
        self.stdout.write('Available options:')
        self.stdout.write('  --create-sample-data      Create sample financial data')
        self.stdout.write('  --test-invoice-generation Test automated invoice generation')
        self.stdout.write('  --show-statistics         Show financial statistics')
        self.stdout.write('')
        self.stdout.write('Example usage:')
        self.stdout.write('  python manage.py test_phase1 --create-sample-data')
        self.stdout.write('  python manage.py test_phase1 --test-invoice-generation')
        self.stdout.write('  python manage.py test_phase1 --show-statistics')