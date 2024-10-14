from django import template

register = template.Library()

@register.filter
def is_long_text(value, length=50):
    return len(value) > length