from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.test import Client
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.contrib.auth import get_user_model

from .models import ChangeRequest, Incident, Lead, Comment, Activity


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
        # Add a regular Django client for UI tests
        self.ui_client = Client()

    def test_cr_list_permission(self):
        url = '/api/change-management/change-requests/'
        # unauthenticated can list
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # authenticated can create
        self.client.force_authenticate(self.user)
        resp = self.client.post(url, {'title': 'API CR'})
        self.assertIn(resp.status_code, (200, 201))

    def test_role_assignment_and_permission(self):
        # create a role and assign to user
        from .models import Role, RoleAssignment
        role = Role.objects.create(name='operator')
        RoleAssignment.objects.create(role=role, user=self.user)

        # user should now be able to create CRs (same as before), but we assert role exists
        self.client.force_authenticate(self.user)
        url = '/api/change-management/change-requests/'
        resp = self.client.post(url, {'title': 'Role-based CR'})
        self.assertIn(resp.status_code, (200, 201))

    def test_comments_and_notifications(self):
        # Create CR
        cr = ChangeRequest.objects.create(title='Notify CR')
        ct = ContentType.objects.get_for_model(ChangeRequest)
        # Post comment as authenticated user
        self.client.force_authenticate(self.user)
        comment_url = '/api/change-management/comments/'
        resp = self.client.post(comment_url, {'content_type': ct.id, 'object_id': cr.id, 'text': 'Hello'})
        self.assertIn(resp.status_code, (200, 201))
        # Activity should be created and mail sent when CR was created (post_save)
        acts = Activity.objects.filter(target__contains='Notify CR')
        self.assertTrue(acts.exists())
        # An email was sent to reporter if reporter provided — in our test reporter is None so no mail yet
        # Now associate a reporter and save the CR to trigger email
        cr.reporter = self.user
        cr.save()
        self.assertTrue(len(mail.outbox) >= 1)

    def test_non_operator_cannot_set_assignee(self):
        """A regular authenticated user without operator role cannot set the assignee on a CR."""
        # create another user to be the assignee
        User = get_user_model()
        assignee = User.objects.create_user(email='assignee@example.com', password='pw', first_name='X', last_name='Y', user_type='USER')
        self.client.force_authenticate(self.user)
        # Create CR first
        create_url = '/api/change-management/change-requests/'
        resp = self.client.post(create_url, {'title': 'Attempt Assign'})
        self.assertIn(resp.status_code, (200, 201))
        cr_id = resp.json().get('id')
        assign_url = f'/api/change-management/change-requests/{cr_id}/assign/'
        resp2 = self.client.post(assign_url, {'assignee': assignee.id})
        self.assertIn(resp2.status_code, (400, 403))

    def test_operator_can_set_assignee(self):
        """A user with operator role can set the assignee on a CR."""
        from .models import Role, RoleAssignment
        Role.objects.create(name='operator')
        RoleAssignment.objects.create(role=Role.objects.get(name='operator'), user=self.user)

        User = get_user_model()
        assignee = User.objects.create_user(email='opassignee@example.com', password='pw', first_name='O', last_name='P', user_type='USER')
        self.client.force_authenticate(self.user)
        create_url = '/api/change-management/change-requests/'
        resp = self.client.post(create_url, {'title': 'Operator Assign'})
        self.assertIn(resp.status_code, (200, 201))
        cr_id = resp.json().get('id')
        assign_url = f'/api/change-management/change-requests/{cr_id}/assign/'
        resp2 = self.client.post(assign_url, {'assignee': assignee.id})
        self.assertIn(resp2.status_code, (200, 201))

    def test_admin_dashboard_and_assign_action(self):
        # create a staff user for admin access
        User = get_user_model()
        # create a CR
        cr = ChangeRequest.objects.create(title='Admin Assign CR')

        client = self.client
        # make superuser and force login to admin
        admin_user = get_user_model().objects.create_superuser(email='admin@example.com', password='pw', first_name='Ad', last_name='Min', user_type='ADMIN')
        client.force_login(admin_user)

        # access change list page
        resp = client.get('/admin/change_management/changerequest/')
        self.assertIn(resp.status_code, (200, 302))

        # Post admin action to the changelist to trigger intermediate page
        post_data = {
            'action': 'assign_to_user_action',
            '_selected_action': [str(cr.pk)],
        }
        resp2 = client.post('/admin/change_management/changerequest/', post_data)
        # intermediate page should render (200) or redirect
        self.assertIn(resp2.status_code, (200, 302))

    def test_cr_detail_post_comment_regular_and_ajax(self):
        # create a CR for UI tests
        cr = ChangeRequest.objects.create(title='UI CR', reporter=self.user)
        url = f'/api/change-management/ui/change-request/{cr.pk}/'

        # regular POST
        self.ui_client.force_login(self.user)
        resp = self.ui_client.post(url, {'text': 'Hello UI'})
        self.assertIn(resp.status_code, (200, 302))
        ct = ContentType.objects.get_for_model(ChangeRequest)
        self.assertTrue(Comment.objects.filter(content_type=ct, object_id=cr.pk, text='Hello UI').exists())

        # AJAX POST
        resp2 = self.ui_client.post(url, {'text': 'Hello AJAX'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(Comment.objects.filter(content_type=ct, object_id=cr.pk, text='Hello AJAX').exists())
