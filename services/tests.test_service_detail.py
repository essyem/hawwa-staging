from django.test import TestCase
from django.urls import reverse
from services.models import ServiceCategory, Service

class ServiceDetailSmokeTest(TestCase):
    def setUp(self):
        # Create a minimal category and service
        self.category = ServiceCategory.objects.create(name='TestCat', slug='testcat')
        self.service = Service.objects.create(
            name='Test Service',
            description='A service used for tests',
            price='100.00',
            duration='01:00:00',
            category=self.category,
            slug='test-service'
        )

    def test_service_detail_renders(self):
        url = reverse('services:service_detail', kwargs={'slug': self.service.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ensure the wishlist URL reverse was resolved by the template render
        self.assertContains(response, 'Add to Wishlist')
