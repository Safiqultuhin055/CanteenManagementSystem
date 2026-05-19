-- ============================================================
-- Complete menu_permissions for all existing menus + User menu access nav item
-- Run on CanteenManagementDB (safe to re-run)
-- ============================================================
USE [CanteenManagementDB];
GO

-- Nav item: User menu permissions (under Administration)
IF NOT EXISTS (SELECT 1 FROM [dbo].[menus] WHERE [menu_code] = N'USER_MENU_ACCESS')
BEGIN
    INSERT INTO [dbo].[menus] ([menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level],[is_visible],[is_active])
    VALUES (
        N'User menu access', N'USER_MENU_ACCESS', 21,
        N'/users/menu-permissions/', N'bi-ui-checks', 6, 1, 1, 1
    );
END
ELSE
    UPDATE [dbo].[menus]
    SET [parent_id] = 21, [url] = N'/users/menu-permissions/', [icon_class] = N'bi-ui-checks',
        [display_order] = 6, [menu_level] = 1, [is_visible] = 1, [is_active] = 1
    WHERE [menu_code] = N'USER_MENU_ACCESS';
GO

DECLARE @pid INT;

-- Dashboard
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DASHBOARD_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'DASHBOARD'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- POS
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'ORDER_CREATE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'POS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Orders branch
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'ORDER_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'ORDERS', N'ORDER_LIST')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'KITCHEN_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'KITCHEN'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DISTRIBUTION_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'DISTRIBUTION', N'TOKEN_DISPLAY')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Employees branch
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'EMPLOYEE_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'EMPLOYEES', N'EMP_LIST')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'CARD_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'CARDS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'BALANCE_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'BALANCE'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Inventory branch
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'INVENTORY_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'INVENTORY', N'MENU_ITEMS', N'CATEGORIES', N'DAILY_STOCK', N'RAW_MATERIALS', N'PURCHASES', N'WASTE', N'SUPPLIERS')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'MENU_ITEM_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'MENU_ITEMS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'SUPPLIER_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'SUPPLIERS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Reports
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'REPORT_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'REPORTS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Administration branch
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'ADMIN', N'USERS', N'ROLES', N'DEPARTMENTS')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'SETTINGS_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'SETTINGS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'AUDIT_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'AUDIT_LOGS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

IF NOT EXISTS (SELECT 1 FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN')
    INSERT INTO [dbo].[permissions] ([permission_name],[permission_code],[module])
    VALUES (N'Assign User Menu Permissions', N'USER_MENU_ASSIGN', N'Security');

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'USER_MENU_ACCESS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Guest cards
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'GUEST_CARD_MANAGE';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'GUEST_CARDS'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

-- Help menus
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DASHBOARD_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'HELP', N'HELP_USER_MANUAL', N'HELP_DIAGRAMS')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'TECH_DOC_VIEW';
IF @pid IS NOT NULL
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m WHERE m.[menu_code] = N'HELP_TECHNICAL'
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);

PRINT 'Menu permissions complete for all existing menus.';
GO
