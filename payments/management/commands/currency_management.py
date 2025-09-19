from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.services.currency_service import CurrencyService
from payments.models import Currency
from decimal import Decimal

class Command(BaseCommand):
    help = 'Manage multi-currency operations and exchange rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-rates',
            action='store_true',
            help='Update all exchange rates'
        )
        
        parser.add_argument(
            '--currency-info',
            type=str,
            help='Get information about specific currency'
        )
        
        parser.add_argument(
            '--convert',
            nargs=3,
            metavar=('AMOUNT', 'FROM', 'TO'),
            help='Convert amount between currencies (amount from_currency to_currency)'
        )
        
        parser.add_argument(
            '--list-currencies',
            action='store_true',
            help='List all supported currencies'
        )
        
        parser.add_argument(
            '--rate-history',
            nargs=2,
            metavar=('FROM', 'TO'),
            help='Show exchange rate history for currency pair'
        )
        
        parser.add_argument(
            '--multi-convert',
            nargs=2,
            metavar=('AMOUNT', 'FROM'),
            help='Convert amount to all supported currencies'
        )
        
        parser.add_argument(
            '--exchange-summary',
            action='store_true',
            help='Display exchange rate summary'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Multi-Currency Management ===')
        )
        
        service = CurrencyService()
        
        if options['update_rates']:
            self.update_exchange_rates(service)
        
        if options['currency_info']:
            self.show_currency_info(service, options['currency_info'])
        
        if options['convert']:
            amount, from_curr, to_curr = options['convert']
            self.convert_currency(service, amount, from_curr, to_curr)
        
        if options['list_currencies']:
            self.list_currencies(service)
        
        if options['rate_history']:
            from_curr, to_curr = options['rate_history']
            self.show_rate_history(service, from_curr, to_curr)
        
        if options['multi_convert']:
            amount, from_curr = options['multi_convert']
            self.multi_currency_convert(service, amount, from_curr)
        
        if options['exchange_summary']:
            self.show_exchange_summary(service)
        
        if not any(options.values()):
            self.display_help()

    def update_exchange_rates(self, service):
        self.stdout.write("Updating exchange rates...")
        
        try:
            results = service.update_all_exchange_rates()
            
            self.stdout.write(f"  ✓ Updated: {results['updated']} currencies")
            
            if results['failed'] > 0:
                self.stdout.write(f"  ❌ Failed: {results['failed']} currencies")
                for error in results['errors']:
                    self.stdout.write(f"     - {error}")
            
            self.stdout.write(self.style.SUCCESS("Exchange rates updated successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to update exchange rates: {e}"))

    def show_currency_info(self, service, currency_code):
        self.stdout.write(f"Currency information for {currency_code}...")
        
        try:
            info = service.get_currency_info(currency_code.upper())
            
            if 'error' in info:
                self.stdout.write(self.style.ERROR(f"  ❌ {info['error']}"))
                return
            
            self.stdout.write(f"  💰 {info['name']} ({info['code']})")
            self.stdout.write(f"     Symbol: {info['symbol']}")
            self.stdout.write(f"     Active: {'Yes' if info['is_active'] else 'No'}")
            self.stdout.write(f"     Exchange rate to QAR: {info['exchange_rate_to_base']}")
            
            trend = info.get('trend', {})
            if trend:
                trend_icon = "📈" if trend['trend'] == 'rising' else "📉" if trend['trend'] == 'falling' else "➡️"
                self.stdout.write(f"     Trend (30 days): {trend_icon} {trend['trend'].title()} ({trend['change']:+.2f}%)")
            
            self.stdout.write(f"     Last updated: {info['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting currency info: {e}"))

    def convert_currency(self, service, amount_str, from_currency, to_currency):
        self.stdout.write(f"Converting {amount_str} {from_currency} to {to_currency}...")
        
        try:
            amount = Decimal(amount_str)
            from_curr = from_currency.upper()
            to_curr = to_currency.upper()
            
            # Validate currencies
            if not service.validate_currency_pair(from_curr, to_curr):
                self.stdout.write(self.style.ERROR("Invalid currency pair"))
                return
            
            converted_amount = service.convert_amount(amount, from_curr, to_curr)
            exchange_rate = service.get_exchange_rate(from_curr, to_curr)
            
            from_symbol = Currency.objects.get(code=from_curr).symbol
            to_symbol = Currency.objects.get(code=to_curr).symbol
            
            self.stdout.write(f"  💱 {from_symbol}{amount} {from_curr} = {to_symbol}{converted_amount} {to_curr}")
            self.stdout.write(f"     Exchange rate: 1 {from_curr} = {exchange_rate} {to_curr}")
            
        except ValueError:
            self.stdout.write(self.style.ERROR("Invalid amount format"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Conversion failed: {e}"))

    def list_currencies(self, service):
        self.stdout.write("Supported currencies...")
        
        try:
            currency_codes = service.get_supported_currencies()
            
            if not currency_codes:
                self.stdout.write("  No currencies found")
                return
            
            self.stdout.write(f"\n  💰 Supported Currencies ({len(currency_codes)}):")
            
            for currency_code in currency_codes:
                try:
                    currency_info = service.get_currency_info(currency_code)
                    if not currency_info:
                        self.stdout.write(f"     {currency_code} (not configured)")
                        continue
                    
                    rate_info = ""
                    if currency_code != 'QAR':
                        rate_info = f" (1 {currency_code} = {currency_info['exchange_rate']} QAR)"
                    
                    status = "✓" if currency_info['is_active'] else "❌"
                    
                    self.stdout.write(f"     {status} {currency_info['symbol']} {currency_info['name']} ({currency_code}){rate_info}")
                    
                except Exception as e:
                    self.stdout.write(f"     ❌ {currency_code} (error: {str(e)})")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to list currencies: {e}"))

    def show_rate_history(self, service, from_currency, to_currency):
        self.stdout.write(f"Exchange rate history for {from_currency} to {to_currency}...")
        
        try:
            from_curr = from_currency.upper()
            to_curr = to_currency.upper()
            
            history = service.get_exchange_rate_history(from_curr, to_curr, days=30)
            
            if not history:
                self.stdout.write("  No exchange rate history found")
                return
            
            self.stdout.write(f"\n  📊 Exchange Rate History (Last 30 days):")
            self.stdout.write(f"     {from_curr} → {to_curr}")
            self.stdout.write("     " + "="*50)
            
            for entry in history[-10:]:  # Show last 10 entries
                self.stdout.write(f"     {entry['date']}: {entry['rate']:.6f} ({entry['source']})")
            
            if len(history) > 10:
                self.stdout.write(f"     ... and {len(history) - 10} more entries")
            
            # Calculate trend
            if len(history) >= 2:
                first_rate = history[0]['rate']
                last_rate = history[-1]['rate']
                change = ((last_rate - first_rate) / first_rate) * 100
                
                trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                self.stdout.write(f"\n     {trend_icon} 30-day change: {change:+.2f}%")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to get rate history: {e}"))

    def multi_currency_convert(self, service, amount_str, from_currency):
        self.stdout.write(f"Converting {amount_str} {from_currency} to all currencies...")
        
        try:
            amount = Decimal(amount_str)
            from_curr = from_currency.upper()
            
            conversions = service.get_multi_currency_summary(amount, from_curr)
            
            from_curr_info = service.get_currency_info(from_curr)
            from_symbol = from_curr_info['symbol'] if from_curr_info else from_curr
            
            self.stdout.write(f"\n  💱 {from_symbol}{amount} {from_curr} converts to:")
            self.stdout.write("     " + "="*60)
            
            for curr_code, conversion in conversions.items():
                if 'error' in conversion:
                    self.stdout.write(f"     ❌ {curr_code} - {conversion['error']}")
                else:
                    self.stdout.write(f"     {conversion['symbol']}{conversion['amount']:.2f} {curr_code}")
            
            self.stdout.write(f"\n     Conversion completed at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except ValueError:
            self.stdout.write(self.style.ERROR("Invalid amount format"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Multi-currency conversion failed: {e}"))

    def show_exchange_summary(self, service):
        self.stdout.write("Exchange rate summary...")
        
        try:
            # Get all active currencies
            currencies = Currency.objects.filter(is_active=True).order_by('name')
            
            if not currencies:
                self.stdout.write("  No active currencies found")
                return
            
            self.stdout.write(f"\n  📈 Exchange Rate Summary ({currencies.count()} currencies):")
            self.stdout.write("     " + "="*80)
            
            for currency in currencies:
                if currency.code == 'QAR':
                    self.stdout.write(f"     {currency.symbol} {currency.name} ({currency.code}) - BASE CURRENCY")
                    continue
                
                try:
                    rate_to_qar = service.get_exchange_rate(currency.code, 'QAR')
                    rate_from_qar = service.get_exchange_rate('QAR', currency.code)
                    
                    # Get trend
                    info = service.get_currency_info(currency.code)
                    trend = info.get('trend', {})
                    trend_icon = ""
                    if trend:
                        trend_icon = " 📈" if trend['trend'] == 'rising' else " 📉" if trend['trend'] == 'falling' else " ➡️"
                    
                    self.stdout.write(f"     {currency.symbol} {currency.name} ({currency.code})")
                    self.stdout.write(f"        1 {currency.code} = {rate_to_qar} QAR")
                    self.stdout.write(f"        1 QAR = {rate_from_qar} {currency.code}{trend_icon}")
                    
                except Exception as e:
                    self.stdout.write(f"     {currency.symbol} {currency.name} ({currency.code}) - Rate unavailable")
            
            # Summary
            self.stdout.write(f"\n  📊 Exchange Rate Summary:")
            self.stdout.write(f"     Total currencies configured: {Currency.objects.count()}")
            self.stdout.write(f"     Active currencies: {Currency.objects.filter(is_active=True).count()}")
            self.stdout.write(f"     Last updated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to generate summary: {e}"))

    def display_help(self):
        self.stdout.write("\n Available commands:")
        self.stdout.write("  --update-rates                Update all exchange rates")
        self.stdout.write("  --currency-info CODE          Get currency information")
        self.stdout.write("  --convert AMOUNT FROM TO      Convert amount between currencies")
        self.stdout.write("  --list-currencies             List all supported currencies")
        self.stdout.write("  --rate-history FROM TO        Show exchange rate history")
        self.stdout.write("  --multi-convert AMOUNT FROM   Convert to all currencies")
        self.stdout.write("  --exchange-summary            Display exchange rate summary")
        self.stdout.write("\n Example usage:")
        self.stdout.write("  python manage.py currency_management --update-rates")
        self.stdout.write("  python manage.py currency_management --convert 100 USD QAR")
        self.stdout.write("  python manage.py currency_management --currency-info USD")
        self.stdout.write("  python manage.py currency_management --multi-convert 1000 QAR")