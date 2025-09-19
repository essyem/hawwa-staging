from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from vendors.models import VendorProfile
from services.models import Service
from bookings.models import Booking
from django.db.models import Q
from faker import Faker
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create realistic bookings for vendor services'

    def handle(self, *args, **options):
        fake = Faker()
        
        # Get all active vendor profiles
        vendor_profiles = VendorProfile.objects.filter(status='active')
        
        if not vendor_profiles.exists():
            self.stdout.write(self.style.ERROR('No active vendor profiles found'))
            return
            
        # Get regular users (non-vendors) to be customers
        vendor_users = [vp.user for vp in vendor_profiles]
        customer_users = User.objects.exclude(id__in=[vu.id for vu in vendor_users])
        
        if not customer_users.exists():
            self.stdout.write(self.style.ERROR('No customer users found'))
            return
            
        bookings_created = 0
        
        for vendor_profile in vendor_profiles:
            # Get services for this vendor
            vendor_services = Service.objects.filter(
                Q(description__icontains=vendor_profile.business_name) |
                Q(name__icontains=vendor_profile.business_name.split()[0])
            )
            
            if not vendor_services.exists():
                self.stdout.write(f'No services found for {vendor_profile.business_name}')
                continue
            
            # Create 3-8 bookings per vendor
            num_bookings = random.randint(3, 8)
            
            for _ in range(num_bookings):
                # Random customer
                customer = random.choice(customer_users)
                
                # Random service
                service = random.choice(vendor_services)
                
                # Random date in the past 60 days or future 30 days
                days_offset = random.randint(-60, 30)
                booking_date = timezone.now().date() + timedelta(days=days_offset)
                
                # Random time
                booking_time = fake.time_object()
                
                # Random status based on date
                if booking_date < timezone.now().date():
                    # Past bookings are mostly completed
                    status = random.choices(
                        ['completed', 'cancelled', 'no_show'],
                        weights=[80, 15, 5]
                    )[0]
                elif booking_date == timezone.now().date():
                    # Today's bookings
                    status = random.choices(
                        ['confirmed', 'in_progress', 'completed'],
                        weights=[40, 30, 30]
                    )[0]
                else:
                    # Future bookings
                    status = random.choices(
                        ['pending', 'confirmed'],
                        weights=[30, 70]
                    )[0]
                
                # Calculate pricing
                base_price = service.price
                # Add some variation (+/- 20%)
                price_variation = random.uniform(0.8, 1.2)
                total_price = base_price * Decimal(str(price_variation))
                
                # Generate booking number
                booking_number = f'BK{fake.unique.random_number(digits=8)}'
                
                try:
                    booking = Booking.objects.create(
                        user=customer,
                        service=service,
                        booking_number=booking_number,
                        start_date=booking_date,
                        start_time=booking_time,
                        end_date=booking_date,
                        end_time=(datetime.combine(booking_date, booking_time) + service.duration).time(),
                        status=status,
                        base_price=service.price,
                        total_price=total_price,
                        address=fake.address(),
                        city='Doha',
                        special_instructions=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                        client_phone=fake.phone_number(),
                        client_email=customer.email,
                    )
                    
                    bookings_created += 1
                    self.stdout.write(f'Created booking {booking_number} for {vendor_profile.business_name} - {service.name}')
                    
                except Exception as e:
                    self.stdout.write(f'Error creating booking: {e}')
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {bookings_created} bookings for vendor services'
            )
        )