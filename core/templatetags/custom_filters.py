from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='div')
def div(value, arg):
    """Divide numeric value by arg. Returns float or original value on error."""
    try:
        v = float(value)
        a = float(arg)
        if a == 0:
            return value
        return v / a
    except Exception:
        return value


@register.filter(name='split')
def split(value, sep=None):
    """Split string by separator and return list. If sep omitted, split on whitespace."""
    if value is None:
        return []
    try:
        if sep is None:
            return str(value).split()
        return str(value).split(sep)
    except Exception:
        return [value]


@register.filter(name='highlight_search')
def highlight_search(value, query):
    """Naive highlight filter: wraps occurrences of query in a span. Case-insensitive."""
    if not value or not query:
        return value
    try:
        text = str(value)
        q = str(query)
        import re
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: '<span class="search-highlight">%s</span>' % m.group(0), text)
        return mark_safe(highlighted)
    except Exception:
        return value
