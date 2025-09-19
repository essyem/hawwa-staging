"""
Template filters for analytics app
"""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """
    Template filter to look up a value in a dictionary
    Usage: {{ dict|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None


@register.filter
def get_item(dictionary, key):
    """
    Alias for lookup filter
    """
    return lookup(dictionary, key)


@register.filter
def percentage(value, total):
    """
    Calculate percentage
    Usage: {{ value|percentage:total }}
    """
    if total and total > 0:
        try:
            return round((float(value) / float(total)) * 100, 1)
        except (ValueError, TypeError, ZeroDivisionError):
            return 0
    return 0


@register.filter
def quality_grade(score):
    """
    Convert quality score to letter grade
    Usage: {{ score|quality_grade }}
    """
    try:
        score = float(score)
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 65:
            return 'D+'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    except (ValueError, TypeError):
        return 'N/A'


@register.filter
def score_color_class(score):
    """
    Get CSS class for score color coding
    Usage: <span class="{{ score|score_color_class }}">{{ score }}</span>
    """
    try:
        score = float(score)
        if score >= 90:
            return 'text-success'
        elif score >= 80:
            return 'text-info'
        elif score >= 70:
            return 'text-warning'
        else:
            return 'text-danger'
    except (ValueError, TypeError):
        return 'text-muted'


@register.filter
def trend_icon(trend):
    """
    Get Font Awesome icon for trend
    Usage: <i class="fas {{ trend|trend_icon }}"></i>
    """
    trend_icons = {
        'improving': 'fa-arrow-up',
        'stable': 'fa-minus',
        'declining': 'fa-arrow-down',
        'up': 'fa-arrow-up',
        'down': 'fa-arrow-down',
        'neutral': 'fa-minus',
    }
    return trend_icons.get(str(trend).lower(), 'fa-minus')


@register.filter
def format_duration(hours):
    """
    Format hours as human-readable duration
    Usage: {{ hours|format_duration }}
    """
    try:
        hours = float(hours)
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes} min"
        elif hours < 24:
            return f"{hours:.1f} hrs"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            if remaining_hours > 0:
                return f"{days}d {remaining_hours}h"
            else:
                return f"{days} days"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def multiply(value, arg):
    """
    Multiply filter
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """
    Divide filter
    Usage: {{ value|divide:arg }}
    """
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.simple_tag
def performance_badge(score, threshold_excellent=90, threshold_good=80, threshold_average=70):
    """
    Generate performance badge HTML
    Usage: {% performance_badge score %}
    """
    try:
        score = float(score)
        if score >= threshold_excellent:
            return f'<span class="badge bg-success">{score:.1f}</span>'
        elif score >= threshold_good:
            return f'<span class="badge bg-info">{score:.1f}</span>'
        elif score >= threshold_average:
            return f'<span class="badge bg-warning">{score:.1f}</span>'
        else:
            return f'<span class="badge bg-danger">{score:.1f}</span>'
    except (ValueError, TypeError):
        return '<span class="badge bg-secondary">N/A</span>'