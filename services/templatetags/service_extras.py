from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Return mapping[key] or None if missing. Works for dicts and objects with attribute access.

    Usage in template: `mydict|get_item:key` or `myobj|get_item:'attr'`.
    """
    try:
        # dict-like access
        return mapping.get(key) if hasattr(mapping, 'get') else getattr(mapping, key)
    except Exception:
        try:
            return mapping[key]
        except Exception:
            return None
