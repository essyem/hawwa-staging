from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import EmailOTP


class OTPRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_registration_creates_otp_and_verifies(self):
        email = 'test_reg@example.com'
        password = 'TestPass123'
        resp = self.client.post(reverse('accounts:register_mother'), {
            'email': email,
            'first_name': 'T',
            'last_name': 'R',
            'phone': '',
            'user_type': 'MOTHER',
            'password1': password,
            'password2': password,
            'agree_terms': 'on'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        user = self.User.objects.filter(email=email).first()
        self.assertIsNotNone(user)
        otps = EmailOTP.objects.filter(user=user)
        self.assertTrue(otps.exists())
        code = otps.first().code

        # verify
        resp2 = self.client.post(reverse('accounts:verify_email_otp'), {'email': email, 'code': code}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.wsgi_request.user.is_authenticated)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_invalid_code_does_not_verify(self):
        email = 'test_invalid@example.com'
        password = 'TestPass123'
        # create user directly
        user = self.User.objects.create_user(email=email, password=password, first_name='A', last_name='B', user_type='MOTHER')
        # create an OTP
        EmailOTP.objects.create(user=user, code='123456')

        # post with wrong code
        resp = self.client.post(reverse('accounts:verify_email_otp'), {'email': email, 'code': '000000'})
        self.assertEqual(resp.status_code, 200)
        # should not be logged in
        self.assertFalse(resp.wsgi_request.user.is_authenticated)
        user.refresh_from_db()
        self.assertFalse(user.is_verified)


class OTPExtraTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

    def test_admin_exclusion_no_otp(self):
        email = 'admin_ex@example.com'
        password = 'AdminPass123'
        # create superuser/admin
        admin = self.User.objects.create_superuser(email=email, password=password, first_name='A', last_name='B')
        # attempt login - since is_superuser, is_verified default False but login should not send OTP via LoginView
        resp = self.client.post(reverse('login'), {'username': email, 'password': password}, follow=True)
        # should be logged in (superuser) or at least not redirected to OTP flow
        self.assertTrue(resp.wsgi_request.user.is_authenticated)

    def test_resend_throttling(self):
        email = 'resend_test@example.com'
        password = 'TestPass123'
        user = self.User.objects.create_user(email=email, password=password, first_name='A', last_name='B', user_type='MOTHER')
        url = reverse('accounts:resend_email_otp')
        for i in range(3):
            resp = self.client.post(url, {'email': email})
            self.assertEqual(resp.status_code, 200)
        # fourth should be rate limited
        resp = self.client.post(url, {'email': email})
        self.assertEqual(resp.status_code, 429)

    def test_show_otp_after_password(self):
        email = 'showotp@example.com'
        password = 'ShowPass123'
        user = self.User.objects.create_user(email=email, password=password, first_name='A', last_name='B', user_type='MOTHER')
        # ensure user not verified
        self.assertFalse(user.is_verified)
        # POST to login
        resp = self.client.post(reverse('login'), {'username': email, 'password': password}, follow=False)
        # Should redirect back to login with show_otp=1
        self.assertEqual(resp.status_code, 302)
        self.assertIn('show_otp=1', resp['Location'])
        # GET the login page with show_otp=1 should include an OTP input name
        resp2 = self.client.get(reverse('login') + '?show_otp=1&email=' + email)
        html = resp2.content.decode()
        self.assertIn('One-time code', html)
