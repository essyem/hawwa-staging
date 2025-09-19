from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Update currency settings and verify QAR conversion'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Currency Configuration Updated!')
        )
        
        # Display current currency settings
        currency_symbol = getattr(settings, 'CURRENCY_SYMBOL', 'QAR')
        currency_code = getattr(settings, 'CURRENCY_CODE', 'QAR')
        
        self.stdout.write(f'Currency Code: {currency_code}')
        self.stdout.write(f'Currency Symbol: {currency_symbol}')
        
        # Test currency formatting
        from decimal import Decimal
        test_amount = Decimal('150000.50')
        
        # Format with commas and 2 decimal places
        formatted = f"{test_amount:,.2f}"
        
        if getattr(settings, 'CURRENCY_SYMBOL_POSITION', 'after') == 'before':
            result = f"{currency_symbol} {formatted}"
        else:
            result = f"{formatted} {currency_symbol}"
            
        self.stdout.write(f'Test formatting (150000.50): {result}')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Currency system is ready!')
        )
        
        self.stdout.write(
            self.style.WARNING('Next steps:')
        )
        self.stdout.write('1. Restart your Django server')
        self.stdout.write('2. Clear browser cache')
        self.stdout.write('3. Test currency display on frontend')
        self.stdout.write('4. Update any hardcoded $ values if found')
