from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging

from ...services.currency_service import CurrencyService
from ...models import Currency

class Command(BaseCommand):
    help = 'Manage currency operations: update rates, convert amounts, view trends'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--update-rates',
            action='store_true',
            help='Update all exchange rates from external API'
        )
        
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update rates (ignore cache)'
        )
        
        parser.add_argument(
            '--convert',
            nargs=3,
            metavar=('AMOUNT', 'FROM', 'TO'),
            help='Convert amount between currencies (e.g., --convert 100 USD QAR)'
        )
        
        parser.add_argument(
            '--list-currencies',
            action='store_true',
            help='List all supported currencies'
        )
        
        parser.add_argument(
            '--currency-info',
            type=str,
            help='Get detailed information about a currency'
        )
        
        parser.add_argument(
            '--trends',
            type=str,
            help='Get currency trends for specified currency'
        )
        
        parser.add_argument(
            '--test-conversions',
            action='store_true',
            help='Test sample currency conversions'
        )
    
    def handle(self, *args, **options):
        self.currency_service = CurrencyService()
        
        self.stdout.write(
            self.style.SUCCESS("=== Advanced Currency Management System ===")
        )
        
        if options['update_rates']:
            self.update_exchange_rates(options['force_update'])
        
        elif options['convert']:
            amount, from_curr, to_curr = options['convert']
            self.convert_currency(amount, from_curr, to_curr)
        
        elif options['list_currencies']:
            self.list_currencies()
        
        elif options['currency_info']:
            self.show_currency_info(options['currency_info'])
        
        elif options['trends']:
            self.show_currency_trends(options['trends'])
        
        elif options['test_conversions']:
            self.test_conversions()
        
        else:
            self.show_currency_dashboard()
    
    def update_exchange_rates(self, force_update=False):
        """Update exchange rates from external API."""
        self.stdout.write("Updating exchange rates...")
        
        results = self.currency_service.update_exchange_rates(force_update)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        self.stdout.write(f"  📊 Exchange Rate Update Results:")
        self.stdout.write(f"     ✓ Successful: {successful}/{total}")
        
        for currency, success in results.items():
            status = "✓" if success else "✗"
            color = self.style.SUCCESS if success else self.style.WARNING
            self.stdout.write(
                color(f"     {status} {currency}")
            )
        
        # Show updated rates
        self.stdout.write("\\n  💱 Current Exchange Rates (1 QAR =):")
        for currency in Currency.objects.filter(is_active=True).order_by('code'):
            if currency.is_base_currency:
                continue
            
            self.stdout.write(
                f"     • {currency.code}: {currency.exchange_rate:.4f} {currency.symbol}"
            )
    
    def convert_currency(self, amount_str, from_currency, to_currency):
        """Convert amount between currencies."""
        try:
            amount = Decimal(amount_str)
            
            if not self.currency_service.validate_currency_pair(from_currency, to_currency):
                self.stdout.write(
                    self.style.ERROR(f"Unsupported currency pair: {from_currency}/{to_currency}")
                )
                return
            
            converted = self.currency_service.convert_amount(amount, from_currency, to_currency)
            rate = self.currency_service.get_exchange_rate(from_currency, to_currency)
            
            from_display = self.currency_service.get_currency_display(amount, from_currency)
            to_display = self.currency_service.get_currency_display(converted, to_currency)
            
            self.stdout.write(f"  💱 Currency Conversion:")
            self.stdout.write(f"     From: {from_display}")
            self.stdout.write(f"     To: {to_display}")
            self.stdout.write(f"     Rate: 1 {from_currency} = {rate:.4f} {to_currency}")
            
        except ValueError:
            self.stdout.write(
                self.style.ERROR(f"Invalid amount: {amount_str}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Conversion error: {e}")
            )
    
    def list_currencies(self):
        """List all supported currencies."""
        self.stdout.write("  🌍 Supported Currencies:")
        
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        
        for currency in currencies:
            base_indicator = " (BASE)" if currency.is_base_currency else ""
            last_updated = currency.last_updated.strftime("%Y-%m-%d %H:%M") if currency.last_updated else "Never"
            
            self.stdout.write(
                f"     • {currency.code} - {currency.name} ({currency.symbol}){base_indicator}"
            )
            self.stdout.write(
                f"       Rate: {currency.exchange_rate:.4f} | Updated: {last_updated}"
            )
    
    def show_currency_info(self, currency_code):
        """Show detailed currency information."""
        info = self.currency_service.get_currency_info(currency_code.upper())
        
        if not info:
            self.stdout.write(
                self.style.ERROR(f"Currency not found: {currency_code}")
            )
            return
        
        self.stdout.write(f"  💰 Currency Information: {info['code']}")
        self.stdout.write(f"     Name: {info['name']}")
        self.stdout.write(f"     Symbol: {info['symbol']}")
        self.stdout.write(f"     Exchange Rate: {info['exchange_rate']:.4f}")
        self.stdout.write(f"     Base Currency: {'Yes' if info['is_base'] else 'No'}")
        self.stdout.write(f"     Status: {'Active' if info['is_active'] else 'Inactive'}")
        
        if info['last_updated']:
            self.stdout.write(f"     Last Updated: {info['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show trends
        trends = info['trends']
        self.stdout.write(f"\\n  📈 Trends ({trends['period_days']} days):")
        self.stdout.write(f"     Trend: {trends['trend'].title()}")
        self.stdout.write(f"     Change: {trends['change_percent']:+.2f}%")
        self.stdout.write(f"     Volatility: {trends['volatility'].title()}")
        self.stdout.write(f"     Recommendation: {trends['recommendation'].title()}")
    
    def show_currency_trends(self, currency_code):
        """Show currency trends."""
        trends = self.currency_service.get_currency_trends(currency_code.upper())
        
        self.stdout.write(f"  📊 Currency Trends: {currency_code.upper()}")
        self.stdout.write(f"     Period: {trends['period_days']} days")
        self.stdout.write(f"     Trend Direction: {trends['trend'].title()}")
        self.stdout.write(f"     Change: {trends['change_percent']:+.2f}%")
        self.stdout.write(f"     Volatility: {trends['volatility'].title()}")
        self.stdout.write(f"     Recommendation: {trends['recommendation'].title()}")
    
    def test_conversions(self):
        """Test sample currency conversions."""
        self.stdout.write("  🧪 Testing Currency Conversions:")
        
        test_cases = [
            (1000, 'QAR', 'USD'),
            (500, 'USD', 'QAR'),
            (100, 'EUR', 'QAR'),
            (1000, 'QAR', 'AED'),
            (50, 'GBP', 'QAR'),
        ]
        
        for amount, from_curr, to_curr in test_cases:
            try:
                converted = self.currency_service.convert_amount(
                    Decimal(str(amount)), from_curr, to_curr
                )
                rate = self.currency_service.get_exchange_rate(from_curr, to_curr)
                
                from_display = self.currency_service.get_currency_display(
                    Decimal(str(amount)), from_curr
                )
                to_display = self.currency_service.get_currency_display(converted, to_curr)
                
                self.stdout.write(f"     • {from_display} → {to_display} (Rate: {rate:.4f})")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"     ✗ {from_curr}/{to_curr} failed: {e}")
                )
    
    def show_currency_dashboard(self):
        """Show currency management dashboard."""
        self.stdout.write("\\n  📊 Currency Management Dashboard:")
        
        # Currency stats
        total_currencies = Currency.objects.count()
        active_currencies = Currency.objects.filter(is_active=True).count()
        
        self.stdout.write(f"     Total Currencies: {total_currencies}")
        self.stdout.write(f"     Active Currencies: {active_currencies}")
        
        # Recent updates
        recent_updates = Currency.objects.filter(
            last_updated__isnull=False
        ).order_by('-last_updated')[:5]
        
        if recent_updates:
            self.stdout.write("\\n  🕒 Recently Updated Currencies:")
            for currency in recent_updates:
                self.stdout.write(
                    f"     • {currency.code}: {currency.last_updated.strftime('%Y-%m-%d %H:%M')}"
                )
        
        # Base currency info
        try:
            base_currency = Currency.objects.get(is_base_currency=True)
            self.stdout.write(f"\\n  🏠 Base Currency: {base_currency.code} ({base_currency.name})")
        except Currency.DoesNotExist:
            self.stdout.write(
                self.style.WARNING("\\n  ⚠️  No base currency configured")
            )
        
        self.stdout.write("\\n  💡 Available Commands:")
        self.stdout.write("     --update-rates: Update all exchange rates")
        self.stdout.write("     --convert 100 USD QAR: Convert currencies")
        self.stdout.write("     --list-currencies: List all currencies")
        self.stdout.write("     --currency-info USD: Get currency details")
        self.stdout.write("     --test-conversions: Test sample conversions")