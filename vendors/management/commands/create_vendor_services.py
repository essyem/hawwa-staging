from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from vendors.models import VendorProfile
from services.models import Service, ServiceCategory
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Link existing services to vendor profiles or create new vendor services'

    def handle(self, *args, **options):
        fake = Faker()
        
        # Get all active vendor profiles
        vendor_profiles = VendorProfile.objects.filter(status='active')
        
        if not vendor_profiles.exists():
            self.stdout.write(self.style.ERROR('No active vendor profiles found'))
            return
            
        # Get or create service categories
        categories = []
        category_names = [
            'Postpartum Care',
            'Wellness & Spa', 
            'Nutrition & Diet',
            'Baby Care',
            'Accommodation',
            'Medical Support'
        ]
        
        for cat_name in category_names:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} services for postpartum mothers'}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {cat_name}')
        
        services_created = 0
        
        for vendor_profile in vendor_profiles:
            # Create 2-4 services per vendor
            num_services = random.randint(2, 4)
            
            for _ in range(num_services):
                # Generate service names based on vendor type
                if vendor_profile.business_type == 'accommodation':
                    service_names = [
                        f"Private Recovery Room at {vendor_profile.business_name}",
                        f"Postpartum Suite with Nursing Support",
                        f"Family Accommodation Package",
                        f"Extended Stay Recovery Program"
                    ]
                elif vendor_profile.business_type == 'individual_caretaker':
                    service_names = [
                        f"24/7 Postpartum Care by {vendor_profile.user.get_full_name()}",
                        f"Daily Home Visit Care",
                        f"Night Shift Baby Care",
                        f"Breastfeeding Support Session"
                    ]
                else:  # wellness center, spa, clinic, etc.
                    service_names = [
                        f"Postpartum Massage Therapy",
                        f"Lactation Consultation",
                        f"Nutritional Counseling Session",
                        f"Mental Health Support Session",
                        f"Baby Care Workshop",
                        f"Prenatal Yoga Class"
                    ]
                
                service_name = random.choice(service_names)
                
                # Check if service already exists for this vendor
                if Service.objects.filter(name=service_name).exists():
                    continue
                    
                # Create the service
                from datetime import timedelta
                service = Service.objects.create(
                    name=service_name,
                    description=fake.text(max_nb_chars=500),
                    short_description=fake.text(max_nb_chars=150),
                    price=random.randint(100, 2000),
                    duration=timedelta(minutes=random.choice([30, 60, 90, 120, 180, 240])),
                    category=random.choice(categories),
                    status='available',
                )
                
                # Add vendor identifier to the service description
                service.description = f"Service provided by {vendor_profile.business_name}. {service.description}"
                service.save()
                
                services_created += 1
                self.stdout.write(f'Created service: {service_name} for {vendor_profile.business_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {services_created} services for {vendor_profiles.count()} vendors'
            )
        )