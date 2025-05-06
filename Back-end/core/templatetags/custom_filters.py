from django import template

register = template.Library()

@register.filter
def split(value, delimiter="|"):
    """Divide una cadena en una lista usando un delimitador."""
    return value.split(delimiter)