"""Management command to seed small fake data across apps for integration testing.
This command is intentionally lightweight and uses either Faker (if installed) or
simple deterministic values so it works in CI without external dependencies.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from change_management.models import ChangeRequest, Incident, Lead, Role, RoleAssignment

try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None


class Command(BaseCommand):
    help = 'Seed minimal fake data for integration tests'

    def handle(self, *args, **options):
        User = get_user_model()
        # create users
        users = []
        for i in range(3):
            email = f'user{i}@example.com'
            u, _ = User.objects.get_or_create(email=email, defaults={
                'first_name': f'First{i}', 'last_name': f'Last{i}', 'user_type': 'USER'
            })
            users.append(u)

        # roles
        op_role, _ = Role.objects.get_or_create(name='operator')
        RoleAssignment.objects.get_or_create(role=op_role, user=users[0])

        # change requests
        for i in range(5):
            title = (fake.sentence() if fake else f'CR Title {i}')
            ChangeRequest.objects.get_or_create(title=title, defaults={
                'description': (fake.paragraph() if fake else 'desc'),
                'reporter': users[i % len(users)]
            })

        # incidents
        for i in range(3):
            title = (fake.sentence() if fake else f'INC Title {i}')
            Incident.objects.get_or_create(title=title, defaults={
                'details': (fake.paragraph() if fake else 'details'),
                'reporter': users[i % len(users)]
            })

        # leads
        for i in range(3):
            name = (fake.name() if fake else f'Lead {i}')
            Lead.objects.get_or_create(name=name, defaults={
                'email': (fake.email() if fake else f'lead{i}@example.com')
            })

        self.stdout.write(self.style.SUCCESS('Seeded change_management fake data'))
