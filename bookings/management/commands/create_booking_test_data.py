from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from datetime import datetime, timedelta
import random

from bookings.models import Booking, BookingItem, BookingStatusHistory, BookingPayment
from services.models import Service, ServiceCategory


User = get_user_model()


class Command(BaseCommand):
    help = 'Generate realistic test data for the booking system using Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bookings',
            type=int,
            default=50,
            help='Number of bookings to create',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create',
        )
        parser.add_argument(
            '--services',
            type=int,
            default=15,
            help='Number of services to create',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data',
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing test data...'))
            Booking.objects.all().delete()
            BookingItem.objects.all().delete()
            BookingStatusHistory.objects.all().delete()
            # Don't delete users/services in case they have real data
            
        self.stdout.write('Creating test data...')
        
        # Create test users (mothers)
        users = self.create_test_users(fake, options['users'])
        
        # Create test services if needed
        services = self.create_test_services(fake, options['services'])
        
        # Create test bookings
        bookings = self.create_test_bookings(fake, users, services, options['bookings'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(users)} users, {len(services)} services, '
                f'and {len(bookings)} bookings with realistic test data!'
            )
        )

    def create_test_users(self, fake, count):
        """Create test users with mother profiles"""
        users = []
        
        for i in range(count):
            # Create user
            user = User.objects.create_user(
                email=fake.email(),
                first_name=fake.first_name_female(),
                last_name=fake.last_name(),
                password='testpass123',
                user_type='MOTHER',
                phone=fake.numerify('+974########'),  # Qatar phone format
                address=fake.address()[:100],  # Truncate to avoid length issues
                city=fake.city()[:50],
                state=fake.state()[:50],
                country='Qatar',
                postal_code=fake.numerify('#####'),
                is_verified=fake.boolean(chance_of_getting_true=80)
            )
                
            users.append(user)
            
        self.stdout.write(f'Created {len(users)} test users')
        return users

    def create_test_services(self, fake, count):
        """Create test services if we don't have enough"""
        existing_services = list(Service.objects.all())
        
        if len(existing_services) >= count:
            return existing_services[:count]
            
        services = existing_services.copy()
        services_to_create = count - len(existing_services)
        
        # Get or create categories
        categories = ['Accommodation', 'Home Care', 'Wellness', 'Nutrition']
        category_objects = []
        
        for cat_name in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} services for postpartum care'}
            )
            category_objects.append(category)
        
        service_names = [
            'Postpartum Recovery Suite', 'Luxury Maternity Room', 'Private Care Suite',
            'Home Nursing Care', 'Newborn Care Specialist', 'Lactation Support',
            'Postnatal Massage', 'Aromatherapy Session', 'Yoga for New Mothers',
            'Nutritional Counseling', 'Meal Delivery Service', 'Herbal Tea Therapy',
            'Mental Health Counseling', 'Sleep Training Support', 'Baby Care Classes'
        ]
        
        for i in range(services_to_create):
            service_name = fake.random_element(service_names) if i < len(service_names) else fake.catch_phrase()
            # Make service name unique
            service_name = f"{service_name} {fake.numerify('###')}"
            
            service = Service.objects.create(
                name=service_name,
                category=fake.random_element(category_objects),
                description=fake.paragraph(nb_sentences=3),
                short_description=fake.sentence(),
                price=fake.pydecimal(left_digits=3, right_digits=2, min_value=50, max_value=500),
                duration=timedelta(hours=random.choice([1, 2, 3, 4, 6, 8, 12, 24])),
                status=fake.random_element(['available', 'limited', 'unavailable']),
                featured=fake.boolean(chance_of_getting_true=20)
            )
            services.append(service)
            
        self.stdout.write(f'Created {services_to_create} new services')
        return services

    def create_test_bookings(self, fake, users, services, count):
        """Create realistic test bookings"""
        bookings = []
        
        booking_statuses = ['draft', 'pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        priorities = ['low', 'normal', 'high', 'urgent']
        
        for i in range(count):
            user = fake.random_element(users)
            service = fake.random_element(services)
            
            # Generate realistic dates
            start_date = fake.date_between(start_date='-30d', end_date='+60d')
            end_date = start_date + service.duration
            
            booking = Booking.objects.create(
                user=user,
                service=service,
                status=fake.random_element(booking_statuses),
                priority=fake.random_element(priorities),
                start_date=start_date,
                end_date=end_date,
                start_time=fake.time(),
                end_time=fake.time(),
                
                # Client information
                client_email=user.email,
                client_phone=fake.numerify('+974########'),
                emergency_contact=fake.name()[:50],
                emergency_phone=fake.numerify('+974########'),
                
                # Location
                address=fake.address(),
                city=fake.city(),
                postal_code=fake.postcode(),
                
                # Pricing
                base_price=service.price,
                discount_amount=fake.pydecimal(left_digits=2, right_digits=2, min_value=0, max_value=50) if fake.boolean(chance_of_getting_true=30) else 0,
                additional_fees=fake.pydecimal(left_digits=2, right_digits=2, min_value=0, max_value=25) if fake.boolean(chance_of_getting_true=20) else 0,
                
                # Notes
                notes=fake.paragraph() if fake.boolean(chance_of_getting_true=60) else '',
                internal_notes=fake.paragraph() if fake.boolean(chance_of_getting_true=40) else '',
                
                # Special requirements
                special_instructions=fake.sentence() if fake.boolean(chance_of_getting_true=40) else '',
            )
            
            # Create booking items (additional services)
            if fake.boolean(chance_of_getting_true=70):
                num_items = random.randint(1, 3)
                for j in range(num_items):
                    BookingItem.objects.create(
                        booking=booking,
                        name=fake.word().title() + ' Service',
                        description=fake.sentence(),
                        quantity=random.randint(1, 3),
                        price=fake.pydecimal(left_digits=2, right_digits=2, min_value=10, max_value=100)
                    )
            
            # Create status history
            BookingStatusHistory.objects.create(
                booking=booking,
                old_status='',
                new_status=booking.status,
                changed_by=user,
                notes=f'Booking created with status: {booking.status}',
                timestamp=booking.created_at
            )
            
            # Add additional status changes for some bookings
            if booking.status not in ['draft', 'pending']:
                # Add a status transition
                old_status = 'pending'
                BookingStatusHistory.objects.create(
                    booking=booking,
                    old_status=old_status,
                    new_status=booking.status,
                    changed_by=user,
                    notes=f'Status changed from {old_status} to {booking.status}',
                    timestamp=booking.created_at + timedelta(hours=random.randint(1, 48))
                )
            
            # Create payments for completed or confirmed bookings
            if booking.status in ['confirmed', 'completed', 'in_progress']:
                payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'cash']
                payment_statuses = ['completed', 'pending', 'processing']
                
                BookingPayment.objects.create(
                    booking=booking,
                    amount=booking.total_price,
                    payment_method=fake.random_element(payment_methods),
                    payment_status=fake.random_element(payment_statuses),
                    transaction_id=fake.uuid4()[:12],
                    notes=f'Payment for {booking.service.name}'
                )
            
            bookings.append(booking)
            
        self.stdout.write(f'Created {len(bookings)} test bookings')
        return bookings