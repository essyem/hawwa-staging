from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings

def format_currency_admin(value):
    """Format currency values for admin display"""
    if value is None or value == '':
        return format_html('<span style="color: #999;">QAR 0.00</span>')
    
    try:
        amount = float(value)
        formatted = f"{amount:,.2f}"
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">QAR {}</span>', 
            formatted
        )
    except (ValueError, TypeError):
        return format_html('<span style="color: #999;">QAR 0.00</span>')

def format_currency_short_admin(value):
    """Format currency values for admin display without decimals"""
    if value is None or value == '':
        return format_html('<span style="color: #999;">QAR 0</span>')
    
    try:
        amount = float(value)
        formatted = f"{amount:,.0f}"
        return format_html(
            '<span style="color: #0066cc; font-weight: bold;">QAR {}</span>', 
            formatted
        )
    except (ValueError, TypeError):
        return format_html('<span style="color: #999;">QAR 0</span>')

# Monkey patch to add currency formatting to common admin displays
def add_currency_methods_to_admin():
    """Add currency formatting methods to admin classes"""
    
    def get_basic_salary_display(self, obj):
        return format_currency_admin(obj.basic_salary)
    get_basic_salary_display.short_description = 'Basic Salary'
    get_basic_salary_display.admin_order_field = 'basic_salary'
    
    def get_total_salary_display(self, obj):
        if hasattr(obj, 'total_salary'):
            return format_currency_admin(obj.total_salary())
        return format_currency_admin(0)
    get_total_salary_display.short_description = 'Total Salary'
    
    def get_gross_salary_display(self, obj):
        return format_currency_admin(obj.gross_salary)
    get_gross_salary_display.short_description = 'Gross Salary'
    get_gross_salary_display.admin_order_field = 'gross_salary'
    
    def get_net_salary_display(self, obj):
        return format_currency_admin(obj.net_salary)
    get_net_salary_display.short_description = 'Net Salary'
    get_net_salary_display.admin_order_field = 'net_salary'
    
    def get_housing_allowance_display(self, obj):
        return format_currency_admin(obj.housing_allowance)
    get_housing_allowance_display.short_description = 'Housing Allowance'
    get_housing_allowance_display.admin_order_field = 'housing_allowance'
    
    def get_transport_allowance_display(self, obj):
        return format_currency_admin(obj.transport_allowance)
    get_transport_allowance_display.short_description = 'Transport Allowance'
    get_transport_allowance_display.admin_order_field = 'transport_allowance'
    
    # Return the methods to be added to admin classes
    return {
        'get_basic_salary_display': get_basic_salary_display,
        'get_total_salary_display': get_total_salary_display,
        'get_gross_salary_display': get_gross_salary_display,
        'get_net_salary_display': get_net_salary_display,
        'get_housing_allowance_display': get_housing_allowance_display,
        'get_transport_allowance_display': get_transport_allowance_display,
    }

# Get the currency methods
currency_methods = add_currency_methods_to_admin()
