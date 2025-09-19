from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from financial.models import LedgerBalance, JournalLine, LedgerAccount
from django.db.models import Sum


class Command(BaseCommand):
    help = 'Rebuild materialized LedgerBalance from JournalLine history'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
        parser.add_argument('--reset', action='store_true', help='Reset balances to zero before rebuild')
        parser.add_argument('--account', type=str, help='Rebuild only for the account code provided')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        reset = options.get('reset')

        # Aggregate by account using DB grouping for efficiency
        accounts_qs = LedgerAccount.objects.all()
        account_code = options.get('account')
        if account_code:
            accounts_qs = accounts_qs.filter(code=account_code)
        accounts = {acct.id: acct for acct in accounts_qs}

        # Use DB aggregation on JournalLine
        jl_agg = JournalLine.objects.filter(account__in=accounts_qs).values('account').annotate(
            debits=Sum('debit'), credits=Sum('credit')
        )

        agg = {}
        for row in jl_agg:
            acct_id = row['account']
            debits = Decimal(row['debits'] or Decimal('0.00'))
            credits = Decimal(row['credits'] or Decimal('0.00'))
            acct = accounts.get(acct_id)
            if acct.account_type in ('asset', 'expense'):
                balance = debits - credits
            else:
                balance = credits - debits
            agg[acct_id] = balance

        if reset and not dry_run:
            LedgerBalance.objects.all().update(balance=Decimal('0.00'))

        changed = 0
        with transaction.atomic():
            for acct_id, balance in agg.items():
                acct = accounts.get(acct_id)
                lb, created = LedgerBalance.objects.get_or_create(account=acct, defaults={'balance': Decimal('0.00')})
                if lb.balance != balance:
                    changed += 1
                    if not dry_run:
                        lb.balance = balance
                        lb.save()

        self.stdout.write(self.style.SUCCESS(f'Rebuilt balances for {len(agg)} accounts, changed: {changed}'))
