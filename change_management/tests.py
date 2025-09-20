from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .models import ChangeRequest, Incident, Lead


class ChangeManagementModelTests(TestCase):
    def test_models_create(self):
        cr = ChangeRequest.objects.create(title='Test CR')
        inc = Incident.objects.create(title='Test Incident')
        lead = Lead.objects.create(name='Test Lead')
        self.assertIsNotNone(cr.pk)
        self.assertIsNotNone(inc.pk)
        self.assertIsNotNone(lead.pk)


class ChangeManagementAPITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='u@example.com', password='pw', first_name='A', last_name='B', user_type='ADMIN')
        self.client = APIClient()

    def test_cr_list_permission(self):
        url = '/api/change-management/change-requests/'
        # unauthenticated can list
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # authenticated can create
        self.client.force_authenticate(self.user)
        resp = self.client.post(url, {'title': 'API CR'})
        self.assertIn(resp.status_code, (200, 201))
