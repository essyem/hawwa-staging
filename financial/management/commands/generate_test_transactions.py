"""
Django management command to generate test financial data for Hawwa Wellness project.
Creates 500+ transactions including invoices, payments, and expenses with proper app integration.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Import models from different apps
from financial.models import (
    AccountingCategory, TaxRate, Invoice, InvoiceItem, Payment, Expense,
    CurrencyRate, Budget, BudgetLine, LedgerAccount, JournalEntry, JournalLine
)
from services.models import Service, ServiceCategory
from bookings.models import Booking
from vendors.models import VendorProfile

# Try to import faker
try:
    from faker import Faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test financial data with proper app integration for Hawwa Wellness project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--transactions',
            type=int,
            default=500,
            help='Number of transactions to generate (default: 500)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before generating new data',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Number of test users to create (default: 100)',
        )
        parser.add_argument(
            '--services',
            type=int,
            default=50,
            help='Number of test services to create (default: 50)',
        )

    def handle(self, *args, **options):
        if not HAS_FAKER:
            raise CommandError(
                'Faker library is required for this command. '
                'Install it with: pip install faker'
            )

        self.faker = Faker(['en_US', 'ar_SA'])  # English and Arabic locales
        self.style = self.style
        self.options = options
        
        # Set random seed for reproducible results
        Faker.seed(12345)
        random.seed(12345)
        
        self.stdout.write(self.style.SUCCESS('Starting test data generation...'))
        
        if options['clear']:
            self.clear_test_data()
        
        # Generate data in proper order
        with transaction.atomic():
            self.create_accounting_categories()
            self.create_tax_rates()
            self.create_currency_rates()
            self.create_ledger_accounts()
            self.create_test_users(options['users'])
            self.create_service_categories()
            self.create_test_services(options['services'])
            self.create_test_bookings()
            self.create_budgets()
            self.create_invoices_and_transactions(options['transactions'])
            self.create_expenses()
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {options["transactions"]} transactions '
                f'with full app integration!'
            )
        )

    def clear_test_data(self):
        """Clear existing test data."""
        self.stdout.write('Clearing existing test data...')
        
        # Clear financial data
        JournalLine.objects.all().delete()
        JournalEntry.objects.all().delete()
        Payment.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        Expense.objects.all().delete()
        BudgetLine.objects.all().delete()
        Budget.objects.all().delete()
        
        # Clear bookings (but keep services/users as they might be real)
        Booking.objects.filter(booking_number__startswith='TEST-').delete()
        
        self.stdout.write(self.style.SUCCESS('Test data cleared'))

    def create_accounting_categories(self):
        """Create accounting categories for financial transactions."""
        self.stdout.write('Creating accounting categories...')
        
        categories = [
            ('SPA001', 'Spa Services', 'Revenue from spa and wellness services', False),
            ('MEAL001', 'Meal Services', 'Revenue from meal preparation and delivery', True),
            ('ACCOM001', 'Accommodation Services', 'Revenue from accommodation bookings', False),
            ('CARE001', 'Caretaker Services', 'Revenue from caretaker and support services', False),
            ('MENTAL001', 'Mental Health Services', 'Revenue from mental health consultations', False),
            ('MEDITATE001', 'Meditation Services', 'Revenue from meditation and mindfulness services', False),
            ('OFFICE001', 'Office Expenses', 'Office supplies and administrative costs', False),
            ('MARKETING001', 'Marketing Expenses', 'Marketing and promotional expenses', False),
            ('UTILITIES001', 'Utilities', 'Electricity, water, internet, phone bills', False),
            ('TRAVEL001', 'Travel Expenses', 'Business travel and transportation', False),
            ('EQUIPMENT001', 'Equipment', 'Medical equipment and spa facilities', False),
            ('SUPPLIES001', 'Medical Supplies', 'Medical and wellness supplies', True),
        ]
        
        for code, name, description, is_cogs in categories:
            AccountingCategory.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_cogs': is_cogs,
                    'is_active': True
                }
            )
        
        self.stdout.write(f'Created {len(categories)} accounting categories')

    def create_tax_rates(self):
        """Create tax rates for Qatar."""
        self.stdout.write('Creating tax rates...')
        
        # Qatar doesn't have VAT yet, but let's create some rates for testing
        tax_rates = [
            ('No Tax', Decimal('0.00'), 'No tax applicable'),
            ('Service Tax', Decimal('5.00'), 'Service tax for certain services'),
            ('Luxury Tax', Decimal('10.00'), 'Luxury tax for premium services'),
        ]
        
        for name, rate, description in tax_rates:
            TaxRate.objects.get_or_create(
                name=name,
                defaults={
                    'rate': rate,
                    'description': description,
                    'effective_from': timezone.now().date() - timedelta(days=365),
                    'is_active': True
                }
            )
        
        self.stdout.write(f'Created {len(tax_rates)} tax rates')

    def create_currency_rates(self):
        """Create currency exchange rates."""
        self.stdout.write('Creating currency rates...')
        
        # Current approximate exchange rates to QAR
        rates = [
            ('USD', 'QAR', Decimal('3.64')),
            ('EUR', 'QAR', Decimal('3.98')),
            ('GBP', 'QAR', Decimal('4.65')),
            ('AED', 'QAR', Decimal('0.99')),
            ('SAR', 'QAR', Decimal('0.97')),
            ('KWD', 'QAR', Decimal('11.98')),
            ('BHD', 'QAR', Decimal('9.65')),
        ]
        
        for from_curr, to_curr, rate in rates:
            CurrencyRate.objects.get_or_create(
                from_currency=from_curr,
                to_currency=to_curr,
                valid_from=timezone.now().date() - timedelta(days=30),
                defaults={'rate': rate}
            )
        
        self.stdout.write(f'Created {len(rates)} currency rates')

    def create_ledger_accounts(self):
        """Create chart of accounts for double-entry bookkeeping."""
        self.stdout.write('Creating ledger accounts...')
        
        accounts = [
            # Assets
            ('1001', 'Cash at Bank', 'asset'),
            ('1002', 'Accounts Receivable', 'asset'),
            ('1003', 'Inventory', 'asset'),
            ('1004', 'Equipment', 'asset'),
            
            # Liabilities
            ('2001', 'Accounts Payable', 'liability'),
            ('2002', 'Accrued Expenses', 'liability'),
            ('2003', 'Taxes Payable', 'liability'),
            
            # Equity
            ('3001', 'Owner Equity', 'equity'),
            ('3002', 'Retained Earnings', 'equity'),
            
            # Revenue
            ('4001', 'Service Revenue', 'revenue'),
            ('4002', 'Other Income', 'revenue'),
            
            # Expenses
            ('5001', 'Cost of Services', 'expense'),
            ('5002', 'Operating Expenses', 'expense'),
            ('5003', 'Marketing Expenses', 'expense'),
            ('5004', 'Administrative Expenses', 'expense'),
        ]
        
        for code, name, account_type in accounts:
            LedgerAccount.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'account_type': account_type,
                    'is_active': True
                }
            )
        
        self.stdout.write(f'Created {len(accounts)} ledger accounts')

    def create_test_users(self, count):
        """Create test users with different types."""
        self.stdout.write(f'Creating {count} test users...')
        
        user_types = [
            'MOTHER', 'ACCOMMODATION', 'CARETAKER', 'WELLNESS',
            'MEDITATION', 'MENTAL_HEALTH', 'FOOD', 'ADMIN'
        ]
        
        created_count = 0
        for i in range(count):
            email = self.faker.unique.email()
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='testpass123',
                    first_name=self.faker.first_name(),
                    last_name=self.faker.last_name(),
                    phone=self.faker.phone_number()[:20],
                    user_type=random.choice(user_types)
                )
                # Add address fields if they exist
                if hasattr(user, 'address'):
                    user.address = self.faker.address()
                    user.city = self.faker.city()
                    user.state = self.faker.state() if random.random() > 0.5 else ''
                    user.postal_code = self.faker.postcode()
                    user.country = random.choice(['Qatar', 'UAE', 'Saudi Arabia', 'Kuwait'])
                    user.save()
                
                created_count += 1
        
        self.stdout.write(f'Created {created_count} test users')

    def create_service_categories(self):
        """Create service categories."""
        self.stdout.write('Creating service categories...')
        
        categories = [
            ('Spa & Wellness', 'Spa treatments and wellness services', 'fa-spa'),
            ('Meal Services', 'Healthy meal preparation and delivery', 'fa-utensils'),
            ('Accommodation', 'Comfortable stay arrangements', 'fa-bed'),
            ('Caretaker Services', 'Personal care and assistance', 'fa-hands-helping'),
            ('Mental Health', 'Psychological counseling and support', 'fa-brain'),
            ('Meditation & Mindfulness', 'Meditation and mindfulness training', 'fa-om'),
            ('Fitness & Exercise', 'Physical fitness and exercise programs', 'fa-dumbbell'),
            ('Nutrition Consultation', 'Dietary advice and nutrition planning', 'fa-apple-alt'),
        ]
        
        for name, description, icon in categories:
            ServiceCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'icon': icon
                }
            )
        
        self.stdout.write(f'Created {len(categories)} service categories')

    def create_test_services(self, count):
        """Create test services."""
        self.stdout.write(f'Creating {count} test services...')
        
        categories = list(ServiceCategory.objects.all())
        
        # Service templates by category
        service_templates = {
            'Spa & Wellness': [
                ('Prenatal Massage', 'Relaxing massage for pregnant mothers', 180, 120),
                ('Aromatherapy Session', 'Essential oil therapy for relaxation', 150, 100),
                ('Hot Stone Therapy', 'Therapeutic hot stone massage', 220, 150),
                ('Facial Treatment', 'Rejuvenating facial for glowing skin', 160, 110),
                ('Reflexology', 'Foot massage and pressure point therapy', 130, 90),
            ],
            'Meal Services': [
                ('Healthy Meal Prep', 'Nutritious meal preparation service', 80, 50),
                ('Pregnancy Diet Plan', 'Customized meal planning for pregnant mothers', 120, 70),
                ('Postpartum Nutrition', 'Special meals for post-delivery recovery', 90, 55),
                ('Baby Food Preparation', 'Organic baby food making service', 60, 35),
                ('Family Meal Service', 'Healthy meals for the whole family', 100, 60),
            ],
            'Accommodation': [
                ('Maternity Suite', 'Comfortable suite for expecting mothers', 350, 200),
                ('Recovery Room', 'Private room for postpartum recovery', 280, 150),
                ('Family Accommodation', 'Family-friendly living space', 400, 220),
                ('Luxury Villa', 'Premium accommodation with full amenities', 600, 350),
            ],
            'Caretaker Services': [
                ('Personal Care Assistant', 'Professional personal care service', 200, 120),
                ('Baby Care Specialist', 'Specialized baby care and support', 250, 150),
                ('Night Care Service', 'Overnight care and assistance', 300, 180),
                ('Companion Service', 'Emotional support and companionship', 150, 90),
            ],
            'Mental Health': [
                ('Prenatal Counseling', 'Psychological support during pregnancy', 180, 120),
                ('Postpartum Depression Support', 'Therapy for postpartum depression', 200, 130),
                ('Family Counseling', 'Family therapy and relationship counseling', 220, 140),
                ('Stress Management', 'Techniques for managing stress and anxiety', 160, 100),
            ],
            'Meditation & Mindfulness': [
                ('Prenatal Yoga', 'Gentle yoga for pregnant mothers', 100, 60),
                ('Meditation Classes', 'Mindfulness and meditation training', 80, 50),
                ('Breathing Techniques', 'Breathing exercises for relaxation', 70, 45),
                ('Mindfulness Training', 'Comprehensive mindfulness program', 120, 75),
            ],
        }
        
        created_count = 0
        for category in categories:
            if category.name in service_templates:
                templates = service_templates[category.name]
                for name, description, price, cost in templates:
                    # Add some variation to prices and create multiple similar services
                    for variation in range(random.randint(1, 3)):
                        varied_name = f"{name}" if variation == 0 else f"{name} - {self.faker.word().title()}"
                        varied_price = Decimal(str(price)) + Decimal(str(random.randint(-20, 50)))
                        varied_cost = Decimal(str(cost)) + Decimal(str(random.randint(-10, 30)))
                        
                        service, created = Service.objects.get_or_create(
                            name=varied_name,
                            category=category,
                            defaults={
                                'description': description + ' - ' + self.faker.text(max_nb_chars=100),
                                'short_description': self.faker.sentence(nb_words=10),
                                'price': varied_price,
                                'cost': varied_cost,
                                'duration': timedelta(minutes=random.choice([30, 60, 90, 120, 180])),
                                'status': random.choice(['available', 'available', 'available', 'limited']),
                            }
                        )
                        if created:
                            created_count += 1
        
        self.stdout.write(f'Created {created_count} test services')

    def create_test_bookings(self):
        """Create test bookings to link with invoices."""
        self.stdout.write('Creating test bookings...')
        
        users = list(User.objects.all()[:50])  # Use first 50 users
        services = list(Service.objects.all())
        
        created_count = 0
        for i in range(100):  # Create 100 test bookings
            user = random.choice(users)
            service = random.choice(services)
            
            # Generate booking dates in the past 6 months
            start_date = self.faker.date_between(start_date='-180d', end_date='today')
            end_date = start_date + timedelta(days=random.randint(1, 7))
            
            booking = Booking.objects.create(
                booking_number=f'TEST-{self.faker.unique.random_int(min=10000, max=99999)}',
                user=user,
                service=service,
                start_date=start_date,
                end_date=end_date,
                start_time=self.faker.time(),
                end_time=self.faker.time(),
                address=self.faker.address(),
                city=self.faker.city(),
                postal_code=self.faker.postcode(),
                base_price=service.price,
                total_price=service.price,
                status=random.choice(['confirmed', 'completed', 'completed', 'completed']),
                priority=random.choice(['normal', 'normal', 'high']),
                client_phone=self.faker.phone_number()[:20],
                client_email=user.email,
                special_instructions=self.faker.text(max_nb_chars=200) if random.random() > 0.7 else '',
                notes=self.faker.text(max_nb_chars=150) if random.random() > 0.8 else ''
            )
            created_count += 1
        
        self.stdout.write(f'Created {created_count} test bookings')

    def create_budgets(self):
        """Create sample budgets."""
        self.stdout.write('Creating budgets...')
        
        categories = list(AccountingCategory.objects.all())
        
        # Create quarterly budgets
        for quarter in range(1, 5):
            start_date = timezone.now().date().replace(month=(quarter-1)*3+1, day=1)
            end_date = start_date.replace(month=quarter*3, day=28)
            
            budget = Budget.objects.create(
                name=f'Q{quarter} 2024 Budget',
                start_date=start_date,
                end_date=end_date,
                currency='QAR'
            )
            
            # Create budget lines
            for category in random.sample(categories, k=min(5, len(categories))):
                BudgetLine.objects.create(
                    budget=budget,
                    name=f'{category.name} Budget',
                    category=category,
                    amount=Decimal(str(random.randint(10000, 50000))),
                    notes=f'Quarterly budget allocation for {category.name}'
                )
        
        self.stdout.write('Created quarterly budgets')

    def create_invoices_and_transactions(self, transaction_count):
        """Create invoices with line items and payments."""
        self.stdout.write(f'Creating {transaction_count} financial transactions...')
        
        users = list(User.objects.all())
        services = list(Service.objects.all())
        bookings = list(Booking.objects.all())
        categories = list(AccountingCategory.objects.all())
        tax_rates = list(TaxRate.objects.all())
        
        invoices_created = 0
        payments_created = 0
        
        for i in range(transaction_count // 2):  # Create half as invoices, rest as expenses
            # Select random data
            customer = random.choice(users)
            booking = random.choice(bookings) if bookings and random.random() > 0.3 else None
            
            # Create invoice
            invoice_date = self.faker.date_between(start_date='-180d', end_date='today')
            due_date = invoice_date + timedelta(days=random.choice([15, 30, 45]))
            
            invoice = Invoice.objects.create(
                customer=customer,
                booking=booking,
                invoice_type=random.choice(['booking', 'service', 'subscription', 'custom']),
                status=random.choice(['draft', 'sent', 'paid', 'paid', 'paid', 'partially_paid']),
                invoice_date=invoice_date,
                due_date=due_date,
                billing_name=customer.get_full_name() or customer.email,
                billing_email=customer.email,
                billing_phone=getattr(customer, 'phone', ''),
                billing_address=getattr(customer, 'address', None) or self.faker.address(),
                billing_city=getattr(customer, 'city', None) or self.faker.city(),
                billing_postal_code=getattr(customer, 'postal_code', None) or self.faker.postcode(),
                billing_country=getattr(customer, 'country', None) or 'Qatar',
                notes=self.faker.text(max_nb_chars=200) if random.random() > 0.7 else '',
            )
            
            # Create invoice items
            item_count = random.randint(1, 4)
            for _ in range(item_count):
                service = random.choice(services)
                quantity = Decimal(str(random.choice([1, 1, 1, 2, 3])))
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    service=service,
                    description=service.name + (' - ' + self.faker.sentence(nb_words=4) if random.random() > 0.5 else ''),
                    quantity=quantity,
                    unit_price=service.price,
                    discount_percentage=Decimal(str(random.choice([0, 0, 0, 5, 10, 15]))),
                    category=random.choice(categories),
                    cost_amount=service.cost * quantity if hasattr(service, 'cost') else Decimal('0'),
                    cost_currency='QAR'
                )
            
            # Apply tax if needed
            if random.random() > 0.7:  # 30% chance of tax
                tax_rate = random.choice(tax_rates)
                invoice._tax_rate = tax_rate.rate
            
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            invoices_created += 1
            
            # Create payments for paid/partially paid invoices
            if invoice.status in ['paid', 'partially_paid']:
                if invoice.status == 'paid':
                    # Full payment
                    payment_amount = invoice.total_amount
                else:
                    # Partial payment
                    payment_amount = invoice.total_amount * Decimal(str(random.uniform(0.3, 0.8)))
                
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=payment_amount,
                    payment_method=random.choice(['cash', 'bank_transfer', 'credit_card', 'online_payment']),
                    payment_status='completed',
                    payment_date=timezone.make_aware(datetime.combine(
                        invoice_date + timedelta(days=random.randint(1, 15)), 
                        timezone.now().time()
                    )),
                    transaction_reference=f'TXN-{self.faker.unique.random_int(min=100000, max=999999)}',
                    notes=self.faker.sentence() if random.random() > 0.8 else ''
                )
                payments_created += 1
            
            # Create journal entries for completed transactions
            if invoice.status == 'paid':
                self.create_journal_entry_for_invoice(invoice)
        
        self.stdout.write(f'Created {invoices_created} invoices and {payments_created} payments')

    def create_expenses(self):
        """Create business expenses."""
        self.stdout.write('Creating business expenses...')
        
        categories = list(AccountingCategory.objects.all())
        users = list(User.objects.filter(user_type='ADMIN')[:5])  # Admin users as creators
        
        expense_types = [
            'operational', 'marketing', 'equipment', 'supplies', 
            'utilities', 'travel', 'professional_services'
        ]
        
        expenses_created = 0
        for i in range(self.options['transactions'] // 2):  # Create half as many expenses as invoices
            expense_date = self.faker.date_between(start_date='-180d', end_date='today')
            
            expense = Expense.objects.create(
                description=self.faker.sentence(nb_words=6),
                amount=Decimal(str(random.uniform(50, 2000))),
                expense_type=random.choice(expense_types),
                category=random.choice(categories),
                vendor_name=self.faker.company(),
                vendor_email=self.faker.email() if random.random() > 0.5 else '',
                vendor_phone=self.faker.phone_number()[:20] if random.random() > 0.5 else '',
                expense_date=expense_date,
                is_approved=random.random() > 0.2,  # 80% approved
                is_paid=random.random() > 0.3,  # 70% paid
                payment_date=expense_date + timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
                notes=self.faker.text(max_nb_chars=200) if random.random() > 0.7 else '',
                created_by=random.choice(users) if users else None
            )
            expenses_created += 1
            
            # Create journal entries for paid expenses
            if expense.is_paid:
                self.create_journal_entry_for_expense(expense)
        
        self.stdout.write(f'Created {expenses_created} business expenses')

    def create_journal_entry_for_invoice(self, invoice):
        """Create double-entry journal entry for paid invoice."""
        # Get ledger accounts
        cash_account = LedgerAccount.objects.get(code='1001')  # Cash at Bank
        revenue_account = LedgerAccount.objects.get(code='4001')  # Service Revenue
        
        # Create journal entry
        entry = JournalEntry.objects.create(
            reference=f'INV-{invoice.invoice_number}',
            date=invoice.paid_date.date() if invoice.paid_date else invoice.invoice_date,
            narration=f'Payment received for invoice {invoice.invoice_number}'
        )
        
        # Debit Cash (Asset increases)
        JournalLine.objects.create(
            entry=entry,
            account=cash_account,
            debit=invoice.total_amount,
            credit=Decimal('0.00'),
            narration=f'Cash received from {invoice.customer.get_full_name()}'
        )
        
        # Credit Revenue (Revenue increases)
        JournalLine.objects.create(
            entry=entry,
            account=revenue_account,
            debit=Decimal('0.00'),
            credit=invoice.total_amount,
            narration=f'Service revenue from invoice {invoice.invoice_number}'
        )

    def create_journal_entry_for_expense(self, expense):
        """Create double-entry journal entry for paid expense."""
        # Get ledger accounts
        cash_account = LedgerAccount.objects.get(code='1001')  # Cash at Bank
        expense_account = LedgerAccount.objects.get(code='5002')  # Operating Expenses
        
        # Create journal entry
        entry = JournalEntry.objects.create(
            reference=f'EXP-{expense.id}',
            date=expense.payment_date or expense.expense_date,
            narration=f'Payment for expense: {expense.description}'
        )
        
        # Debit Expense (Expense increases)
        JournalLine.objects.create(
            entry=entry,
            account=expense_account,
            debit=expense.amount,
            credit=Decimal('0.00'),
            narration=expense.description
        )
        
        # Credit Cash (Asset decreases)
        JournalLine.objects.create(
            entry=entry,
            account=cash_account,
            debit=Decimal('0.00'),
            credit=expense.amount,
            narration=f'Cash paid to {expense.vendor_name}'
        )