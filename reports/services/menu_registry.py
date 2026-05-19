"""Ensure Reports submenu items exist in navigation."""
from users.models import Menu

REPORT_MENUS = (
    ('REPORT_DAILY', 'Daily sales', '/reports/daily/', 'bi-calendar-day', 1),
    ('REPORT_USER', 'User-wise sales', '/reports/user-wise/', 'bi-person-lines-fill', 2),
    ('REPORT_MONTHLY', 'Monthly summary', '/reports/monthly/', 'bi-calendar-month', 3),
    ('REPORT_INVENTORY', 'Inventory status', '/reports/inventory/', 'bi-box-seam', 4),
    ('REPORT_SALES', 'Sales analytics', '/reports/sales/', 'bi-graph-up-arrow', 5),
)


def ensure_report_menus() -> int:
    parent = Menu.objects.filter(menu_code='REPORTS', is_deleted=False).first()
    if not parent:
        return 0
    created = 0
    for code, name, url, icon, order in REPORT_MENUS:
        defaults = {
            'menu_name': name,
            'parent_id': parent.id,
            'url': url,
            'icon_class': icon,
            'display_order': order,
            'menu_level': 1,
            'is_visible': True,
            'is_active': True,
            'is_deleted': False,
        }
        menu, was_created = Menu.objects.get_or_create(menu_code=code, defaults=defaults)
        if not was_created:
            Menu.objects.filter(pk=menu.pk).update(**defaults)
        else:
            created += 1
    Menu.objects.filter(pk=parent.pk).update(url='/reports/')
    return created
