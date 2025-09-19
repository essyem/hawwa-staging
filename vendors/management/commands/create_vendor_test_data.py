from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from datetime import datetime, timedelta
import random
from decimal import Decimal

from vendors.models import VendorProfile, VendorDocument, VendorAvailability, VendorPayment
from services.models import Service, ServiceCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate realistic test data for vendors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vendors',
            type=int,
            default=10,
            help='Number of vendors to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing vendor data before creating new data',
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing vendor data...'))
            VendorProfile.objects.all().delete()
            
        self.stdout.write('Creating vendor test data...')
        
        # Create test vendors
        vendors = self.create_test_vendors(fake, options['vendors'])
        
        # Create vendor availability schedules
        self.create_vendor_availability(fake, vendors)
        
        # Create vendor documents
        self.create_vendor_documents(fake, vendors)
        
        # Create vendor payments
        self.create_vendor_payments(fake, vendors)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(vendors)} vendors with complete profiles!'
            )
        )

    def create_test_vendors(self, fake, count):
        """Create test vendor users and profiles"""
        vendors = []
        
        vendor_types = ['ACCOMMODATION', 'CARETAKER', 'WELLNESS', 'MENTAL_HEALTH', 'FOOD']
        business_types = ['individual', 'small_business', 'corporation']
        
        business_names = [
            'Qatar Wellness Center', 'Desert Rose Spa', 'Falcon Care Services',
            'Pearl Accommodation', 'Doha Maternal Care', 'Arabian Nights Retreat',
            'Lotus Healing Center', 'Crescent Moon Services', 'Oasis Care Solutions',
            'Qatar Family Support', 'Jasmine Wellness Hub', 'Palm Tree Care',
            'Golden Sands Recovery', 'Emerald Health Services', 'Silver Star Care'
        ]
        
        for i in range(count):
            # Create vendor user
            user = User.objects.create_user(
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='testpass123',
                user_type=fake.random_element(vendor_types),
                phone=fake.numerify('+974########'),
                address=fake.address()[:100],
                city=fake.city()[:50],
                country='Qatar',
                is_verified=fake.boolean(chance_of_getting_true=80)
            )
            
            # Create vendor profile
            business_name = fake.random_element(business_names) + f" {fake.numerify('##')}"
            
            vendor_profile = VendorProfile.objects.create(
                user=user,
                business_name=business_name,
                business_type=fake.random_element(business_types),
                business_license=fake.numerify('QL-####-####'),
                tax_id=fake.numerify('TX########'),
                business_phone=fake.numerify('+974########'),
                business_email=fake.email(),
                website=f"https://{fake.domain_name()}" if fake.boolean() else '',
                service_areas='Doha, Al Rayyan, Al Wakrah, Qatar',
                status=fake.random_element(['active', 'pending', 'suspended']),
                verified=fake.boolean(chance_of_getting_true=70),
                verification_date=timezone.make_aware(fake.date_time_between(start_date='-1y', end_date='now')) if fake.boolean() else None,
                average_rating=fake.pydecimal(left_digits=1, right_digits=2, min_value=3.0, max_value=5.0),
                total_reviews=random.randint(5, 100),
                total_bookings=random.randint(10, 200),
                completed_bookings=random.randint(8, 180),
                commission_rate=fake.pydecimal(left_digits=2, right_digits=2, min_value=10.0, max_value=20.0),
                total_earnings=fake.pydecimal(left_digits=5, right_digits=2, min_value=1000, max_value=50000),
                auto_accept_bookings=fake.boolean(chance_of_getting_true=30),
                notification_email=fake.boolean(chance_of_getting_true=90),
                notification_sms=fake.boolean(chance_of_getting_true=70)
            )
            
            vendors.append(vendor_profile)
            
            # Create associated services for this vendor
            self.create_vendor_services(fake, user, vendor_profile)
            
        self.stdout.write(f'Created {len(vendors)} test vendors')
        return vendors

    def create_vendor_services(self, fake, user, vendor_profile):
        """Create services associated with the vendor"""
        # Get or create categories based on vendor type
        category_mapping = {
            'ACCOMMODATION': 'Accommodation',
            'CARETAKER': 'Home Care',
            'WELLNESS': 'Wellness',
            'MENTAL_HEALTH': 'Wellness',
            'FOOD': 'Nutrition'
        }
        
        category_name = category_mapping.get(user.user_type, 'Wellness')
        category, created = ServiceCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{category_name} services for postpartum care'}
        )
        
        # Create 1-3 services for this vendor
        service_count = random.randint(1, 3)
        
        service_templates = {
            'ACCOMMODATION': [
                'Private Recovery Suite', 'Luxury Postpartum Room', 'Family Accommodation Package'
            ],
            'CARETAKER': [
                'Newborn Care Specialist', 'Postpartum Nursing', '24/7 Care Support'
            ],
            'WELLNESS': [
                'Postnatal Massage', 'Wellness Consultation', 'Stress Relief Therapy'
            ],
            'MENTAL_HEALTH': [
                'Postpartum Counseling', 'Mental Health Support', 'Therapy Sessions'
            ],
            'FOOD': [
                'Nutritional Meal Plans', 'Postpartum Cooking', 'Dietary Consultation'
            ]
        }
        
        templates = service_templates.get(user.user_type, service_templates['WELLNESS'])
        
        for i in range(service_count):
            service_name = f"{vendor_profile.business_name} - {fake.random_element(templates)} {fake.numerify('##')}"
            
            Service.objects.create(
                name=service_name,
                category=category,
                description=fake.paragraph(nb_sentences=3),
                short_description=fake.sentence(),
                price=fake.pydecimal(left_digits=3, right_digits=2, min_value=100, max_value=800),
                duration=timedelta(hours=random.choice([2, 4, 6, 8, 12, 24])),
                status=fake.random_element(['available', 'limited', 'unavailable']),
                featured=fake.boolean(chance_of_getting_true=20)
            )

    def create_vendor_availability(self, fake, vendors):
        """Create availability schedules for vendors"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for vendor in vendors:
            # Create availability for most days
            for day in days:
                if fake.boolean(chance_of_getting_true=80):  # 80% chance vendor is available on any given day
                    start_hour = random.choice([6, 7, 8, 9])
                    end_hour = random.choice([16, 17, 18, 19, 20])
                    
                    VendorAvailability.objects.create(
                        vendor=vendor,
                        day_of_week=day,
                        start_time=f"{start_hour:02d}:00",
                        end_time=f"{end_hour:02d}:00",
                        is_available=True
                    )

    def create_vendor_documents(self, fake, vendors):
        """Create sample documents for vendors"""
        document_types = ['license', 'insurance', 'certification', 'tax_certificate', 'identity']
        
        for vendor in vendors:
            # Create 2-4 documents per vendor
            doc_count = random.randint(2, 4)
            selected_types = fake.random_elements(document_types, length=doc_count, unique=True)
            
            for doc_type in selected_types:
                VendorDocument.objects.create(
                    vendor=vendor,
                    document_type=doc_type,
                    title=f"{doc_type.replace('_', ' ').title()} - {vendor.business_name}",
                    description=fake.sentence(),
                    status=fake.random_element(['pending', 'approved', 'rejected']),
                    uploaded_date=timezone.make_aware(fake.date_time_between(start_date='-6m', end_date='now')),
                    verified_date=timezone.make_aware(fake.date_time_between(start_date='-3m', end_date='now')) if fake.boolean() else None,
                    expiry_date=fake.date_between(start_date='+6m', end_date='+2y') if fake.boolean() else None
                )

    def create_vendor_payments(self, fake, vendors):
        """Create payment records for vendors"""
        
        for vendor in vendors:
            # Create 3-8 payment records
            payment_count = random.randint(3, 8)
            
            for i in range(payment_count):
                period_start = fake.date_between(start_date='-1y', end_date='-1m')
                period_end = period_start + timedelta(days=30)
                
                gross_amount = fake.pydecimal(left_digits=4, right_digits=2, min_value=500, max_value=5000)
                commission_amount = gross_amount * (vendor.commission_rate / 100)
                
                VendorPayment.objects.create(
                    vendor=vendor,
                    payment_type='commission',
                    amount=commission_amount,
                    currency='QAR',
                    period_start=period_start,
                    period_end=period_end,
                    booking_count=random.randint(5, 25),
                    gross_amount=gross_amount,
                    commission_rate=vendor.commission_rate,
                    status=fake.random_element(['completed', 'pending', 'processing']),
                    payment_date=timezone.make_aware(fake.date_time_between(start_date=period_end, end_date='now')) if fake.boolean() else None,
                    reference_number=fake.numerify('PAY-####-####'),
                    notes=fake.sentence() if fake.boolean() else ''
                )