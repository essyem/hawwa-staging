from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css):
    """Return field as HTML with added class attribute (very small compatibility helper)."""
    try:
        existing = field.field.widget.attrs.get('class', '')
        classes = (existing + ' ' + css).strip()
        field.field.widget.attrs['class'] = classes
        return field
    except Exception:
        return field


@register.filter(name='first')
def first(value):
    try:
        return value[0]
    except Exception:
        return ''
