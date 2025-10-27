from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model


class SidebarConfigurationTests(TestCase):
    """Validate that sidebar configuration covers LOCAL_APPS and that the HRMS
    dashboard renders the configured sidebar items for an authenticated user.
    """

    def setUp(self):
        User = get_user_model()
        # create a superuser to bypass RBAC restrictions in views
        # our custom User uses email as the USERNAME_FIELD so pass email
        self.admin = User.objects.create_superuser(email='admin@example.com', password='pass')
        self.client = Client()
        # login via email (custom user model uses email as USERNAME_FIELD)
        logged_in = self.client.login(email='admin@example.com', password='pass')
        if not logged_in:
            # fallback to username login if configured differently
            self.client.login(username='admin@example.com', password='pass')

    def test_local_apps_are_listed_in_sidebar_setting(self):
        """Ensure every app in settings.LOCAL_APPS has at least one corresponding
        sidebar entry configured in settings.HAWWA_SIDEBAR_APPS. The mapping is
        fuzzy: we accept either an item whose url_name starts with '<app>:' or
        an item whose label contains the app name (case-insensitive).
        """
        local_apps = getattr(settings, 'LOCAL_APPS', [])
        sidebar = getattr(settings, 'HAWWA_SIDEBAR_APPS', []) or []

        # Flatten configured sidebar url_name and labels for quick matching
        configured_url_names = []
        configured_labels = []
        for section in sidebar:
            for item in section.get('items', []):
                url_name = item.get('url_name')
                label = item.get('label')
                if url_name:
                    configured_url_names.append(url_name)
                if label:
                    configured_labels.append(label.lower())

        missing = []
        for app in local_apps:
            # skip internal apps that don't need sidebar presence
            if app in ('accounts', 'core'):
                continue

            found = any(name.startswith(f"{app}:") for name in configured_url_names)
            if not found:
                # fallback: check label contains app name
                if not any(app.lower() in label for label in configured_labels):
                    missing.append(app)

        self.assertFalse(missing, msg=f"The following LOCAL_APPS are not represented in HAWWA_SIDEBAR_APPS: {missing}")

    def test_hrms_dashboard_renders_sidebar_items(self):
        """Request the HRMS dashboard and ensure configured sidebar labels are present
        in the rendered HTML for an authenticated superuser.
        """
        url = reverse('hrms:dashboard')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        content = resp.content.decode('utf-8')
        sidebar = getattr(settings, 'HAWWA_SIDEBAR_APPS', []) or []

        for section in sidebar:
            title = section.get('title')
            if title:
                self.assertIn(title, content, msg=f"Sidebar section title '{title}' not found in HRMS dashboard HTML")
            for item in section.get('items', []):
                label = item.get('label')
                if label:
                    self.assertIn(label, content, msg=f"Sidebar item label '{label}' not found in HRMS dashboard HTML")
