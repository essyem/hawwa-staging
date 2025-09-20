from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model

from .models import ChangeRequest, Incident, Activity


class SignalsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='siguser@example.com', password='pw', first_name='S', last_name='T', user_type='USER')

    def test_change_request_signal_activity_and_email(self):
        # Create a CR -> Activity should be created even if reporter is None
        cr = ChangeRequest.objects.create(title='Signal CR')
        acts = Activity.objects.filter(target__contains='Signal CR')
        self.assertTrue(acts.exists())

        # No email sent because reporter is None by default
        self.assertEqual(len(mail.outbox), 0)

        # Associate reporter and save -> email should be sent
        cr.reporter = self.user
        cr.save()
        self.assertTrue(len(mail.outbox) >= 1)

    def test_incident_signal_activity_and_email(self):
        inc = Incident.objects.create(title='Signal Incident')
        acts = Activity.objects.filter(target__contains='Signal Incident')
        self.assertTrue(acts.exists())

        # No email yet
        self.assertEqual(len(mail.outbox), 0)

        inc.reporter = self.user
        inc.save()
        self.assertTrue(len(mail.outbox) >= 1)
