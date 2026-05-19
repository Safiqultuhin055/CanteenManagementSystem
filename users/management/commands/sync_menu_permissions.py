from django.core.management.base import BaseCommand

from reports.services.menu_registry import ensure_report_menus
from users.services.menu_permission_service import (
    ensure_menu_permission_mappings,
    ensure_user_menu_access_nav,
)


class Command(BaseCommand):
    help = 'Link all existing menus to permissions and add User menu access nav item.'

    def handle(self, *args, **options):
        nav_ok = ensure_user_menu_access_nav()
        report_menus = ensure_report_menus()
        created = ensure_menu_permission_mappings()
        self.stdout.write(self.style.SUCCESS(
            f'Nav item ready: {nav_ok}. Report submenus: {report_menus} new. '
            f'Menu_permission rows: {created} new.',
        ))
