from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    
    Usage:
    {{ mydict|get_item:item.name }}
    """
    if dictionary is None:
        return None
    return dictionary.get(str(key))

@register.filter
def get_range(value):
    """
    Returns a range of integers from 1 to the given value.
    
    Usage:
    {% for i in 5|get_range %}
        {{ i }}
    {% endfor %}
    """
    return range(1, value + 1)

@register.filter
def star_range(value):
    """
    Returns a list of integers from 1 to 5, used for star ratings.
    
    Usage:
    {% for i in review.rating|star_range %}
        {% if i <= review.rating %}
            <i class="fas fa-star"></i>
        {% else %}
            <i class="far fa-star"></i>
        {% endif %}
    {% endfor %}
    """
    return range(1, 6)

@register.filter
def div(value, divisor):
    """
    Divides the value by the divisor.
    
    Usage:
    {{ service.duration.seconds|div:3600 }}
    """
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0