from django import template
from django.utils.formats import number_format
from decimal import Decimal

register = template.Library()

@register.filter
def currency_format(value):
    """
    Format a number as Qatar Riyal currency
    Example: 5000 -> "QAR 5,000.00"
    """
    if value is None or value == '':
        return "QAR 0.00"
    
    try:
        # Convert to Decimal for precision
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format with commas and 2 decimal places
        formatted = number_format(value, decimal_pos=2, use_l10n=True)
        return f"QAR {formatted}"
    
    except (ValueError, TypeError):
        return "QAR 0.00"

@register.filter
def qar_format(value):
    """
    Alternative filter name for currency formatting
    """
    return currency_format(value)
