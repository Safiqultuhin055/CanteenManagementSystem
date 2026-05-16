"""Consistent labels for admin select boxes and list displays."""


def name_with_code(name, code, separator=' - '):
    name = (name or '').strip()
    code = (code or '').strip()
    if name and code:
        return f'{name}{separator}{code}'
    return name or code or ''
