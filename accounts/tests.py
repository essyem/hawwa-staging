from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class WishlistTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(
			email='test@example.com', password='password', first_name='Test', last_name='User', user_type='MOTHER'
		)

	def test_add_to_wishlist(self):
		self.client.login(email='test@example.com', password='password')
		url = reverse('accounts:add_to_wishlist')
		response = self.client.post(url, data='{"service_id": 123}', content_type='application/json')
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertTrue(data.get('success'))
		self.assertIn(123, self.client.session.get('wishlist', []))

	def test_add_to_wishlist_requires_auth_ajax(self):
		# Unauthenticated AJAX POST should get a JSON 401 with error 'login_required'
		url = reverse('accounts:add_to_wishlist')
		response = self.client.post(url, data='{"service_id": 99}', content_type='application/json')
		self.assertEqual(response.status_code, 401)
		data = response.json()
		self.assertEqual(data.get('error'), 'login_required')

# Create your tests here.
