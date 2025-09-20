"""Seed several apps with minimal fake data for integration tests.
This command seeds `accounts`, `services`, `vendors`, and `bookings` with lightweight records.
It uses Faker when available, otherwise deterministic placeholders.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None


class Command(BaseCommand):
    help = 'Seed core apps (accounts, services, vendors, bookings) with minimal test data'

    def handle(self, *args, **options):
        User = get_user_model()
        users = []
        # Create a predictable superuser for demos
        try:
            if not User.objects.filter(email='admin@hawwa.com').exists():
                # Create superuser with required fields for custom user model
                try:
                    User.objects.create_superuser(email='admin@hawwa.com', password='admin123', first_name='Admin', last_name='Hawwa', user_type='ADMIN')
                except Exception:
                    u = User.objects.create(email='admin@hawwa.com', first_name='Admin', last_name='Hawwa', user_type='ADMIN')
                    u.set_password('admin123')
                    # set staff/superuser flags if available
                    try:
                        u.is_staff = True
                        u.is_superuser = True
                    except Exception:
                        pass
                    u.save()
        except Exception:
            pass

        # Create predictable demo accounts
        try:
            if not User.objects.filter(email='mother@example.com').exists():
                u = User.objects.create(email='mother@example.com', first_name='Aisha', last_name='Mother')
                u.set_password('mother123')
                u.save()
            if not User.objects.filter(email='provider@example.com').exists():
                p = User.objects.create(email='provider@example.com', first_name='Lina', last_name='Provider')
                p.set_password('provider123')
                p.save()
        except Exception:
            pass

        for i in range(5):
            email = f'integ_user{i}@example.com'
            u, _ = User.objects.get_or_create(email=email, defaults={
                'first_name': (fake.first_name() if fake else f'User{i}'),
                'last_name': (fake.last_name() if fake else 'Test'),
                # default to MOTHER for seeded users to satisfy USER_TYPE_CHOICES
                'user_type': 'MOTHER'
            })
            users.append(u)

        # Services
        try:
            from services.models import ServiceCategory, Service
            cat, _ = ServiceCategory.objects.get_or_create(name='Default Category', defaults={'description': 'seeded'})
            for i in range(5):
                name = (fake.sentence(nb_words=3) if fake else f'Service {i}')
                Service.objects.get_or_create(name=name, defaults={
                    'description': (fake.paragraph() if fake else 'desc'),
                    'price': 10.00 + i,
                    'duration': '01:00:00',
                    'category': cat,
                    'slug': f'service-{i}'
                })
        except Exception:
            pass

        # Vendors
        try:
            from vendors.models import VendorProfile
            for i in range(3):
                email = f'vendor{i}@example.com'
                VendorProfile.objects.get_or_create(email=email, defaults={
                    'name': (fake.company() if fake else f'Vendor {i}'),
                })
        except Exception:
            pass

        # Bookings (ensure there is a service and a user)
        try:
            from bookings.models import Booking
            from services.models import Service
            svc = Service.objects.first()
            if svc and users:
                for i in range(3):
                    Booking.objects.get_or_create(user=users[i % len(users)], defaults={
                        'service': svc,
                        'start_date': '2025-09-01',
                        'start_time': '09:00:00',
                        'address': '123 Test St',
                        'base_price': svc.price,
                    })
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS('Seeded minimal data across core apps'))
