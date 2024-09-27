from django import template

register = template.Library()

@register.filter
def in_pairs(value):
    """Divide a list into pairs."""
    return [value[i:i+4] for i in range(0, len(value), 4)]

@register.filter
def replace_spaces(value):
    """Replace spaces with an empty string."""
    return value.replace(" ", "")

@register.filter
def is_long_text(value, length=50):
    return len(value) > length