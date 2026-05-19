"""User-wise menu permission assignment."""
from collections import defaultdict

from django.db import models, transaction
from django.utils import timezone

from users.models import Menu, MenuPermission, Permission, User, UserMenuGrant, UserPermission

# Map each menu_code to an existing permission from seed data.
MENU_CODE_TO_PERMISSION = {
    'DASHBOARD': 'DASHBOARD_VIEW',
    'POS': 'ORDER_CREATE',
    'ORDERS': 'ORDER_VIEW',
    'ORDER_LIST': 'ORDER_VIEW',
    'KITCHEN': 'KITCHEN_VIEW',
    'DISTRIBUTION': 'DISTRIBUTION_VIEW',
    'TOKEN_DISPLAY': 'DISTRIBUTION_VIEW',
    'EMPLOYEES': 'EMPLOYEE_VIEW',
    'EMP_LIST': 'EMPLOYEE_VIEW',
    'CARDS': 'CARD_MANAGE',
    'BALANCE': 'BALANCE_VIEW',
    'INVENTORY': 'INVENTORY_VIEW',
    'MENU_ITEMS': 'MENU_ITEM_MANAGE',
    'CATEGORIES': 'INVENTORY_VIEW',
    'DAILY_STOCK': 'INVENTORY_VIEW',
    'RAW_MATERIALS': 'INVENTORY_VIEW',
    'PURCHASES': 'INVENTORY_VIEW',
    'WASTE': 'INVENTORY_VIEW',
    'SUPPLIERS': 'SUPPLIER_MANAGE',
    'REPORTS': 'REPORT_VIEW',
    'REPORT_DAILY': 'REPORT_VIEW',
    'REPORT_USER': 'REPORT_VIEW',
    'REPORT_MONTHLY': 'REPORT_VIEW',
    'REPORT_INVENTORY': 'REPORT_VIEW',
    'REPORT_SALES': 'REPORT_VIEW',
    'ADMIN': 'USER_MANAGE',
    'USERS': 'USER_MANAGE',
    'ROLES': 'ROLE_MANAGE',
    'DEPARTMENTS': 'DEPARTMENT_MANAGE',
    'SETTINGS': 'SETTINGS_MANAGE',
    'AUDIT_LOGS': 'AUDIT_VIEW',
    'GUEST_CARDS': 'GUEST_CARD_MANAGE',
    'HELP': 'DASHBOARD_VIEW',
    'HELP_USER_MANUAL': 'DASHBOARD_VIEW',
    'HELP_DIAGRAMS': 'DASHBOARD_VIEW',
    'HELP_TECHNICAL': 'TECH_DOC_VIEW',
    'USER_MENU_ACCESS': 'USER_MENU_ASSIGN',
}


def search_users(query: str, limit: int = 20):
    qs = User.objects.filter(is_deleted=False, is_active=True)
    if query:
        q = query.strip()
        qs = qs.filter(
            models.Q(username__icontains=q)
            | models.Q(full_name__icontains=q)
            | models.Q(email__icontains=q)
        )
    return list(qs.order_by('username')[:limit])


def _permission_id_by_code():
    return {
        row['permission_code']: row['id']
        for row in Permission.objects.filter(is_active=True, is_deleted=False).values(
            'id', 'permission_code',
        )
    }


def ensure_user_menu_access_nav():
    """Ensure sidebar item for this page exists under Administration."""
    admin = Menu.objects.filter(menu_code='ADMIN', is_active=True, is_deleted=False).first()
    if not admin:
        return False
    defaults = {
        'menu_name': 'User menu access',
        'parent_id': admin.id,
        'url': '/users/menu-permissions/',
        'icon_class': 'bi-ui-checks',
        'display_order': 6,
        'menu_level': 1,
        'is_visible': True,
        'is_active': True,
        'is_deleted': False,
    }
    menu, created = Menu.objects.get_or_create(menu_code='USER_MENU_ACCESS', defaults=defaults)
    if not created:
        Menu.objects.filter(pk=menu.pk).update(**defaults)
    return True


def ensure_menu_permission_mappings():
    """Link every active menu to a permission (idempotent)."""
    code_to_id = _permission_id_by_code()
    created = 0
    for menu in Menu.objects.filter(is_active=True, is_deleted=False):
        perm_code = MENU_CODE_TO_PERMISSION.get(menu.menu_code)
        if not perm_code:
            continue
        perm_id = code_to_id.get(perm_code)
        if not perm_id:
            continue
        exists = MenuPermission.objects.filter(
            menu_id=menu.id, permission_id=perm_id,
        ).exists()
        if not exists:
            MenuPermission.objects.create(
                menu_id=menu.id,
                permission_id=perm_id,
                is_active=True,
            )
            created += 1
    return created


def _menu_permission_map():
    mapping = defaultdict(set)
    for menu_id, perm_id in MenuPermission.objects.filter(is_active=True).values_list(
        'menu_id', 'permission_id',
    ):
        mapping[menu_id].add(perm_id)
    return mapping


def get_user_direct_permission_ids(user_id: int) -> set[int]:
    return set(
        UserPermission.objects.filter(
            user_id=user_id,
            is_active=True,
            is_deleted=False,
        ).values_list('permission_id', flat=True)
    )


def get_granted_menu_ids(user_id: int) -> set[int]:
    return set(
        UserMenuGrant.objects.filter(
            user_id=user_id, is_active=True, is_deleted=False,
        ).values_list('menu_id', flat=True)
    )


def get_checked_menu_ids(user_id: int) -> set[int]:
    return get_granted_menu_ids(user_id)


def menu_is_granted_to_user(user_id: int, menu_id: int, menu_perm_map=None) -> bool:
    return menu_id in get_granted_menu_ids(user_id)


def backfill_menu_grants_from_permissions(user_id: int, actor_id: int | None = None):
    """Sync user_menu_grants from existing user_permissions (missing rows only)."""
    menu_perm_map = _menu_permission_map()
    direct = get_user_direct_permission_ids(user_id)
    if not direct:
        return 0
    created = 0
    for menu in Menu.objects.filter(is_active=True, is_deleted=False):
        required = menu_perm_map.get(menu.id, set())
        if not required or not required.issubset(direct):
            continue
        exists = UserMenuGrant.objects.filter(
            user_id=user_id, menu_id=menu.id, is_active=True, is_deleted=False,
        ).exists()
        if not exists:
            _grant_menu(user_id, menu.id, actor_id)
            created += 1
    return created


def build_nested_menu_tree(user_id: int | None):
    """Nested tree matching sidebar menu structure."""
    menus = list(
        Menu.objects.filter(is_active=True, is_deleted=False).order_by(
            'menu_level', 'display_order', 'id',
        )
    )
    menu_perm_map = _menu_permission_map()
    perm_codes = {
        p['id']: p['permission_code']
        for p in Permission.objects.filter(is_active=True, is_deleted=False).values(
            'id', 'permission_code',
        )
    }
    by_parent = defaultdict(list)
    for menu in menus:
        by_parent[menu.parent_id].append(menu)

    def build_node(menu, depth):
        required = menu_perm_map.get(menu.id, set())
        perm_labels = [perm_codes.get(pid, str(pid)) for pid in sorted(required)]
        children = [
            build_node(child, depth + 1)
            for child in by_parent.get(menu.id, [])
        ]
        return {
            'menu': menu,
            'depth': depth,
            'checked': menu_is_granted_to_user(user_id, menu.id, menu_perm_map) if user_id else False,
            'has_mapping': bool(required),
            'permission_codes': perm_labels,
            'children': children,
            'has_children': bool(children),
        }

    return [build_node(m, 0) for m in by_parent.get(None, [])]


def _grant_menu(user_id: int, menu_id: int, actor_id: int | None):
    now = timezone.now()
    row = UserMenuGrant.objects.filter(user_id=user_id, menu_id=menu_id).first()
    if row:
        if not row.is_active or row.is_deleted:
            row.is_active = True
            row.is_deleted = False
            row.updated_by = actor_id
            row.updated_at = now
            row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])
    else:
        UserMenuGrant.objects.create(
            user_id=user_id,
            menu_id=menu_id,
            is_active=True,
            is_deleted=False,
            created_by=actor_id,
        )


def _revoke_menu(user_id: int, menu_id: int, actor_id: int | None):
    now = timezone.now()
    for row in UserMenuGrant.objects.filter(
        user_id=user_id, menu_id=menu_id, is_active=True, is_deleted=False,
    ):
        row.is_active = False
        row.is_deleted = True
        row.updated_by = actor_id
        row.updated_at = now
        row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])


def _permissions_for_granted_menus(user_id: int, exclude_menu_id: int | None = None) -> set[int]:
    menu_perm_map = _menu_permission_map()
    needed = set()
    qs = UserMenuGrant.objects.filter(user_id=user_id, is_active=True, is_deleted=False)
    if exclude_menu_id is not None:
        qs = qs.exclude(menu_id=exclude_menu_id)
    for menu_id in qs.values_list('menu_id', flat=True):
        needed.update(menu_perm_map.get(menu_id, set()))
    return needed


def _grant_permissions(user_id: int, perm_ids: set[int], actor_id: int | None):
    now = timezone.now()
    existing = {up.permission_id: up for up in UserPermission.objects.filter(user_id=user_id)}
    for perm_id in perm_ids:
        row = existing.get(perm_id)
        if row:
            if not row.is_active or row.is_deleted:
                row.is_active = True
                row.is_deleted = False
                row.updated_by = actor_id
                row.updated_at = now
                row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])
        else:
            UserPermission.objects.create(
                user_id=user_id,
                permission_id=perm_id,
                is_active=True,
                is_deleted=False,
                created_by=actor_id,
            )


def _revoke_permissions(user_id: int, perm_ids: set[int], actor_id: int | None):
    if not perm_ids:
        return
    now = timezone.now()
    for row in UserPermission.objects.filter(
        user_id=user_id, permission_id__in=perm_ids, is_active=True, is_deleted=False,
    ):
        row.is_active = False
        row.is_deleted = True
        row.updated_by = actor_id
        row.updated_at = now
        row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])


@transaction.atomic
def toggle_user_menu_access(user_id: int, menu_id: int, grant: bool, actor_id: int | None):
    """Grant/revoke one menu: soft-delete user_menu_grants + sync user_permissions."""
    menu_perm_map = _menu_permission_map()
    menu_perms = menu_perm_map.get(menu_id, set())
    if not menu_perms:
        return {'ok': False, 'error': 'This menu has no permission mapping. Run database/17_menu_permissions_complete.sql'}

    if grant:
        _grant_menu(user_id, menu_id, actor_id)
        _grant_permissions(user_id, menu_perms, actor_id)
        return {'ok': True, 'granted': len(menu_perms), 'checked': True}

    _revoke_menu(user_id, menu_id, actor_id)
    still_needed = _permissions_for_granted_menus(user_id)
    to_remove = menu_perms - still_needed
    _revoke_permissions(user_id, to_remove, actor_id)
    return {'ok': True, 'revoked': len(to_remove), 'checked': False}


@transaction.atomic
def save_user_menu_permissions(user_id: int, selected_menu_ids: list[int], actor_id: int | None):
    selected = {int(mid) for mid in selected_menu_ids}
    menu_perm_map = _menu_permission_map()
    all_menu_ids = set(
        Menu.objects.filter(is_active=True, is_deleted=False).values_list('id', flat=True)
    )

    for menu_id in all_menu_ids:
        if menu_id in selected:
            _grant_menu(user_id, menu_id, actor_id)
        else:
            _revoke_menu(user_id, menu_id, actor_id)

    grant_permission_ids = set()
    for menu_id in selected:
        grant_permission_ids.update(menu_perm_map.get(menu_id, set()))

    now = timezone.now()
    existing = {up.permission_id: up for up in UserPermission.objects.filter(user_id=user_id)}

    for perm_id, row in existing.items():
        if perm_id in grant_permission_ids:
            if not row.is_active or row.is_deleted:
                row.is_active = True
                row.is_deleted = False
                row.updated_by = actor_id
                row.updated_at = now
                row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])
        else:
            if row.is_active and not row.is_deleted:
                row.is_active = False
                row.is_deleted = True
                row.updated_by = actor_id
                row.updated_at = now
                row.save(update_fields=['is_active', 'is_deleted', 'updated_by', 'updated_at'])

    for perm_id in grant_permission_ids:
        if perm_id in existing:
            continue
        UserPermission.objects.create(
            user_id=user_id,
            permission_id=perm_id,
            is_active=True,
            is_deleted=False,
            created_by=actor_id,
        )

    return len(grant_permission_ids)
