"""Management command to seed CurrencyRate records from a CSV file.

CSV format expected (header): from_currency,to_currency,rate,valid_from,valid_to
Dates should be YYYY-MM-DD. valid_to may be blank for open-ended.

Usage:
    python manage.py seed_currency_rates path/to/rates.csv
"""
from django.core.management.base import BaseCommand, CommandError
from financial.models import CurrencyRate
import csv
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed currency rates from a CSV file (from_currency,to_currency,rate,valid_from,valid_to)'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to CSV file to import')
        parser.add_argument('--commit', action='store_true', help='Actually save changes (dry-run by default)')

    def handle(self, *args, **options):
        path = options['csvfile']
        commit = options['commit']
        try:
            f = open(path, newline='')
        except Exception as exc:
            raise CommandError(f'Unable to open file: {exc}')

        reader = csv.DictReader(f)
        created = 0
        updated = 0
        skipped = 0
        for i, row in enumerate(reader, start=1):
            try:
                frm = row.get('from_currency') or row.get('from')
                to = row.get('to_currency') or row.get('to')
                rate = Decimal(row.get('rate') or row.get('fx_rate') or '0')
                vf = row.get('valid_from')
                vt = row.get('valid_to')
                if not frm or not to or not rate:
                    self.stdout.write(self.style.WARNING(f'Skipping line {i}: missing required fields'))
                    skipped += 1
                    continue
                valid_from = datetime.strptime(vf, '%Y-%m-%d').date() if vf else None
                valid_to = datetime.strptime(vt, '%Y-%m-%d').date() if vt else None

                if commit:
                    obj, created_flag = CurrencyRate.objects.update_or_create(
                        from_currency=frm,
                        to_currency=to,
                        valid_from=valid_from or CurrencyRate._meta.get_field('valid_from').get_default(),
                        defaults={'rate': rate, 'valid_to': valid_to}
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                else:
                    # Dry-run: don't persist, but count as would-be created
                    created += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'Error on line {i}: {exc}'))
        f.close()
        self.stdout.write(self.style.SUCCESS(f'Done. Created: {created} Updated: {updated} Skipped: {skipped}'))
        if not commit:
            self.stdout.write(self.style.NOTICE('Dry-run: no changes were saved. Re-run with --commit to persist.'))
 