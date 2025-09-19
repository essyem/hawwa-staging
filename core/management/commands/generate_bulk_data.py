"""
Comprehensive bulk data generation command for all Hawwa apps
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta, time, date
import random
import uuid
from faker import Faker

# Import all models
from accounts.models import User
from services.models import (
    ServiceCategory, Service, AccommodationService, HomeCareService,
    WellnessService, NutritionService, ServiceReview, ServiceImage
)
from vendors.models import (
    VendorProfile, VendorDocument, VendorAvailability, VendorBlackoutDate,
    VendorPayment, VendorAnalytics
)
from bookings.models import (
    Booking, BookingItem, BookingStatusHistory, BookingPayment
)

# Import analytics models
from analytics.models import (
    QualityScore, PerformanceMetrics, VendorRanking, QualityCertification,
    VendorAvailability as AnalyticsVendorAvailability,
    VendorWorkload, VendorAssignment, AssignmentPreference, AssignmentLog
)

# Try to import optional models (may not exist in all setups)
try:
    from operations.models import WorkflowTemplate, WorkflowInstance
    HAS_OPERATIONS = True
except ImportError:
    HAS_OPERATIONS = False

try:
    from payments.models import Currency, PaymentMethod, Payment
    HAS_PAYMENTS = True
except ImportError:
    HAS_PAYMENTS = False

try:
    from financial.models import Invoice, FinancialAccount, Transaction
    HAS_FINANCIAL = True
except ImportError:
    HAS_FINANCIAL = False

try:
    from wellness.models import WellnessProgram, WellnessSession, ProgressTracking
    HAS_WELLNESS = True
except ImportError:
    HAS_WELLNESS = False

try:
    from reporting.models import Report, ReportTemplate
    HAS_REPORTING = True
except ImportError:
    HAS_REPORTING = False

User = get_user_model()
fake = Faker(['en_US'])

class Command(BaseCommand):
    help = 'Generate comprehensive bulk test data for all Hawwa apps'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=100,
            help='Number of users to create (default: 100)'
        )
        parser.add_argument(
            '--vendors',
            type=int,
            default=30,
            help='Number of vendor profiles to create (default: 30)'
        )
        parser.add_argument(
            '--services',
            type=int,
            default=50,
            help='Number of services to create (default: 50)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=200,
            help='Number of bookings to create (default: 200)'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=90,
            help='Number of days back to generate data (default: 90)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test data before generating new data'
        )
    
    def handle(self, *args, **options):
        self.users_count = options['users']
        self.vendors_count = options['vendors']
        self.services_count = options['services']
        self.bookings_count = options['bookings']
        self.days_back = options['days_back']
        self.clean_data = options['clean']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting comprehensive bulk data generation...')
        )
        
        if self.clean_data:
            self._clean_test_data()
        
        with transaction.atomic():
            # Phase 1: Core Data
            self.stdout.write('📊 Phase 1: Creating core reference data...')
            if HAS_PAYMENTS:
                self._create_currencies()
                self._create_payment_methods()
            self._create_service_categories()
            if HAS_OPERATIONS:
                self._create_workflow_templates()
            if HAS_REPORTING:
                self._create_report_templates()
            
            # Phase 2: Users and Vendors
            self.stdout.write('👥 Phase 2: Creating users and vendor profiles...')
            self._create_users()
            self._create_vendor_profiles()
            self._create_vendor_documents()
            self._create_vendor_availability()
            
            # Phase 3: Services
            self.stdout.write('🏥 Phase 3: Creating services and wellness programs...')
            self._create_services()
            if HAS_WELLNESS:
                self._create_wellness_programs()
            
            # Phase 4: Bookings and Operations
            self.stdout.write('📅 Phase 4: Creating bookings and operational data...')
            self._create_bookings()
            if HAS_OPERATIONS:
                self._create_workflow_instances()
            
            # Phase 5: Financial Data
            self.stdout.write('💰 Phase 5: Creating financial and payment data...')
            if HAS_FINANCIAL:
                self._create_financial_accounts()
            if HAS_PAYMENTS:
                self._create_payments()
            if HAS_FINANCIAL:
                self._create_invoices()
            self._create_vendor_payments()
            
            # Phase 6: Analytics Data
            self.stdout.write('📈 Phase 6: Creating analytics and performance data...')
            self._create_quality_scores()
            self._create_performance_metrics()
            self._create_vendor_rankings()
            # Note: Smart vendor assignment system models not yet implemented
            # self._create_assignment_data()
            self.stdout.write('  ⚠️ Smart vendor assignment data creation skipped (models not implemented)')
            
            # Phase 7: Reviews and Feedback
            self.stdout.write('⭐ Phase 7: Creating reviews and feedback...')
            self._create_service_reviews()
            if HAS_WELLNESS:
                self._create_wellness_sessions()
            
            # Phase 8: Reports
            if HAS_REPORTING:
                self.stdout.write('📋 Phase 8: Creating reports and analytics...')
                self._create_reports()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Bulk data generation completed successfully!')
        )
        self._print_summary()
    
    def _clean_test_data(self):
        """Clean existing test data"""
        self.stdout.write('🧹 Cleaning existing test data...')
        
        # Clean in reverse dependency order
        AssignmentLog.objects.all().delete()
        VendorAssignment.objects.all().delete()
        VendorWorkload.objects.all().delete()
        AnalyticsVendorAvailability.objects.all().delete()
        
        QualityCertification.objects.all().delete()
        VendorRanking.objects.all().delete()
        PerformanceMetrics.objects.all().delete()
        QualityScore.objects.all().delete()
        
        ServiceReview.objects.all().delete()
        BookingPayment.objects.all().delete()
        BookingStatusHistory.objects.all().delete()
        BookingItem.objects.all().delete()
        Booking.objects.all().delete()
        
        VendorPayment.objects.all().delete()
        VendorBlackoutDate.objects.all().delete()
        VendorAvailability.objects.all().delete()
        VendorDocument.objects.all().delete()
        VendorProfile.objects.all().delete()
        
        Service.objects.all().delete()
        ServiceCategory.objects.all().delete()
        
        # Keep admin users, clean test users
        User.objects.filter(is_staff=False, is_superuser=False).delete()
        
        self.stdout.write('✅ Test data cleaned')
    
    def _create_currencies(self):
        """Create currency data"""
        if not HAS_PAYMENTS:
            return
            
        currencies_data = [
            ('QAR', 'Qatari Riyal', 'ر.ق', 1.0000),
            ('USD', 'US Dollar', '$', 3.6400),
            ('EUR', 'Euro', '€', 3.9500),
            ('GBP', 'British Pound', '£', 4.5200),
            ('SAR', 'Saudi Riyal', 'ر.س', 0.9700),
            ('AED', 'UAE Dirham', 'د.إ', 0.9900),
            ('KWD', 'Kuwaiti Dinar', 'د.ك', 11.9000),
        ]
        
        for code, name, symbol, rate in currencies_data:
            Currency.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'symbol': symbol,
                    'exchange_rate_to_qar': Decimal(str(rate)),
                    'is_active': True
                }
            )
        
        self.stdout.write('  💱 Created currencies')
    
    def _create_service_categories(self):
        """Create service categories"""
        categories_data = [
            ('Accommodation', 'Comfortable retreat and accommodation services', 'fa-home'),
            ('Home Care', 'Professional home care and assistance services', 'fa-heart'),
            ('Wellness & Spa', 'Wellness, spa, and relaxation services', 'fa-spa'),
            ('Mental Health', 'Mental health and counseling services', 'fa-brain'),
            ('Nutrition', 'Nutrition planning and meal services', 'fa-apple-alt'),
            ('Meditation', 'Meditation and mindfulness sessions', 'fa-om'),
            ('Fitness', 'Personal fitness and exercise programs', 'fa-dumbbell'),
            ('Childcare', 'Professional childcare services', 'fa-baby'),
            ('Elderly Care', 'Specialized elderly care services', 'fa-wheelchair'),
            ('Emergency Care', 'Emergency and urgent care services', 'fa-ambulance'),
        ]
        
        self.categories = []
        for name, description, icon in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'icon': icon,
                }
            )
            self.categories.append(category)
        
        self.stdout.write(f'  🏷️ Created {len(self.categories)} service categories')
    
    def _create_payment_methods(self):
        """Create payment methods"""
        if not HAS_PAYMENTS:
            return
            
        payment_methods_data = [
            ('card', 'Credit/Debit Card', True, {'supports_recurring': True}),
            ('bank_transfer', 'Bank Transfer', True, {'processing_time': '1-3 days'}),
            ('digital_wallet', 'Digital Wallet', True, {'instant_transfer': True}),
            ('cash', 'Cash Payment', True, {'requires_confirmation': True}),
            ('bnpl', 'Buy Now Pay Later', True, {'credit_check': True}),
        ]
        
        for payment_type, name, is_active, config in payment_methods_data:
            PaymentMethod.objects.get_or_create(
                payment_type=payment_type,
                defaults={
                    'name': name,
                    'is_active': is_active,
                    'configuration': config
                }
            )
        
        self.stdout.write('  💳 Created payment methods')
    
    def _create_workflow_templates(self):
        """Create workflow templates"""
        if not HAS_OPERATIONS:
            return
            
        workflow_templates = [
            {
                'name': 'Standard Booking Processing',
                'workflow_type': 'booking_processing',
                'trigger_type': 'event_based',
                'description': 'Standard workflow for processing new bookings',
                'estimated_duration_minutes': 30,
            },
            {
                'name': 'Vendor Assignment Process',
                'workflow_type': 'vendor_assignment',
                'trigger_type': 'event_based',
                'description': 'Automated vendor assignment workflow',
                'estimated_duration_minutes': 15,
            },
            {
                'name': 'Quality Assurance Check',
                'workflow_type': 'quality_check',
                'trigger_type': 'time_based',
                'description': 'Post-service quality assurance workflow',
                'estimated_duration_minutes': 45,
            },
            {
                'name': 'Payment Processing',
                'workflow_type': 'payment_processing',
                'trigger_type': 'event_based',
                'description': 'Secure payment processing workflow',
                'estimated_duration_minutes': 10,
            },
        ]
        
        admin_user = User.objects.filter(is_staff=True).first()
        
        for template_data in workflow_templates:
            WorkflowTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    **template_data,
                    'created_by': admin_user,
                    'steps_config': {
                        'steps': ['validation', 'processing', 'completion'],
                        'auto_advance': True
                    },
                    'conditions_config': {'default_conditions': True},
                    'automation_rules': {'auto_assign': True}
                }
            )
        
        self.stdout.write('  🔄 Created workflow templates')
    
    def _create_report_templates(self):
        """Create report templates"""
        if not HAS_REPORTING:
            return
            
        report_templates = [
            {
                'name': 'Daily Operations Report',
                'report_type': 'operational',
                'description': 'Daily overview of platform operations',
                'parameters': {'period': 'daily', 'metrics': ['bookings', 'revenue']},
            },
            {
                'name': 'Vendor Performance Report',
                'report_type': 'performance',
                'description': 'Vendor performance and quality metrics',
                'parameters': {'period': 'monthly', 'metrics': ['ratings', 'completion_rate']},
            },
            {
                'name': 'Financial Summary Report',
                'report_type': 'financial',
                'description': 'Financial overview and revenue analysis',
                'parameters': {'period': 'monthly', 'metrics': ['revenue', 'payments', 'commissions']},
            }
        ]
        
        admin_user = User.objects.filter(is_staff=True).first()
        
        for template_data in report_templates:
            ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    **template_data,
                    'created_by': admin_user,
                    'is_active': True
                }
            )
        
        self.stdout.write('  📊 Created report templates')
    
    def _create_users(self):
        """Create diverse user accounts"""
        self.users = []
        user_types = ['MOTHER', 'ACCOMMODATION', 'CARETAKER', 'WELLNESS', 'MENTAL_HEALTH', 'FOOD']
        
        # Create mothers (customers)
        mothers_count = int(self.users_count * 0.6)  # 60% mothers
        for i in range(mothers_count):
            user = User.objects.create_user(
                email=fake.unique.email(),
                password='testpass123',
                first_name=fake.first_name_female(),
                last_name=fake.last_name(),
                user_type='MOTHER',
                phone=fake.phone_number()[:20],
                address=fake.address(),
                city=fake.city(),
                country='Qatar',
                postal_code=fake.postcode(),
                is_verified=random.choice([True, False]),
                date_joined=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=timezone.get_current_timezone())
            )
            self.users.append(user)
        
        # Create service providers
        providers_count = self.users_count - mothers_count
        provider_types = [t for t in user_types if t != 'MOTHER']
        
        for i in range(providers_count):
            user_type = random.choice(provider_types)
            user = User.objects.create_user(
                email=fake.unique.email(),
                password='testpass123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type=user_type,
                phone=fake.phone_number()[:20],
                address=fake.address(),
                city=fake.city(),
                country='Qatar',
                postal_code=fake.postcode(),
                is_verified=True,
                date_joined=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone())
            )
            self.users.append(user)
        
        self.stdout.write(f'  👥 Created {len(self.users)} users')
    
    def _create_vendor_profiles(self):
        """Create vendor profiles for service providers"""
        self.vendors = []
        provider_users = [u for u in self.users if u.user_type != 'MOTHER']
        
        business_types = ['individual', 'small_business', 'corporation', 'ngo']
        statuses = ['active', 'pending', 'suspended', 'inactive']
        
        for i, user in enumerate(provider_users[:self.vendors_count]):
            vendor = VendorProfile.objects.create(
                user=user,
                business_name=fake.company(),
                business_type=random.choice(business_types),
                business_license=fake.bothify('LIC-#####'),
                tax_id=fake.bothify('TAX-########'),
                business_phone=fake.phone_number()[:20],
                business_email=fake.company_email(),
                website=fake.url() if random.choice([True, False]) else '',
                service_areas=f"{fake.city()}, {fake.city()}, {fake.city()}",
                status=random.choice(statuses) if i > 0 else 'active',  # First vendor always active
                verified=random.choice([True, False]),
                verification_date=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()) if random.choice([True, False]) else None,
                average_rating=round(random.uniform(3.5, 5.0), 2),
                total_reviews=random.randint(0, 100),
                total_bookings=random.randint(0, 200),
                completed_bookings=random.randint(0, 180),
                commission_rate=Decimal(str(random.uniform(10.0, 20.0))),
                total_earnings=Decimal(str(random.uniform(1000.0, 50000.0))),
                joined_date=user.date_joined,
                auto_accept_bookings=random.choice([True, False])
            )
            self.vendors.append(vendor)
        
        self.stdout.write(f'  🏢 Created {len(self.vendors)} vendor profiles')
    
    def _create_vendor_documents(self):
        """Create vendor documents"""
        document_types = ['license', 'insurance', 'certification', 'tax_certificate', 'identity']
        statuses = ['approved', 'pending', 'rejected']
        
        for vendor in self.vendors:
            num_docs = random.randint(2, 5)
            for _ in range(num_docs):
                VendorDocument.objects.create(
                    vendor=vendor,
                    document_type=random.choice(document_types),
                    title=fake.sentence(nb_words=4),
                    document_file=f'vendor_documents/{fake.file_name(extension="pdf")}',
                    description=fake.text(max_nb_chars=200),
                    status=random.choice(statuses),
                    uploaded_date=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()),
                    expiry_date=fake.date_between(start_date='+1m', end_date='+2y') if random.choice([True, False]) else None
                )
        
        self.stdout.write('  📄 Created vendor documents')
    
    def _create_vendor_availability(self):
        """Create vendor availability schedules"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for vendor in self.vendors:
            # Regular weekly availability
            working_days = random.sample(days, random.randint(4, 7))
            for day in working_days:
                start_hour = random.randint(6, 10)
                end_hour = random.randint(16, 22)
                
                VendorAvailability.objects.create(
                    vendor=vendor,
                    day_of_week=day,
                    start_time=time(start_hour, 0),
                    end_time=time(end_hour, 0),
                    is_available=True
                )
            
            # Add some blackout dates
            if random.choice([True, False]):
                today = timezone.now().date()
                start_date = fake.date_between(start_date=today + timedelta(days=1), end_date=today + timedelta(days=90))
                end_date = start_date + timedelta(days=random.randint(1, 7))
                
                VendorBlackoutDate.objects.create(
                    vendor=vendor,
                    start_date=start_date,
                    end_date=end_date,
                    reason=fake.sentence(nb_words=6),
                    description=fake.text(max_nb_chars=150)
                )
        
        self.stdout.write('  📅 Created vendor availability schedules')
    
    def _create_services(self):
        """Create diverse services"""
        self.services = []
        service_types = [
            (Service, {}),
            (AccommodationService, {
                'location': fake.city(),
                'address': fake.address(),
                'capacity': random.randint(1, 20),
                'amenities': ', '.join(fake.words(nb=5)),
                'room_type': random.choice(['Single', 'Double', 'Suite', 'Family']),
                'check_in_time': time(14, 0),
                'check_out_time': time(11, 0)
            }),
            (HomeCareService, {
                'service_area': f"{fake.city()}, {fake.city()}",
                'min_hours': random.randint(2, 8)
            }),
            (WellnessService, {
                'service_type': random.choice(['Massage', 'Meditation', 'Counseling', 'Therapy']),
                'is_virtual': random.choice([True, False])
            }),
            (NutritionService, {
                'dietary_options': ', '.join(random.sample(['Vegetarian', 'Vegan', 'Gluten-Free', 'Halal', 'Organic'], 3)),
                'is_customizable': True,
                'preparation_time': timedelta(hours=random.randint(1, 4)),
                'delivery_available': random.choice([True, False])
            })
        ]
        
        for i in range(self.services_count):
            service_class, extra_fields = random.choice(service_types)
            category = random.choice(self.categories)
            
            base_data = {
                'name': fake.catch_phrase(),
                'description': fake.text(max_nb_chars=500),
                'price': Decimal(str(random.uniform(50.0, 1000.0))),
                'duration': timedelta(hours=random.randint(1, 8)),
                'category': category,
                'status': random.choice(['available', 'unavailable', 'limited']),
                'featured': random.choice([True, False]),
                'created_at': fake.date_time_between(start_date='-1y', end_date='now', tzinfo=timezone.get_current_timezone()),
            }
            
            service = service_class.objects.create(**base_data, **extra_fields)
            self.services.append(service)
        
        self.stdout.write(f'  🏥 Created {len(self.services)} services')
    
    def _create_wellness_programs(self):
        """Create wellness programs"""
        if not HAS_WELLNESS:
            return
            
        program_types = ['meditation', 'fitness', 'nutrition', 'mental_health', 'lifestyle']
        
        for _ in range(15):
            WellnessProgram.objects.create(
                name=fake.catch_phrase(),
                description=fake.text(max_nb_chars=300),
                program_type=random.choice(program_types),
                duration_weeks=random.randint(4, 16),
                max_participants=random.randint(5, 30),
                price=Decimal(str(random.uniform(200.0, 2000.0))),
                is_active=True,
                created_by=random.choice(self.vendors).user if self.vendors else None
            )
        
        self.stdout.write('  🧘 Created wellness programs')
    
    def _create_bookings(self):
        """Create realistic bookings"""
        self.bookings = []
        mothers = [u for u in self.users if u.user_type == 'MOTHER']
        statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        priorities = ['low', 'normal', 'high', 'urgent']
        
        for i in range(self.bookings_count):
            user = random.choice(mothers)
            service = random.choice(self.services)
            
            start_date = fake.date_between(start_date=f'-{self.days_back}d', end_date='+30d')
            end_date = start_date + timedelta(days=random.randint(0, 7))
            
            booking = Booking.objects.create(
                user=user,
                service=service,
                start_date=start_date,
                end_date=end_date,
                start_time=time(random.randint(8, 18), random.choice([0, 30])),
                end_time=time(random.randint(10, 20), random.choice([0, 30])),
                address=fake.address(),
                city=fake.city(),
                postal_code=fake.postcode(),
                special_instructions=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                base_price=service.price,
                additional_fees=Decimal(str(random.uniform(0, 100))),
                discount_amount=Decimal(str(random.uniform(0, 50))),
                status=random.choice(statuses),
                priority=random.choice(priorities),
                client_phone=fake.phone_number()[:20],
                client_email=user.email,
                emergency_contact=fake.name(),
                emergency_phone=fake.phone_number()[:20],
                notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                created_at=fake.date_time_between(start_date=f'-{self.days_back}d', end_date='now', tzinfo=timezone.get_current_timezone())
            )
            
            # Add booking items
            if random.choice([True, False]):
                num_items = random.randint(1, 3)
                for _ in range(num_items):
                    BookingItem.objects.create(
                        booking=booking,
                        name=fake.word().title(),
                        description=fake.sentence(),
                        quantity=random.randint(1, 5),
                        price=Decimal(str(random.uniform(10.0, 100.0)))
                    )
            
            # Add status history
            if booking.status != 'pending':
                BookingStatusHistory.objects.create(
                    booking=booking,
                    old_status='pending',
                    new_status=booking.status,
                    changed_by=random.choice(self.vendors).user if self.vendors else None,
                    notes=fake.sentence(),
                    timestamp=booking.created_at + timedelta(hours=random.randint(1, 48))
                )
            
            self.bookings.append(booking)
        
        self.stdout.write(f'  📅 Created {len(self.bookings)} bookings')
    
    def _create_workflow_instances(self):
        """Create workflow instances"""
        if not HAS_OPERATIONS:
            return
            
        templates = WorkflowTemplate.objects.all()
        if not templates.exists():
            return
        
        for booking in self.bookings[:50]:  # Create workflows for some bookings
            template = random.choice(templates)
            
            WorkflowInstance.objects.create(
                template=template,
                status=random.choice(['pending', 'running', 'completed', 'failed']),
                context_data={'booking_id': booking.id, 'auto_generated': True},
                started_at=booking.created_at,
            )
        
        self.stdout.write('  🔄 Created workflow instances')
    
    def _create_financial_accounts(self):
        """Create financial accounts"""
        if not HAS_FINANCIAL:
            return
            
        account_types = ['revenue', 'expense', 'asset', 'liability', 'equity']
        qar_currency = None
        
        if HAS_PAYMENTS:
            qar_currency = Currency.objects.filter(code='QAR').first()
        
        for _ in range(10):
            FinancialAccount.objects.create(
                account_number=fake.bothify('ACC-#######'),
                account_name=fake.sentence(nb_words=3),
                account_type=random.choice(account_types),
                currency=qar_currency,
                balance=Decimal(str(random.uniform(1000.0, 100000.0))),
                is_active=True,
                description=fake.text(max_nb_chars=200)
            )
        
        self.stdout.write('  🏦 Created financial accounts')
    
    def _create_payments(self):
        """Create payment records"""
        if not HAS_PAYMENTS:
            return
            
        payment_methods = PaymentMethod.objects.all()
        currencies = Currency.objects.all()
        
        if not payment_methods.exists() or not currencies.exists():
            return
        
        for booking in random.sample(self.bookings, min(len(self.bookings), 150)):
            payment = Payment.objects.create(
                user=booking.user,
                amount=booking.total_price,
                currency=random.choice(currencies),
                payment_method=random.choice(payment_methods),
                status=random.choice(['pending', 'processing', 'completed', 'failed']),
                transaction_reference=fake.bothify('TXN-############'),
                description=f'Payment for booking {booking.booking_number}',
                payment_date=booking.created_at + timedelta(minutes=random.randint(1, 60)),
                metadata={'booking_id': booking.id}
            )
            
            # Create corresponding booking payment
            BookingPayment.objects.create(
                booking=booking,
                amount=booking.total_price,
                payment_method='credit_card',
                payment_status='completed' if payment.status == 'completed' else 'pending',
                transaction_id=payment.transaction_reference,
                payment_date=payment.payment_date
            )
        
        self.stdout.write('  💳 Created payment records')
    
    def _create_invoices(self):
        """Create invoices"""
        if not HAS_FINANCIAL:
            return
            
        qar_currency = None
        if HAS_PAYMENTS:
            qar_currency = Currency.objects.filter(code='QAR').first()
        
        for booking in random.sample(self.bookings, min(len(self.bookings), 100)):
            Invoice.objects.create(
                invoice_number=fake.bothify('INV-########'),
                customer=booking.user,
                issue_date=booking.created_at.date(),
                due_date=booking.created_at.date() + timedelta(days=30),
                subtotal=booking.base_price,
                tax_amount=booking.base_price * Decimal('0.05'),  # 5% tax
                total_amount=booking.total_price,
                currency=qar_currency,
                status=random.choice(['draft', 'sent', 'paid', 'overdue', 'cancelled']),
                description=f'Invoice for {booking.service.name}',
                metadata={'booking_id': booking.id}
            )
        
        self.stdout.write('  🧾 Created invoices')
    
    def _create_vendor_payments(self):
        """Create vendor payment records"""
        for vendor in self.vendors:
            # Create periodic payments
            start_date = timezone.now().date() - timedelta(days=self.days_back)
            current_date = start_date
            
            while current_date <= timezone.now().date():
                period_end = min(current_date + timedelta(days=30), timezone.now().date())
                
                VendorPayment.objects.create(
                    vendor=vendor,
                    payment_type='commission',
                    amount=Decimal(str(random.uniform(500.0, 5000.0))),
                    period_start=current_date,
                    period_end=period_end,
                    booking_count=random.randint(5, 25),
                    gross_amount=Decimal(str(random.uniform(2000.0, 20000.0))),
                    commission_rate=vendor.commission_rate,
                    status=random.choice(['completed', 'processing', 'pending']),
                    payment_date=fake.date_time_between(start_date=current_date, end_date=period_end, tzinfo=timezone.get_current_timezone()),
                    reference_number=fake.bothify('VP-############')
                )
                
                current_date = period_end + timedelta(days=1)
        
        self.stdout.write('  💰 Created vendor payments')
    
    def _create_quality_scores(self):
        """Create quality scores for vendors"""
        for vendor in self.vendors:
            # Create historical quality scores
            start_date = timezone.now().date() - timedelta(days=self.days_back)
            current_date = start_date
            
            while current_date <= timezone.now().date():
                period_end = min(current_date + timedelta(days=7), timezone.now().date())
                
                # Generate realistic quality scores
                base_score = random.uniform(70, 95)
                customer_ratings = base_score + random.uniform(-5, 5)
                completion_rate = base_score + random.uniform(-10, 5)
                response_time = base_score + random.uniform(-15, 10)
                repeat_customers = base_score + random.uniform(-20, 15)
                performance_trends = base_score + random.uniform(-10, 10)
                
                overall_score = (customer_ratings + completion_rate + response_time + repeat_customers + performance_trends) / 5
                
                QualityScore.objects.create(
                    vendor=vendor,
                    overall_score=Decimal(str(round(overall_score, 2))),
                    customer_ratings_score=Decimal(str(round(customer_ratings, 2))),
                    completion_rate_score=Decimal(str(round(completion_rate, 2))),
                    response_time_score=Decimal(str(round(response_time, 2))),
                    repeat_customers_score=Decimal(str(round(repeat_customers, 2))),
                    performance_trends_score=Decimal(str(round(performance_trends, 2))),
                    weights={
                        'customer_ratings': 0.3,
                        'completion_rate': 0.25,
                        'response_time': 0.2,
                        'repeat_customers': 0.15,
                        'performance_trends': 0.1
                    },
                    total_bookings=random.randint(5, 50),
                    completed_bookings=random.randint(4, 45),
                    avg_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                    avg_response_time_hours=Decimal(str(round(random.uniform(0.5, 6.0), 2))),
                    repeat_customer_rate=Decimal(str(round(random.uniform(20.0, 80.0), 2))),
                    trend_direction=random.choice(['improving', 'stable', 'declining']),
                    period_start=current_date,
                    period_end=period_end
                )
                
                current_date = period_end + timedelta(days=1)
        
        self.stdout.write('  📊 Created quality scores')
    
    def _create_performance_metrics(self):
        """Create performance metrics"""
        for vendor in self.vendors:
            # Create daily performance metrics
            start_date = timezone.now().date() - timedelta(days=30)
            current_date = start_date
            
            while current_date <= timezone.now().date():
                PerformanceMetrics.objects.create(
                    vendor=vendor,
                    date=current_date,
                    bookings_received=random.randint(0, 10),
                    bookings_accepted=random.randint(0, 8),
                    bookings_completed=random.randint(0, 6),
                    bookings_cancelled=random.randint(0, 2),
                    bookings_no_show=random.randint(0, 1),
                    avg_response_time_minutes=random.randint(30, 240),
                    first_response_rate=Decimal(str(round(random.uniform(70.0, 100.0), 2))),
                    total_ratings=random.randint(0, 5),
                    avg_rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
                    five_star_ratings=random.randint(0, 3),
                    four_star_ratings=random.randint(0, 2),
                    three_star_ratings=random.randint(0, 1),
                    two_star_ratings=random.randint(0, 1),
                    one_star_ratings=random.randint(0, 1),
                    revenue=Decimal(str(random.uniform(0, 1000))),
                    commission_paid=Decimal(str(random.uniform(0, 150))),
                    avg_booking_value=Decimal(str(random.uniform(100, 500))),
                    new_customers=random.randint(0, 5),
                    repeat_customers=random.randint(0, 3),
                    total_unique_customers=random.randint(0, 8),
                    on_time_completion_rate=Decimal(str(round(random.uniform(80.0, 100.0), 2))),
                    rework_rate=Decimal(str(round(random.uniform(0.0, 10.0), 2)))
                )
                
                current_date += timedelta(days=1)
        
        self.stdout.write('  📈 Created performance metrics')
    
    def _create_vendor_rankings(self):
        """Create vendor rankings"""
        categories = ServiceCategory.objects.all()
        
        # Overall rankings
        vendors_with_scores = []
        for vendor in self.vendors:
            latest_score = QualityScore.objects.filter(vendor=vendor).order_by('-calculated_at').first()
            if latest_score:
                vendors_with_scores.append((vendor, latest_score.overall_score))
        
        vendors_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (vendor, score) in enumerate(vendors_with_scores, 1):
            VendorRanking.objects.create(
                vendor=vendor,
                service_category=None,  # Overall ranking
                overall_rank=rank,
                quality_rank=rank,
                performance_rank=random.randint(1, len(vendors_with_scores)),
                customer_satisfaction_rank=random.randint(1, len(vendors_with_scores)),
                quality_score=score,
                performance_score=Decimal(str(round(random.uniform(70, 95), 2))),
                customer_satisfaction_score=Decimal(str(round(random.uniform(80, 100), 2))),
                total_vendors=len(vendors_with_scores),
                period_start=timezone.now().date() - timedelta(days=30),
                period_end=timezone.now().date()
            )
        
        # Category-specific rankings
        for category in categories:
            category_vendors = random.sample(vendors_with_scores, min(10, len(vendors_with_scores)))
            for rank, (vendor, score) in enumerate(category_vendors, 1):
                VendorRanking.objects.create(
                    vendor=vendor,
                    service_category=category,
                    overall_rank=rank,
                    quality_rank=rank,
                    performance_rank=random.randint(1, len(category_vendors)),
                    customer_satisfaction_rank=random.randint(1, len(category_vendors)),
                    quality_score=score,
                    performance_score=Decimal(str(round(random.uniform(70, 95), 2))),
                    customer_satisfaction_score=Decimal(str(round(random.uniform(80, 100), 2))),
                    total_vendors=len(category_vendors),
                    period_start=timezone.now().date() - timedelta(days=30),
                    period_end=timezone.now().date()
                )
        
        self.stdout.write('  🏆 Created vendor rankings')
    
    def _create_assignment_data(self):
        """Create smart vendor assignment data"""
        # Create vendor availability data
        for vendor in self.vendors:
            for days_offset in range(0, 30):
                assignment_date = timezone.now().date() + timedelta(days=days_offset)
                
                AnalyticsVendorAvailability.objects.create(
                    vendor=vendor,
                    date=assignment_date,
                    status=random.choice(['available', 'busy', 'unavailable']),
                    max_bookings=random.randint(3, 10),
                    current_bookings=random.randint(0, 7),
                    time_slots_available=random.randint(4, 12),
                    time_slots_booked=random.randint(0, 8),
                    service_areas=['Doha', 'Al Rayyan', 'Al Wakrah'],
                    max_travel_distance_km=random.randint(20, 100),
                    notes=fake.sentence() if random.choice([True, False]) else ''
                )
        
        # Create vendor workload data
        for vendor in self.vendors:
            for days_offset in range(-7, 8):
                workload_date = timezone.now().date() + timedelta(days=days_offset)
                
                VendorWorkload.objects.create(
                    vendor=vendor,
                    date=workload_date,
                    active_bookings=random.randint(0, 8),
                    pending_bookings=random.randint(0, 5),
                    completed_today=random.randint(0, 6),
                    cancelled_today=random.randint(0, 2),
                    capacity_utilization=Decimal(str(round(random.uniform(30.0, 95.0), 2))),
                    avg_job_duration_hours=Decimal(str(round(random.uniform(1.0, 6.0), 2))),
                    total_work_hours_scheduled=Decimal(str(round(random.uniform(4.0, 10.0), 2))),
                    stress_level=random.choice(['low', 'medium', 'high']),
                    notes=fake.sentence() if random.choice([True, False]) else ''
                )
        
        # Create vendor assignments
        for booking in random.sample(self.bookings, min(len(self.bookings), 100)):
            if self.vendors:
                vendor = random.choice(self.vendors)
                assignment = VendorAssignment.objects.create(
                    booking=booking,
                    vendor=vendor,
                    status=random.choice(['pending', 'accepted', 'declined']),
                    assignment_method=random.choice(['smart_ai', 'manual', 'preference_based']),
                    total_score=Decimal(str(round(random.uniform(60.0, 95.0), 2))),
                    quality_score=Decimal(str(round(random.uniform(70.0, 95.0), 2))),
                    location_score=Decimal(str(round(random.uniform(50.0, 90.0), 2))),
                    availability_score=Decimal(str(round(random.uniform(60.0, 100.0), 2))),
                    workload_score=Decimal(str(round(random.uniform(40.0, 90.0), 2))),
                    preference_score=Decimal(str(round(random.uniform(0.0, 80.0), 2))),
                    confidence_level=Decimal(str(round(random.uniform(0.5, 1.0), 2))),
                    assigned_by=random.choice(self.users),
                    vendor_notified_at=timezone.now() - timedelta(minutes=random.randint(1, 120)),
                    vendor_responded_at=timezone.now() - timedelta(minutes=random.randint(1, 60)) if random.choice([True, False]) else None,
                    notes=fake.sentence() if random.choice([True, False]) else ''
                )
                
                # Add assignment logs
                log_types = ['assignment_created', 'vendor_notified', 'vendor_responded', 'assignment_updated']
                for log_type in random.sample(log_types, random.randint(1, 3)):
                    AssignmentLog.objects.create(
                        assignment=assignment,
                        log_type=log_type,
                        message=fake.sentence(),
                        data={'auto_generated': True, 'test_data': True},
                        timestamp=assignment.assigned_at + timedelta(minutes=random.randint(1, 60))
                    )
        
        # Create assignment preferences
        mothers = [u for u in self.users if u.user_type == 'MOTHER']
        for _ in range(20):
            if self.vendors and mothers:
                AssignmentPreference.objects.create(
                    vendor=random.choice(self.vendors),
                    customer=random.choice(mothers),
                    preference_type=random.choice(['preferred', 'avoided']),
                    weight=Decimal(str(round(random.uniform(0.1, 1.0), 2))),
                    reason=fake.sentence(),
                    is_active=True,
                    notes=fake.text(max_nb_chars=200)
                )
        
        self.stdout.write('  🎯 Created smart assignment data')
    
    def _create_service_reviews(self):
        """Create service reviews"""
        mothers = [u for u in self.users if u.user_type == 'MOTHER']
        
        for _ in range(100):
            if mothers:
                service = random.choice(self.services)
                user = random.choice(mothers)
                
                # Avoid duplicate reviews
                if not ServiceReview.objects.filter(service=service, user=user).exists():
                    ServiceReview.objects.create(
                        service=service,
                        user=user,
                        rating=random.randint(3, 5),
                        comment=fake.text(max_nb_chars=300),
                        created_at=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=timezone.get_current_timezone()),
                        is_public=random.choice([True, False])
                    )
        
        self.stdout.write('  ⭐ Created service reviews')
    
    def _create_wellness_sessions(self):
        """Create wellness sessions"""
        if not HAS_WELLNESS:
            return
            
        programs = WellnessProgram.objects.all()
        mothers = [u for u in self.users if u.user_type == 'MOTHER']
        
        if not programs.exists() or not mothers:
            return
        
        for program in programs:
            for _ in range(random.randint(1, 5)):
                if mothers:
                    participant = random.choice(mothers)
                    WellnessSession.objects.create(
                        program=program,
                        participant=participant,
                        session_date=fake.date_between(start_date='-3m', end_date='+1m'),
                        session_time=time(random.randint(9, 17), random.choice([0, 30])),
                        duration_minutes=random.randint(30, 120),
                        session_type=random.choice(['individual', 'group', 'virtual']),
                        status=random.choice(['scheduled', 'completed', 'cancelled', 'no_show']),
                        notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                        instructor=random.choice(self.vendors).user if self.vendors else None
                    )
        
        self.stdout.write('  🧘 Created wellness sessions')
    
    def _create_reports(self):
        """Create sample reports"""
        if not HAS_REPORTING:
            return
            
        templates = ReportTemplate.objects.all()
        admin_user = User.objects.filter(is_staff=True).first()
        
        if not templates.exists():
            return
        
        for template in templates:
            for _ in range(random.randint(2, 5)):
                Report.objects.create(
                    name=f"{template.name} - {fake.date()}",
                    report_type=template.report_type,
                    template=template,
                    generated_by=admin_user,
                    parameters=template.parameters,
                    data={
                        'total_bookings': random.randint(50, 200),
                        'total_revenue': random.uniform(10000, 50000),
                        'avg_rating': random.uniform(4.0, 5.0),
                        'completion_rate': random.uniform(85.0, 98.0)
                    },
                    status=random.choice(['completed', 'in_progress', 'failed']),
                    file_path=f'reports/{fake.file_name(extension="pdf")}' if random.choice([True, False]) else '',
                    scheduled_at=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=timezone.get_current_timezone()),
                    completed_at=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=timezone.get_current_timezone())
                )
        
        self.stdout.write('  📋 Created reports')
    
    def _print_summary(self):
        """Print data generation summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 BULK DATA GENERATION SUMMARY'))
        self.stdout.write('='*60)
        
        summary_data = [
            ('Users', User.objects.count()),
            ('Vendor Profiles', VendorProfile.objects.count()),
            ('Service Categories', ServiceCategory.objects.count()),
            ('Services', Service.objects.count()),
            ('Bookings', Booking.objects.count()),
            ('Service Reviews', ServiceReview.objects.count()),
            ('Quality Scores', QualityScore.objects.count()),
            ('Performance Metrics', PerformanceMetrics.objects.count()),
            ('Vendor Rankings', VendorRanking.objects.count()),
            ('Vendor Assignments', VendorAssignment.objects.count()),
        ]
        
        # Add optional model counts
        if HAS_PAYMENTS:
            summary_data.extend([
                ('Currencies', Currency.objects.count()),
                ('Payment Methods', PaymentMethod.objects.count()),
                ('Payments', Payment.objects.count()),
            ])
        
        if HAS_FINANCIAL:
            summary_data.extend([
                ('Financial Accounts', FinancialAccount.objects.count()),
                ('Invoices', Invoice.objects.count()),
            ])
        
        if HAS_WELLNESS:
            summary_data.extend([
                ('Wellness Programs', WellnessProgram.objects.count()),
                ('Wellness Sessions', WellnessSession.objects.count()),
            ])
        
        if HAS_OPERATIONS:
            summary_data.extend([
                ('Workflow Templates', WorkflowTemplate.objects.count()),
                ('Workflow Instances', WorkflowInstance.objects.count()),
            ])
        
        if HAS_REPORTING:
            summary_data.extend([
                ('Report Templates', ReportTemplate.objects.count()),
                ('Reports', Report.objects.count()),
            ])
        
        for item, count in summary_data:
            self.stdout.write(f"{item:.<30} {count:>8}")
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('✅ All bulk data generated successfully!')
        )
        self.stdout.write(
            self.style.WARNING('💡 Run quality scoring and analytics commands to populate calculated metrics')
        )