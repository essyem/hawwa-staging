"""
Management command to create enhanced admin superuser with advanced capabilities.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Create enhanced superuser for Hawwa platform administration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Superuser email address',
            default='essyem@hawwa.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Superuser password',
            default='HawwaAdmin2025!'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Superuser first name',
            default='Super'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Superuser last name',
            default='Admin'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if superuser already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with email {email} already exists.')
            )
            
            # Ask if we should update the existing user
            response = input('Do you want to update the existing user? (y/N): ')
            if response.lower() != 'y':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return
            
            # Update existing user
            user = User.objects.get(email=email)
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.is_verified = True
            user.user_type = 'ADMIN'
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated superuser: {email}')
            )
        else:
            # Create new superuser
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        user_type='ADMIN',
                        is_staff=True,
                        is_superuser=True,
                        is_active=True,
                        is_verified=True
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully created superuser: {email}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating superuser: {str(e)}')
                )
                return

        # Display login information
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SUPERUSER CREATED/UPDATED SUCCESSFULLY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Name: {first_name} {last_name}')
        self.stdout.write('\nAdmin Access URLs:')
        self.stdout.write('- Standard Django Admin: /admin/')
        self.stdout.write('- Enhanced Hawwa Admin: /hawwa-admin/')
        self.stdout.write('- Platform Dashboard: /admin-dashboard/')
        self.stdout.write('\nCapabilities:')
        self.stdout.write('✓ Full platform administration')
        self.stdout.write('✓ User unregistration/management')
        self.stdout.write('✓ Bulk user operations')
        self.stdout.write('✓ System health monitoring')
        self.stdout.write('✓ Platform statistics')
        self.stdout.write('✓ Enhanced admin features')
        self.stdout.write('='*50 + '\n')