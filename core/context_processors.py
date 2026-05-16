from users.permissions import get_menu_tree_for_user, is_admin_user, user_permission_codes


def navigation(request):
    """App sidebar context — skip on Django admin (avoids template context conflicts)."""
    empty = {
        'nav_menu_tree': [],
        'user_is_admin': False,
        'user_permission_codes': [],
    }
    path = getattr(request, 'path', '') or ''
    if path.startswith('/admin/'):
        return empty
    if not request.user.is_authenticated:
        return empty
    return {
        'nav_menu_tree': get_menu_tree_for_user(request.user),
        'user_is_admin': is_admin_user(request.user),
        'user_permission_codes': list(user_permission_codes(request.user)),
    }
