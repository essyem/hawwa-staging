from django.conf import settings


def hawwa_settings(request):
    """Expose HAWWA_SETTINGS to all templates as `HAWWA_SETTINGS`.

    Uses `django.conf.settings` to avoid importing the settings module directly
    (prevents circular imports during setup).
    """
    # Copy the sidebar setting and compute an item-level `visible` flag so
    # templates do not need to call methods like `has_perm` (which is awkward
    # inside template expressions). This also keeps templates simple and fast.
    raw_sidebar = getattr(settings, 'HAWWA_SIDEBAR_APPS', [])
    sidebar = []
    for section in raw_sidebar:
        new_section = {'title': section.get('title'), 'items': []}
        for item in section.get('items', []):
            # copy item to avoid mutating settings
            item_copy = item.copy()
            perm = item_copy.get('perm')
            # If perm is provided, visible only when user has it; otherwise visible
            try:
                item_copy['visible'] = True if not perm else request.user.has_perm(perm)
            except Exception:
                # In some contexts (anonymous user or during startup) request.user
                # may not be fully usable; default to False for restricted items.
                item_copy['visible'] = False if perm else True
            new_section['items'].append(item_copy)
        sidebar.append(new_section)

    return {
        'HAWWA_SETTINGS': getattr(settings, 'HAWWA_SETTINGS', {}),
        # Expose the processed sidebar with item visibility flags
        'HAWWA_SIDEBAR_APPS': sidebar,
    }
