-- ============================================================
-- Menu permissions, Help menus, Technical doc permission
-- Run AFTER 09_seed_data.sql
-- ============================================================

USE [CanteenManagementDB];
GO

-- New permission: technical documentation (admin only)
IF NOT EXISTS (SELECT 1 FROM [dbo].[permissions] WHERE [permission_code] = N'TECH_DOC_VIEW')
BEGIN
    INSERT INTO [dbo].[permissions] ([permission_name],[permission_code],[module])
    VALUES (N'View Technical Documentation', N'TECH_DOC_VIEW', N'Help');
END
GO

-- Grant TECH_DOC_VIEW to Super Admin and Admin roles only
DECLARE @TechPermId INT = (SELECT [id] FROM [dbo].[permissions] WHERE [permission_code] = N'TECH_DOC_VIEW');
IF @TechPermId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [dbo].[role_permissions] WHERE [role_id]=1 AND [permission_id]=@TechPermId)
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active]) VALUES (1, @TechPermId, 1);
    IF NOT EXISTS (SELECT 1 FROM [dbo].[role_permissions] WHERE [role_id]=2 AND [permission_id]=@TechPermId)
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active]) VALUES (2, @TechPermId, 1);
END
GO

-- Help menus
IF NOT EXISTS (SELECT 1 FROM [dbo].[menus] WHERE [menu_code] = N'HELP')
BEGIN
    SET IDENTITY_INSERT [dbo].[menus] ON;
    INSERT INTO [dbo].[menus] ([id],[menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level])
    VALUES
    (28, N'Help', N'HELP', NULL, NULL, N'bi-question-circle', 9, 0),
    (29, N'User Manual', N'HELP_USER_MANUAL', 28, N'/help/user-manual/', N'bi-book', 1, 1),
    (30, N'Technical Documentation', N'HELP_TECHNICAL', 28, N'/help/technical/', N'bi-file-earmark-code', 2, 1),
    (31, N'System Diagrams', N'HELP_DIAGRAMS', 28, N'/help/diagrams/', N'bi-diagram-3', 3, 1);
    SET IDENTITY_INSERT [dbo].[menus] OFF;
END
GO

-- Map menus to permissions (menu visible if user has linked permission)
DECLARE @pid INT;

-- Dashboard
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DASHBOARD_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=1 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (1, @pid);

-- POS
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'ORDER_CREATE';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=2 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (2, @pid);

-- Orders parent + children
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'ORDER_VIEW';
IF @pid IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=3 AND [permission_id]=@pid)
        INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (3, @pid);
    IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=4 AND [permission_id]=@pid)
        INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (4, @pid);
END

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'KITCHEN_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=5 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (5, @pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DISTRIBUTION_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=6 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (6, @pid);

IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=7)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT 7, [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DISTRIBUTION_VIEW';

-- Fix token display URL in menus
UPDATE [dbo].[menus] SET [url] = N'/distribution/display/' WHERE [menu_code] = N'TOKEN_DISPLAY';

-- Employees
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'EMPLOYEE_VIEW';
IF @pid IS NOT NULL
BEGIN
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[menu_code] IN (N'EMPLOYEES', N'EMP_LIST')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);
END

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'CARD_MANAGE';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=10 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (10, @pid);

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'BALANCE_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=11 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (11, @pid);

-- Inventory
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'INVENTORY_VIEW';
IF @pid IS NOT NULL
BEGIN
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[parent_id] = 12 OR m.[id] = 12
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);
END

-- Reports
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'REPORT_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=20 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (20, @pid);

-- Administration
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MANAGE';
IF @pid IS NOT NULL
BEGIN
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id])
    SELECT m.[id], @pid FROM [dbo].[menus] m
    WHERE m.[parent_id] = 21 OR m.[menu_code] IN (N'USERS', N'ROLES', N'DEPARTMENTS', N'SETTINGS', N'AUDIT_LOGS')
    AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] mp WHERE mp.[menu_id]=m.[id] AND mp.[permission_id]=@pid);
END

SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'AUDIT_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=26 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (26, @pid);

-- Guest cards
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'GUEST_CARD_MANAGE';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=27 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (27, @pid);

-- Help: user manual = all authenticated (dashboard view)
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'DASHBOARD_VIEW';
IF @pid IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=28 AND [permission_id]=@pid)
        INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (28, @pid);
    IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=29 AND [permission_id]=@pid)
        INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (29, @pid);
    IF NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=31 AND [permission_id]=@pid)
        INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (31, @pid);
END

-- Technical docs = admin only
SELECT @pid = [id] FROM [dbo].[permissions] WHERE [permission_code] = N'TECH_DOC_VIEW';
IF @pid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [dbo].[menu_permissions] WHERE [menu_id]=30 AND [permission_id]=@pid)
    INSERT INTO [dbo].[menu_permissions] ([menu_id],[permission_id]) VALUES (30, @pid);

-- Map Django admin URLs for inventory/employee modules
UPDATE [dbo].[menus] SET [url] = N'/admin/employee/employee/' WHERE [menu_code] = N'EMP_LIST';
UPDATE [dbo].[menus] SET [url] = N'/admin/employee/employeecard/' WHERE [menu_code] = N'CARDS';
UPDATE [dbo].[menus] SET [url] = N'/admin/balance/employeebalance/' WHERE [menu_code] = N'BALANCE';
UPDATE [dbo].[menus] SET [url] = N'/admin/inventory/menuitem/' WHERE [menu_code] = N'MENU_ITEMS';
UPDATE [dbo].[menus] SET [url] = N'/admin/inventory/foodcategory/' WHERE [menu_code] = N'CATEGORIES';
UPDATE [dbo].[menus] SET [url] = N'/admin/inventory/dailyfoodstock/' WHERE [menu_code] = N'DAILY_STOCK';
UPDATE [dbo].[menus] SET [url] = N'/admin/inventory/rawmaterial/' WHERE [menu_code] = N'RAW_MATERIALS';
UPDATE [dbo].[menus] SET [url] = N'/admin/inventory/supplier/' WHERE [menu_code] = N'SUPPLIERS';
UPDATE [dbo].[menus] SET [url] = N'/admin/users/user/' WHERE [menu_code] = N'USERS';
UPDATE [dbo].[menus] SET [url] = N'/admin/users/role/' WHERE [menu_code] = N'ROLES';
UPDATE [dbo].[menus] SET [url] = N'/admin/employee/department/' WHERE [menu_code] = N'DEPARTMENTS';
UPDATE [dbo].[menus] SET [url] = N'/admin/' WHERE [menu_code] = N'SETTINGS';

PRINT 'Menu permissions and Help menus configured.';
GO
