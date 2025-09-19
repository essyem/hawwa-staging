from decimal import Decimal
from django.utils import timezone
from ..models import CurrencyRate


def get_rate(from_currency, to_currency, date=None):
    """Return the best matching rate to convert from_currency -> to_currency for the given date.

    If no rate exists, return Decimal('1.0') as a safe default.
    """
    if from_currency == to_currency:
        return Decimal('1.0')
    if date is None:
        date = timezone.now().date()

    # Prefer exact matches where valid_from <= date <= valid_to (or valid_to is null)
    rate_obj = CurrencyRate.objects.filter(
        from_currency=from_currency,
        to_currency=to_currency,
        valid_from__lte=date
    ).filter(models.Q(valid_to__gte=date) | models.Q(valid_to__isnull=True)).order_by('-valid_from').first()

    if rate_obj:
        return Decimal(rate_obj.rate)

    # Fallback: try reverse rate and invert
    reverse = CurrencyRate.objects.filter(from_currency=to_currency, to_currency=from_currency).order_by('-valid_from').first()
    if reverse and reverse.rate:
        try:
            return Decimal('1.0') / Decimal(reverse.rate)
        except Exception:
            return Decimal('1.0')

    return Decimal('1.0')


def convert_amount(amount, from_currency, to_currency, date=None):
    """Convert Decimal amount from `from_currency` to `to_currency` using historical rates.

    Default behavior: if there is no rate, return the original amount (1:1).
    """
    amount = Decimal(amount or '0')
    rate = get_rate(from_currency, to_currency, date)
    try:
        return (amount * rate)
    except Exception:
        return amount
