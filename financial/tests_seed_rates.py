from django.test import TestCase
from django.core.management import call_command
from financial.models import CurrencyRate
from io import StringIO
from decimal import Decimal
from datetime import date

class SeedCurrencyRatesTests(TestCase):
    def test_seed_csv_dry_run(self):
        sample = """from_currency,to_currency,rate,valid_from,valid_to
USD,QAR,3.64,2025-01-01,
EUR,QAR,4.00,2025-01-01,
"""
        sio = StringIO(sample)
        # Write to a temp file
        import tempfile
        with tempfile.NamedTemporaryFile('w+', delete=False) as f:
            f.write(sample)
            tmpname = f.name
        out = StringIO()
        call_command('seed_currency_rates', tmpname, stdout=out)
        # Dry-run: objects should not be created
        self.assertEqual(CurrencyRate.objects.count(), 0)
        # Now run with commit
        call_command('seed_currency_rates', tmpname, '--commit', stdout=out)
        self.assertGreaterEqual(CurrencyRate.objects.count(), 2)
        usd = CurrencyRate.objects.filter(from_currency='USD', to_currency='QAR').first()
        self.assertIsNotNone(usd)
        self.assertEqual(usd.rate, Decimal('3.64'))
 