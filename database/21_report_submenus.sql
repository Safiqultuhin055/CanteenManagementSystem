-- Reports submenu items (run once, or use: py manage.py sync_menu_permissions)
USE [CanteenManagementDB];
GO

DECLARE @pid INT = (SELECT [id] FROM [dbo].[menus] WHERE [menu_code] = N'REPORTS');

IF @pid IS NOT NULL
BEGIN
    UPDATE [dbo].[menus] SET [url] = N'/reports/' WHERE [id] = @pid;

    MERGE [dbo].[menus] AS t
    USING (VALUES
        (N'REPORT_DAILY',     N'Daily sales',       N'/reports/daily/',      N'bi-calendar-day',      1),
        (N'REPORT_USER',       N'User-wise sales',   N'/reports/user-wise/',  N'bi-person-lines-fill', 2),
        (N'REPORT_MONTHLY',    N'Monthly summary',   N'/reports/monthly/',    N'bi-calendar-month',    3),
        (N'REPORT_INVENTORY',  N'Inventory status',  N'/reports/inventory/',  N'bi-box-seam',          4),
        (N'REPORT_SALES',      N'Sales analytics',   N'/reports/sales/',      N'bi-graph-up-arrow',    5)
    ) AS s([menu_code], [menu_name], [url], [icon_class], [display_order])
    ON t.[menu_code] = s.[menu_code]
    WHEN MATCHED THEN
        UPDATE SET
            [menu_name] = s.[menu_name],
            [parent_id] = @pid,
            [url] = s.[url],
            [icon_class] = s.[icon_class],
            [display_order] = s.[display_order],
            [menu_level] = 1,
            [is_visible] = 1,
            [is_active] = 1,
            [is_deleted] = 0
    WHEN NOT MATCHED THEN
        INSERT ([menu_name], [menu_code], [parent_id], [url], [icon_class], [display_order], [menu_level], [is_visible], [is_active])
        VALUES (s.[menu_name], s.[menu_code], @pid, s.[url], s.[icon_class], s.[display_order], 1, 1, 1);
END
GO
