import importlib
from django.test import SimpleTestCase


class AppImportSmokeTests(SimpleTestCase):
    """Attempt simple imports of each app's `models` module to catch import-time errors.

    This avoids touching the DB and fails early if an app has missing dependencies or syntax errors.
    """

    APPS_TO_CHECK = [
        'accounts', 'admin_dashboard', 'ai_buddy', 'api', 'bookings', 'core',
        'financial', 'operations', 'payments', 'reporting', 'services', 'vendors', 'wellness'
    ]

    def test_import_app_models(self):
        failures = []
        for app in self.APPS_TO_CHECK:
            module_name = f"{app}.models"
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError as mnfe:
                # If the app doesn't provide a models module, that's acceptable; skip it.
                # But if the missing module is due to a deeper import (e.g. module exists but import fails),
                # we should capture it. We differentiate by checking the exception message.
                if module_name in str(mnfe):
                    # skip absent models modules
                    continue
                failures.append((module_name, repr(mnfe)))
            except Exception as exc:  # pragma: no cover - we want to see real exceptions
                failures.append((module_name, repr(exc)))

        if failures:
            msgs = [f"{m}: {e}" for m, e in failures]
            self.fail("App import failures:\n" + "\n".join(msgs))
