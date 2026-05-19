"""Role and menu permission helpers."""

from .models import Menu, MenuPermission, Permission, Role, UserMenuGrant, UserPermission, UserRole


def user_role_codes(user) -> set[str]:
    if not user.is_authenticated:
        return set()
    if getattr(user, 'is_superuser', False):
        return {'SUPER_ADMIN', 'ADMIN'}
    role_ids = UserRole.objects.filter(
        user_id=user.id, is_active=True, is_deleted=False,
    ).values_list('role_id', flat=True)
    return set(
        Role.objects.filter(
            id__in=role_ids, is_active=True, is_deleted=False,
        ).values_list('role_code', flat=True)
    )


def is_admin_user(user) -> bool:
    if not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return bool(user_role_codes(user) & {'SUPER_ADMIN', 'ADMIN'})


def user_permission_codes(user) -> set[str]:
    if not user.is_authenticated:
        return set()
    if getattr(user, 'is_superuser', False):
        return set(Permission.objects.filter(is_active=True, is_deleted=False).values_list('permission_code', flat=True))

    codes = set()
    role_ids = list(
        UserRole.objects.filter(user_id=user.id, is_active=True, is_deleted=False).values_list(
            'role_id', flat=True,
        )
    )
    if role_ids:
        codes.update(
            Permission.objects.filter(
                is_active=True,
                is_deleted=False,
                rolepermission__role_id__in=role_ids,
                rolepermission__is_active=True,
                rolepermission__is_deleted=False,
            ).values_list('permission_code', flat=True).distinct()
        )

    direct_perm_ids = UserPermission.objects.filter(
        user_id=user.id, is_active=True, is_deleted=False,
    ).values_list('permission_id', flat=True)
    if direct_perm_ids:
        codes.update(
            Permission.objects.filter(
                id__in=direct_perm_ids, is_active=True, is_deleted=False,
            ).values_list('permission_code', flat=True)
        )

    return codes


def user_has_direct_menu_grants(user) -> bool:
    """User was assigned menus via User menu access (explicit menu rows)."""
    if not user.is_authenticated:
        return False
    return UserMenuGrant.objects.filter(
        user_id=user.id, is_active=True, is_deleted=False,
    ).exists()


def user_menu_is_granted(user, menu_id: int) -> bool:
    if not user.is_authenticated:
        return False
    return UserMenuGrant.objects.filter(
        user_id=user.id, menu_id=menu_id, is_active=True, is_deleted=False,
    ).exists()


def user_has_permission(user, permission_code: str) -> bool:
    return permission_code in user_permission_codes(user)


def user_can_access_menu(user, menu: Menu) -> bool:
    if not user.is_authenticated or not menu.is_active or not menu.is_visible or menu.is_deleted:
        return False
    if getattr(user, 'is_superuser', False):
        return True

    perm_ids = list(
        MenuPermission.objects.filter(menu_id=menu.id, is_active=True).values_list('permission_id', flat=True)
    )
    if not perm_ids:
        return menu.menu_code in ('DASHBOARD', 'HELP', 'HELP_USER_MANUAL', 'HELP_DIAGRAMS')

    if user_has_direct_menu_grants(user):
        return user_menu_is_granted(user, menu.id)

    user_perms = user_permission_codes(user)
    menu_perm_codes = set(
        Permission.objects.filter(id__in=perm_ids, is_active=True).values_list('permission_code', flat=True)
    )
    return bool(menu_perm_codes & user_perms)


def get_menu_tree_for_user(user):
    """Return nested menu dicts for sidebar rendering."""
    all_menus = list(
        Menu.objects.filter(is_active=True, is_deleted=False, is_visible=True).order_by('menu_level', 'display_order', 'id')
    )
    by_parent = {}
    for m in all_menus:
        by_parent.setdefault(m.parent_id, []).append(m)

    def build(parent_id=None):
        items = []
        for menu in by_parent.get(parent_id, []):
            children = build(menu.id)
            if menu.url:
                allowed = user_can_access_menu(user, menu)
            else:
                allowed = bool(children) or user_can_access_menu(user, menu)
            if not allowed:
                continue
            items.append({
                'id': menu.id,
                'name': menu.menu_name,
                'code': menu.menu_code,
                'url': menu.url or '#',
                'icon': menu.icon_class or 'bi-circle',
                'children': children,
                'has_children': bool(children),
            })
        return items

    return build(None)
