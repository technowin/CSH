from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    try:
        if isinstance(dictionary, dict):
            return dictionary.get(key, '-')
        return '-'
    except Exception:
        return '-'

@register.filter
def to_int(value):
    """Convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def in_list(value, list_str):
    """Check if value is in comma-separated list"""
    if not list_str:
        return False
    try:
        list_values = [int(x.strip()) for x in list_str.split(',') if x.strip()]
        return int(value) in list_values
    except:
        return False