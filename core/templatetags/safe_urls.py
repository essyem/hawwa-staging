from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=False)
def safe_url(view_name, *args, **kwargs):
    """Attempt to reverse a URL and return empty string on failure.

    Usage in template:
        {% load safe_urls %}
        {% safe_url 'docpool:document_list' as docpool_url %}
        {% if docpool_url %}<a href="{{ docpool_url }}">DocPool</a>{% endif %}

    This avoids NoReverseMatch at template render time when app/namespace isn't present.
    """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ''
