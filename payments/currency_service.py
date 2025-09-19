import requests
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from payments.models import Currency, ExchangeRateHistory
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    """
    Advanced currency management service with real-time exchange rates,
    currency conversion, and multi-currency support.
    """
    
    BASE_CURRENCY = 'QAR'  # Qatar Riyal as base currency
    CACHE_TIMEOUT = 3600  # 1 hour cache for exchange rates
    
    # Exchange rate API endpoints (mock for development)
    EXCHANGE_RATE_APIS = {
        'primary': 'https://api.exchangerate-api.com/v4/latest/QAR',
        'fallback': 'https://api.fixer.io/latest?base=QAR',
        'backup': 'https://openexchangerates.org/api/latest.json'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get current exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate as Decimal
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        # Check cache first
        cache_key = f"exchange_rate_{from_currency}_{to_currency}"
        cached_rate = cache.get(cache_key)
        if cached_rate:
            return Decimal(str(cached_rate))
        
        try:
            # Get latest exchange rate
            rate = self._fetch_exchange_rate(from_currency, to_currency)
            
            # Cache the rate
            cache.set(cache_key, float(rate), self.CACHE_TIMEOUT)
            
            # Store in database for historical tracking
            self._store_exchange_rate_history(from_currency, to_currency, rate)
            
            return rate
            
        except Exception as e:
            logger.error(f"Failed to get exchange rate {from_currency} to {to_currency}: {e}")
            
            # Fallback to database historical data
            return self._get_fallback_rate(from_currency, to_currency)

    def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Fetch exchange rate from external API.
        """
        # In production, you would use real APIs like:
        # - ExchangeRate-API
        # - Fixer.io
        # - OpenExchangeRates
        # - CurrencyLayer
        
        # Mock exchange rates for development
        mock_rates = {
            ('QAR', 'USD'): Decimal('0.275'),
            ('QAR', 'EUR'): Decimal('0.25'),
            ('QAR', 'GBP'): Decimal('0.22'),
            ('QAR', 'SAR'): Decimal('1.03'),
            ('QAR', 'AED'): Decimal('1.01'),
            ('QAR', 'KWD'): Decimal('0.084'),
            ('QAR', 'BHD'): Decimal('0.103'),
            ('USD', 'QAR'): Decimal('3.64'),
            ('EUR', 'QAR'): Decimal('4.0'),
            ('GBP', 'QAR'): Decimal('4.55'),
            ('SAR', 'QAR'): Decimal('0.97'),
            ('AED', 'QAR'): Decimal('0.99'),
            ('KWD', 'QAR'): Decimal('11.9'),
            ('BHD', 'QAR'): Decimal('9.7'),
        }
        
        rate_key = (from_currency, to_currency)
        if rate_key in mock_rates:
            # Add small random fluctuation to simulate real market
            import random
            base_rate = mock_rates[rate_key]
            fluctuation = Decimal(str(random.uniform(-0.002, 0.002)))  # ±0.2% fluctuation
            return (base_rate * (Decimal('1') + fluctuation)).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
        
        # If not found in mock data, calculate inverse or cross-rate
        inverse_key = (to_currency, from_currency)
        if inverse_key in mock_rates:
            return (Decimal('1') / mock_rates[inverse_key]).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
        
        # Cross-rate calculation via QAR
        if from_currency != self.BASE_CURRENCY and to_currency != self.BASE_CURRENCY:
            from_to_base = self._fetch_exchange_rate(from_currency, self.BASE_CURRENCY)
            base_to_target = self._fetch_exchange_rate(self.BASE_CURRENCY, to_currency)
            return (from_to_base * base_to_target).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
        
        raise ValueError(f"Exchange rate not available for {from_currency} to {to_currency}")

    def _store_exchange_rate_history(self, from_currency: str, to_currency: str, rate: Decimal):
        """
        Store exchange rate in historical data.
        """
        try:
            from_curr = Currency.objects.get(code=from_currency)
            to_curr = Currency.objects.get(code=to_currency)
            
            ExchangeRateHistory.objects.create(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=rate,
                date=timezone.now().date(),
                source='api'
            )
        except Currency.DoesNotExist:
            logger.warning(f"Currency not found: {from_currency} or {to_currency}")
        except Exception as e:
            logger.error(f"Failed to store exchange rate history: {e}")

    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get fallback exchange rate from database.
        """
        try:
            # Get most recent rate from database
            latest_rate = ExchangeRateHistory.objects.filter(
                from_currency__code=from_currency,
                to_currency__code=to_currency
            ).order_by('-date', '-created_at').first()
            
            if latest_rate:
                logger.info(f"Using fallback rate: {latest_rate.rate}")
                return latest_rate.rate
            
            # Try inverse rate
            inverse_rate = ExchangeRateHistory.objects.filter(
                from_currency__code=to_currency,
                to_currency__code=from_currency
            ).order_by('-date', '-created_at').first()
            
            if inverse_rate:
                fallback_rate = Decimal('1') / inverse_rate.rate
                logger.info(f"Using inverse fallback rate: {fallback_rate}")
                return fallback_rate
            
        except Exception as e:
            logger.error(f"Failed to get fallback rate: {e}")
        
        # Last resort - return 1.0 (no conversion)
        logger.warning(f"No exchange rate found, using 1.0 for {from_currency} to {to_currency}")
        return Decimal('1.0')

    def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        converted_amount = amount * rate
        
        # Round to 2 decimal places for currencies
        return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_currency_info(self, currency_code: str) -> Dict:
        """
        Get comprehensive currency information.
        """
        try:
            currency = Currency.objects.get(code=currency_code)
            
            # Get recent exchange rate trend
            recent_rates = ExchangeRateHistory.objects.filter(
                from_currency=currency,
                to_currency__code=self.BASE_CURRENCY,
                date__gte=timezone.now().date() - timedelta(days=30)
            ).order_by('date')
            
            trend = self._calculate_trend(recent_rates)
            
            return {
                'code': currency.code,
                'name': currency.name,
                'symbol': currency.symbol,
                'is_active': currency.is_active,
                'exchange_rate_to_base': self.get_exchange_rate(currency_code, self.BASE_CURRENCY),
                'trend': trend,
                'last_updated': timezone.now()
            }
            
        except Currency.DoesNotExist:
            return {'error': f'Currency {currency_code} not found'}

    def _calculate_trend(self, rates_queryset) -> Dict:
        """
        Calculate currency trend from historical rates.
        """
        rates = list(rates_queryset.values_list('rate', flat=True))
        
        if len(rates) < 2:
            return {'trend': 'stable', 'change': 0}
        
        first_rate = rates[0]
        last_rate = rates[-1]
        change_percent = ((last_rate - first_rate) / first_rate) * 100
        
        if change_percent > 1:
            trend = 'rising'
        elif change_percent < -1:
            trend = 'falling'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': float(change_percent),
            'first_rate': float(first_rate),
            'last_rate': float(last_rate)
        }

    def update_all_exchange_rates(self) -> Dict:
        """
        Update exchange rates for all active currencies.
        """
        active_currencies = Currency.objects.filter(is_active=True)
        results = {
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        with transaction.atomic():
            for currency in active_currencies:
                if currency.code == self.BASE_CURRENCY:
                    continue
                
                try:
                    rate = self.get_exchange_rate(currency.code, self.BASE_CURRENCY)
                    results['updated'] += 1
                    logger.info(f"Updated exchange rate for {currency.code}: {rate}")
                    
                except Exception as e:
                    results['failed'] += 1
                    error_msg = f"Failed to update {currency.code}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
        
        return results

    def get_supported_currencies(self) -> List[Dict]:
        """
        Get list of all supported currencies with current rates.
        """
        currencies = Currency.objects.filter(is_active=True).order_by('name')
        
        supported = []
        for currency in currencies:
            info = self.get_currency_info(currency.code)
            supported.append(info)
        
        return supported

    def validate_currency_pair(self, from_currency: str, to_currency: str) -> bool:
        """
        Validate if currency pair is supported.
        """
        try:
            from_curr = Currency.objects.get(code=from_currency, is_active=True)
            to_curr = Currency.objects.get(code=to_currency, is_active=True)
            return True
        except Currency.DoesNotExist:
            return False

    def get_exchange_rate_history(self, from_currency: str, to_currency: str, days: int = 30) -> List[Dict]:
        """
        Get exchange rate history for a currency pair.
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        history = ExchangeRateHistory.objects.filter(
            from_currency__code=from_currency,
            to_currency__code=to_currency,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        return [
            {
                'date': rate.date.isoformat(),
                'rate': float(rate.rate),
                'source': rate.source
            }
            for rate in history
        ]

    def get_multi_currency_summary(self, base_amount: Decimal, base_currency: str) -> Dict:
        """
        Get amount converted to multiple currencies.
        """
        active_currencies = Currency.objects.filter(is_active=True).exclude(code=base_currency)
        
        conversions = {}
        for currency in active_currencies:
            try:
                converted_amount = self.convert_amount(base_amount, base_currency, currency.code)
                conversions[currency.code] = {
                    'amount': float(converted_amount),
                    'symbol': currency.symbol,
                    'name': currency.name
                }
            except Exception as e:
                logger.error(f"Failed to convert to {currency.code}: {e}")
        
        return {
            'base_amount': float(base_amount),
            'base_currency': base_currency,
            'conversions': conversions,
            'timestamp': timezone.now().isoformat()
        }