import requests
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional
import logging

from ..models import Currency

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service for currency management and exchange rate operations."""
    
    def __init__(self):
        self.base_currency = 'QAR'  # Qatari Riyal as base currency
        self.api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
        self.cache_timeout = 3600  # 1 hour cache for exchange rates
        
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        return [
            'QAR',  # Qatari Riyal (base)
            'USD',  # US Dollar
            'EUR',  # Euro
            'GBP',  # British Pound
            'AED',  # UAE Dirham
            'SAR',  # Saudi Riyal
            'KWD',  # Kuwaiti Dinar
            'BHD',  # Bahraini Dinar
            'OMR',  # Omani Rial
            'JPY',  # Japanese Yen
            'CNY',  # Chinese Yuan
            'INR',  # Indian Rupee
        ]
    
    def update_exchange_rates(self, force_update: bool = False) -> Dict[str, bool]:
        """Update exchange rates from external API."""
        results = {}
        
        for currency_code in self.get_supported_currencies():
            if currency_code == self.base_currency:
                # Ensure base currency exists with rate 1.0
                currency, created = Currency.objects.get_or_create(
                    code=currency_code,
                    defaults={
                        'name': 'Qatari Riyal',
                        'symbol': 'QAR',
                        'exchange_rate_to_qar': Decimal('1.0'),
                        'is_active': True
                    }
                )
                results[currency_code] = True
                continue
            
            try:
                # Check cache first unless force update
                cache_key = f'exchange_rate_{currency_code}'
                if not force_update:
                    cached_rate = cache.get(cache_key)
                    if cached_rate:
                        self._update_currency_rate(currency_code, cached_rate)
                        results[currency_code] = True
                        continue
                
                # Fetch from API
                rate = self._fetch_exchange_rate(currency_code)
                if rate:
                    self._update_currency_rate(currency_code, rate)
                    cache.set(cache_key, rate, self.cache_timeout)
                    results[currency_code] = True
                else:
                    # Use fallback rates if API fails
                    fallback_rate = self._get_fallback_rate(currency_code)
                    self._update_currency_rate(currency_code, fallback_rate)
                    results[currency_code] = False
                    logger.warning(f"Using fallback rate for {currency_code}")
                    
            except Exception as e:
                logger.error(f"Error updating exchange rate for {currency_code}: {e}")
                results[currency_code] = False
        
        return results
    
    def update_all_exchange_rates(self, force_update: bool = False) -> Dict:
        """Update all exchange rates and return summary."""
        results = self.update_exchange_rates(force_update)
        
        updated_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - updated_count
        
        return {
            'updated': updated_count,
            'failed': failed_count,
            'total': len(results),
            'results': results,
            'errors': []
        }
    
    def _fetch_exchange_rate(self, currency_code: str) -> Optional[Decimal]:
        """Fetch exchange rate from external API."""
        try:
            # Using free exchangerate-api.com (fallback to hardcoded rates if no API key)
            if self.api_key:
                url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/pair/{self.base_currency}/{currency_code}"
            else:
                # Use free tier without API key (limited requests)
                url = f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if self.api_key:
                # Direct pair rate
                return Decimal(str(data.get('conversion_rate', 0)))
            else:
                # Extract rate from rates object
                rates = data.get('rates', {})
                return Decimal(str(rates.get(currency_code, 0)))
                
        except Exception as e:
            logger.error(f"API request failed for {currency_code}: {e}")
            return None
    
    def _get_fallback_rate(self, currency_code: str) -> Decimal:
        """Get fallback exchange rates (approximate rates for QAR)."""
        fallback_rates = {
            'USD': Decimal('0.27'),    # 1 QAR = 0.27 USD
            'EUR': Decimal('0.25'),    # 1 QAR = 0.25 EUR
            'GBP': Decimal('0.22'),    # 1 QAR = 0.22 GBP
            'AED': Decimal('1.01'),    # 1 QAR = 1.01 AED
            'SAR': Decimal('1.03'),    # 1 QAR = 1.03 SAR
            'KWD': Decimal('0.08'),    # 1 QAR = 0.08 KWD
            'BHD': Decimal('0.10'),    # 1 QAR = 0.10 BHD
            'OMR': Decimal('0.11'),    # 1 QAR = 0.11 OMR
            'JPY': Decimal('40.50'),   # 1 QAR = 40.50 JPY
            'CNY': Decimal('1.95'),    # 1 QAR = 1.95 CNY
            'INR': Decimal('22.80'),   # 1 QAR = 22.80 INR
        }
        
        return fallback_rates.get(currency_code, Decimal('1.0'))
    
    def _update_currency_rate(self, currency_code: str, rate: Decimal):
        """Update currency rate in database."""
        currency_names = {
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'AED': 'UAE Dirham',
            'SAR': 'Saudi Riyal',
            'KWD': 'Kuwaiti Dinar',
            'BHD': 'Bahraini Dinar',
            'OMR': 'Omani Rial',
            'JPY': 'Japanese Yen',
            'CNY': 'Chinese Yuan',
            'INR': 'Indian Rupee',
        }
        
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'AED': 'AED',
            'SAR': 'SAR',
            'KWD': 'KWD',
            'BHD': 'BHD',
            'OMR': 'OMR',
            'JPY': '¥',
            'CNY': '¥',
            'INR': '₹',
        }
        
        currency, created = Currency.objects.get_or_create(
            code=currency_code,
            defaults={
                'name': currency_names.get(currency_code, currency_code),
                'symbol': currency_symbols.get(currency_code, currency_code),
                'exchange_rate_to_qar': rate,
                'is_active': True
            }
        )
        
        if not created:
            currency.exchange_rate_to_qar = rate
            currency.last_updated = timezone.now()
            currency.save()
    
    def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return amount
        
        try:
            from_curr = Currency.objects.get(code=from_currency, is_active=True)
            to_curr = Currency.objects.get(code=to_currency, is_active=True)
            
            # Convert to base currency first, then to target currency
            if from_currency != self.base_currency:
                # Convert from source to base (QAR)
                base_amount = amount / from_curr.exchange_rate_to_qar
            else:
                base_amount = amount
            
            if to_currency != self.base_currency:
                # Convert from base to target
                converted_amount = base_amount * to_curr.exchange_rate_to_qar
            else:
                converted_amount = base_amount
            
            return converted_amount.quantize(Decimal('0.01'))
            
        except Currency.DoesNotExist:
            logger.error(f"Currency not found: {from_currency} or {to_currency}")
            return amount
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return amount

    def get_multi_currency_summary(self, amount: Decimal, from_currency: str) -> Dict:
        """Convert amount to all supported currencies."""
        results = {}
        
        for currency_code in self.get_supported_currencies():
            if currency_code == from_currency:
                results[currency_code] = {
                    'amount': amount,
                    'symbol': from_currency,
                    'rate': Decimal('1.0')
                }
                continue
                
            try:
                converted = self.convert_amount(amount, from_currency, currency_code)
                currency_info = self.get_currency_info(currency_code)
                
                results[currency_code] = {
                    'amount': converted,
                    'symbol': currency_info['symbol'] if currency_info else currency_code,
                    'rate': converted / amount if amount > 0 else Decimal('0')
                }
            except Exception as e:
                results[currency_code] = {
                    'error': str(e),
                    'amount': Decimal('0'),
                    'symbol': currency_code,
                    'rate': Decimal('0')
                }
        
        return results
    
    def get_currency_display(self, amount: Decimal, currency_code: str) -> str:
        """Format amount with currency symbol."""
        try:
            currency = Currency.objects.get(code=currency_code)
            return f"{currency.symbol} {amount:,.2f}"
        except Currency.DoesNotExist:
            return f"{currency_code} {amount:,.2f}"
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """Get exchange rate between two currencies."""
        if from_currency == to_currency:
            return Decimal('1.0')
        
        try:
            # Convert 1 unit of from_currency to to_currency
            return self.convert_amount(Decimal('1.0'), from_currency, to_currency)
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return None
    
    def get_currency_trends(self, currency_code: str, days: int = 30) -> Dict:
        """Get currency trends over specified period."""
        # This would typically query historical exchange rate data
        # For now, return sample trend data
        return {
            'currency': currency_code,
            'period_days': days,
            'trend': 'stable',  # up, down, stable
            'change_percent': Decimal('0.5'),
            'volatility': 'low',  # low, medium, high
            'recommendation': 'hold'  # buy, sell, hold
        }
    
    def validate_currency_pair(self, from_currency: str, to_currency: str) -> bool:
        """Validate if currency pair is supported."""
        supported = self.get_supported_currencies()
        return from_currency in supported and to_currency in supported
    
    def get_currency_info(self, currency_code: str) -> Optional[Dict]:
        """Get comprehensive currency information."""
        try:
            currency = Currency.objects.get(code=currency_code)
            return {
                'code': currency.code,
                'name': currency.name,
                'symbol': currency.symbol,
                'exchange_rate': currency.exchange_rate_to_qar,
                'last_updated': currency.last_updated,
                'is_active': currency.is_active
            }
        except Currency.DoesNotExist:
            return None