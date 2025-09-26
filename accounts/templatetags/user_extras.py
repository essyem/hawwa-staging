from django import template

register = template.Library()


@register.filter
def user_initial(user):
    """Return a single uppercase initial for a user.

    Priority: first_name -> email. Returns empty string for anonymous users.
    """
    try:
        if not getattr(user, "is_authenticated", False):
            return ""
        # first_name may be callable or attribute
        first = getattr(user, "first_name", "") or ""
        if first:
            return str(first)[0].upper()
        email = getattr(user, "email", "") or ""
        return str(email)[0].upper() if email else ""
    except Exception:
        return ""


@register.filter
def user_display_name(user):
    """Return a sensible display name for a user.

    Uses get_full_name() if available, otherwise email. Returns empty for anonymous.
    """
    try:
        if not getattr(user, "is_authenticated", False):
            return ""
        full = getattr(user, "get_full_name", None)
        if callable(full):
            full = full()
        if full:
            return full
        return getattr(user, "email", "") or ""
    except Exception:
        return ""
