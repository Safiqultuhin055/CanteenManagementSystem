"""Create dbo.user_permissions if missing (SQL Server)."""
from django.core.management.base import BaseCommand
from django.db import connection

from users.db_schema import ensure_user_access_schema

SEED_PERMISSION_SQL = """
IF NOT EXISTS (SELECT 1 FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN')
    INSERT INTO [dbo].[permissions] ([permission_name],[permission_code],[module])
    VALUES (N'Assign User Menu Permissions', N'USER_MENU_ASSIGN', N'Security');
"""

SEED_ROLE_SQL = """
DECLARE @AssignPermId INT = (
    SELECT [id] FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN'
);
IF @AssignPermId IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM [dbo].[role_permissions]
        WHERE [role_id] = 1 AND [permission_id] = @AssignPermId
    )
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active])
        VALUES (1, @AssignPermId, 1);
    IF NOT EXISTS (
        SELECT 1 FROM [dbo].[role_permissions]
        WHERE [role_id] = 2 AND [permission_id] = @AssignPermId
    )
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active])
        VALUES (2, @AssignPermId, 1);
END
"""


class Command(BaseCommand):
    help = 'Create user_permissions / user_menu_grants tables and USER_MENU_ASSIGN permission.'

    def handle(self, *args, **options):
        ensure_user_access_schema()
        with connection.cursor() as cursor:
            cursor.execute(SEED_PERMISSION_SQL)
            cursor.execute(SEED_ROLE_SQL)
        self.stdout.write(self.style.SUCCESS('user_permissions and user_menu_grants tables are ready.'))
