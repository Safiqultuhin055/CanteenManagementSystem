"""Template helpers — ASCII-safe currency (avoids UTF-8 ৳ display issues on Windows)."""
from django import template

register = template.Library()

CURRENCY_PREFIX = 'Tk '


@register.filter
def taka(value, arg=2):
    """Format amount as Tk 1,234.56 (plain ASCII). arg=0 for no decimals."""
    try:
        decimals = int(arg)
    except (TypeError, ValueError):
        decimals = 2
    try:
        n = float(value)
    except (TypeError, ValueError):
        return f'{CURRENCY_PREFIX}—'
    if decimals == 0:
        return f'{CURRENCY_PREFIX}{n:,.0f}'
    return f'{CURRENCY_PREFIX}{n:,.2f}'
