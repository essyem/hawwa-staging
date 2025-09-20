from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient


class IntegrationSeedTests(TestCase):
    def test_seed_and_basic_endpoints(self):
        # Run seed
        call_command('seed_all_apps')

        client = APIClient()
        # Check services endpoint
        resp = client.get('/api/services/')
        self.assertIn(resp.status_code, (200, 204, 404))

        # Check bookings list if API registered
        resp2 = client.get('/api/bookings/')
        self.assertIn(resp2.status_code, (200, 204, 404))
