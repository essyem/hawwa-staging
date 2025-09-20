import importlib
from django.test import SimpleTestCase


class AppImportSmokeTests(SimpleTestCase):
    """Attempt simple imports of each app's `models` module to catch import-time errors.

    This avoids touching the DB and fails early if an app has missing dependencies or syntax errors.
    """

    APPS_TO_CHECK = [
        'accounts', 'admin_dashboard', 'ai_buddy', 'api', 'bookings', 'core',
        'finance' if False else 'financial', 'financial', 'operations', 'payments',
        'reporting', 'services', 'vendors', 'wellness'
    ]

    def test_import_app_models(self):
        failures = []
        for app in self.APPS_TO_CHECK:
            module_name = f"{app}.models"
            try:
                importlib.import_module(module_name)
            except Exception as exc:  # pragma: no cover - we want to see real exceptions
                failures.append((module_name, repr(exc)))

        if failures:
            msgs = [f"{m}: {e}" for m, e in failures]
            self.fail("App import failures:\n" + "\n".join(msgs))
