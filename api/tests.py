from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service
from bookings.models import Booking

User = get_user_model()

class UserTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com', 
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.user = User.objects.create_user(
            email='user@example.com', 
            password='userpass123',
            first_name='Normal',
            last_name='User'
        )
        self.client = APIClient()

    def test_user_can_get_own_profile(self):
        """Test that users can retrieve their own profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_user_can_update_own_profile(self):
        """Test that users can update their own profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse('user-update-profile'),
            {'first_name': 'Updated'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')


class ServiceTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com', 
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            email='user@example.com', 
            password='userpass123'
        )
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description'
        )
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            category=self.category,
            short_description='Test service short description',
            description='Test service description',
            price=100.00,
            duration=60
        )
        self.client = APIClient()

    def test_list_services(self):
        """Test listing services is available to unauthenticated users"""
        response = self.client.get(reverse('service-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_retrieve_service(self):
        """Test retrieving a service by slug is available to unauthenticated users"""
        response = self.client.get(
            reverse('service-detail', kwargs={'slug': self.service.slug})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.service.name)

    def test_create_service_admin_only(self):
        """Test creating services requires admin privileges"""
        # Unauthenticated user cannot create service
        response = self.client.post(
            reverse('service-list'),
            {
                'name': 'New Service',
                'slug': 'new-service',
                'category': self.category.id,
                'short_description': 'New service short description',
                'description': 'New service description',
                'price': 150.00,
                'duration': 90
            }
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Normal user cannot create service
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('service-list'),
            {
                'name': 'New Service',
                'slug': 'new-service',
                'category': self.category.id,
                'short_description': 'New service short description',
                'description': 'New service description',
                'price': 150.00,
                'duration': 90
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can create service
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse('service-list'),
            {
                'name': 'New Service',
                'slug': 'new-service',
                'category': self.category.id,
                'short_description': 'New service short description',
                'description': 'New service description',
                'price': 150.00,
                'duration': 90
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Service')


class BookingTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com', 
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            email='user@example.com', 
            password='userpass123'
        )
        self.category = ServiceCategory.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            category=self.category,
            price=100.00,
            duration=60
        )
        self.client = APIClient()

    def test_create_booking(self):
        """Test that authenticated users can create bookings"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse('booking-list'),
            {
                'booking_date': '2024-07-15',
                'booking_time': '14:00:00',
                'note': 'Test booking note'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_user_can_list_own_bookings(self):
        """Test that users can list their own bookings"""
        self.client.force_authenticate(user=self.user)
        booking = Booking.objects.create(
            user=self.user,
            booking_date='2024-07-15',
            booking_time='14:00:00',
            status='pending'
        )
        response = self.client.get(reverse('booking-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], booking.id)