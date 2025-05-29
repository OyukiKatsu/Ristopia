from django import template

register = template.Library()

@register.filter
def split(value, delimiter="|"):
    """Divide a string by a delimiter"""
    return value.split(delimiter)

@register.filter
def times(value):
    """
    Usage: {% for _ in some_number|times %}
    will iterate 0…some_number‑1
    """
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []