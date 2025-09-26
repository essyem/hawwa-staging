from django.utils.text import capfirst
from django.conf import settings


def app_title(request):
    """Provide a friendly app title for templates.

    Behavior:
    - If the resolver's app_name matches a section/item in `HAWWA_SIDEBAR_APPS`, prefer the configured label.
    - Do not show a title for the main core home page (so the header doesn't show 'Core').
    - Fall back to a readable version of app_name or url_name.
    """
    resolver = getattr(request, 'resolver_match', None)
    title = ''
    if not resolver:
        return {'app_title': title}

    app = resolver.app_name or ''
    name = resolver.url_name or ''

    # Avoid showing a generic 'Core' title for the site landing page
    if app == 'core' and name in ('home', '', None):
        return {'app_title': ''}

    # Prefer label from HAWWA_SIDEBAR_APPS when available
    sidebar = getattr(settings, 'HAWWA_SIDEBAR_APPS', []) or []
    if app:
        for section in sidebar:
            for item in section.get('items', []):
                # item.url_name may be like 'appname:viewname' — compare app part
                url_name = item.get('url_name') or ''
                if ':' in url_name:
                    item_app, _ = url_name.split(':', 1)
                else:
                    item_app = ''
                if item_app == app and item.get('label'):
                    return {'app_title': capfirst(item.get('label'))}

    # Fallbacks
    if app:
        title = capfirst(app.replace('_', ' '))
    elif name:
        title = capfirst(name.replace('_', ' '))

    return {'app_title': title}
