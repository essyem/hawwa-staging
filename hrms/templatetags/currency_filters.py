from django import template
from django.conf import settings
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def currency(value):
    """
    Format a number as currency using QAR
    Usage: {{ amount|currency }}
    """
    if value is None or value == '':
        return f"QAR 0.00"
    
    try:
        # Handle string values that might have currency symbols or commas
        if isinstance(value, str):
            # Remove any existing currency symbols and commas
            cleaned_value = value.replace('$', '').replace('ر.ق', '').replace('QAR', '').replace(',', '').strip()
            if not cleaned_value or cleaned_value == 'None':
                return f"0.00 {getattr(settings, 'CURRENCY_SYMBOL', 'QAR')}"
            value = cleaned_value
        
        # Convert to Decimal for proper formatting
        amount = Decimal(str(value))
        
        # Format with commas and 2 decimal places
        formatted = f"{amount:,.2f}"
        
        # Get currency settings from Django settings
        currency_symbol = getattr(settings, 'CURRENCY_SYMBOL', 'QAR')
        position = getattr(settings, 'CURRENCY_SYMBOL_POSITION', 'before')
        
        if position == 'before':
            return f"{currency_symbol} {formatted}"
        else:
            return f"{formatted} {currency_symbol}"
            
    except (ValueError, TypeError, InvalidOperation):
        return f"QAR 0.00"

@register.filter  
def currency_short(value):
    """
    Format currency without decimal places for large amounts
    Usage: {{ amount|currency_short }}
    """
    if value is None or value == '':
        return f"QAR 0"
        
    try:
        # Handle string values that might have currency symbols or commas
        if isinstance(value, str):
            # Remove any existing currency symbols and commas
            cleaned_value = value.replace('$', '').replace('ر.ق', '').replace('QAR', '').replace(',', '').strip()
            if not cleaned_value or cleaned_value == 'None':
                return f"QAR 0"
            value = cleaned_value
            
        amount = Decimal(str(value))
        formatted = f"{amount:,.0f}"
        currency_symbol = getattr(settings, 'CURRENCY_SYMBOL', 'QAR')
        position = getattr(settings, 'CURRENCY_SYMBOL_POSITION', 'before')
        
        if position == 'before':
            return f"{currency_symbol} {formatted}"
        else:
            return f"{formatted} {currency_symbol}"
            
    except (ValueError, TypeError, InvalidOperation):
        return f"QAR 0"

@register.simple_tag
def currency_symbol():
    """
    Get the currency symbol
    Usage: {% currency_symbol %}
    """
    return getattr(settings, 'CURRENCY_SYMBOL', 'QAR')

@register.filter
def currency_format(value):
    """
    Alternative filter name for backward compatibility
    """
    return currency(value)

@register.filter
def qar_format(value):
    """
    Specifically format as QAR currency (alias for currency filter)
    """
    return currency(value)

@register.simple_tag
def currency_code():
    """
    Get the currency code
    Usage: {% currency_code %}
    """
    return getattr(settings, 'CURRENCY_CODE', 'QAR')
