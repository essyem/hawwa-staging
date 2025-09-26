from django import template

register = template.Library()


@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status"""
    return queryset.filter(status=status) if hasattr(queryset, 'filter') else queryset


@register.filter
def percentage(part, whole):
    """Calculate percentage"""
    try:
        return (part / whole) * 100 if whole > 0 else 0
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def currency(value):
    """Format currency value"""
    try:
        return f"QAR {float(value):,.2f}"
    except (ValueError, TypeError):
        return "QAR 0.00"


@register.filter
def status_color(status):
    """Get color class for status"""
    colors = {
        'paid': 'success',
        'pending': 'warning', 
        'overdue': 'danger',
        'draft': 'secondary',
        'cancelled': 'dark'
    }
    return colors.get(status, 'secondary')


@register.filter
def days_between(date1, date2):
    """Calculate days between two dates"""
    try:
        return (date2 - date1).days
    except (AttributeError, TypeError):
        return 0


@register.simple_tag
def invoice_count_by_status(invoices, status):
    """Count invoices by status"""
    if hasattr(invoices, 'filter'):
        return invoices.filter(status=status).count()
    return len([inv for inv in invoices if inv.status == status])


@register.simple_tag
def payment_count_by_status(payments, status):
    """Count payments by status"""
    if hasattr(payments, 'filter'):
        return payments.filter(payment_status=status).count()
    return len([pay for pay in payments if pay.payment_status == status])


@register.inclusion_tag('financial/partials/status_badge.html')
def status_badge(status):
    """Render status badge"""
    return {'status': status}


@register.inclusion_tag('financial/partials/payment_progress.html')
def payment_progress(invoice):
    """Render payment progress bar"""
    if hasattr(invoice, 'total_amount') and invoice.total_amount > 0:
        paid_amount = getattr(invoice, 'paid_amount', 0)
        percentage = (paid_amount / invoice.total_amount) * 100
    else:
        percentage = 0
    
    return {
        'invoice': invoice,
        'percentage': percentage,
        'paid_amount': getattr(invoice, 'paid_amount', 0),
        'remaining_amount': getattr(invoice, 'remaining_amount', invoice.total_amount if hasattr(invoice, 'total_amount') else 0)
    }