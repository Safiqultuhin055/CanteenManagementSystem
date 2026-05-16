-- Settings menu: hub page + admin module links as children
USE [CanteenManagementDB];
GO

UPDATE [dbo].[menus]
SET [url] = N'/settings/', [menu_name] = N'Settings', [icon_class] = N'bi-sliders'
WHERE [menu_code] = N'SETTINGS';
GO

-- Move Users & Roles under Settings (optional: keep Administration for departments only)
UPDATE [dbo].[menus] SET [parent_id] = (SELECT id FROM menus WHERE menu_code = N'SETTINGS'), [display_order] = 1
WHERE [menu_code] = N'USERS';
UPDATE [dbo].[menus] SET [parent_id] = (SELECT id FROM menus WHERE menu_code = N'SETTINGS'), [display_order] = 2
WHERE [menu_code] = N'ROLES';
UPDATE [dbo].[menus] SET [parent_id] = (SELECT id FROM menus WHERE menu_code = N'SETTINGS'), [display_order] = 3
WHERE [menu_code] = N'AUDIT_LOGS';
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[menus] WHERE [menu_code] = N'SET_PERMISSIONS')
    INSERT INTO [dbo].[menus] ([menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level])
    SELECT N'Permissions', N'SET_PERMISSIONS', id, N'/admin/users/permission/', N'bi-key', 4, 1
    FROM [dbo].[menus] WHERE [menu_code] = N'SETTINGS';

IF NOT EXISTS (SELECT 1 FROM [dbo].[menus] WHERE [menu_code] = N'SET_MENUS')
    INSERT INTO [dbo].[menus] ([menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level])
    SELECT N'Menus', N'SET_MENUS', id, N'/admin/users/menu/', N'bi-list-nested', 5, 1
    FROM [dbo].[menus] WHERE [menu_code] = N'SETTINGS';

IF NOT EXISTS (SELECT 1 FROM [dbo].[menus] WHERE [menu_code] = N'SET_SYSTEM')
    INSERT INTO [dbo].[menus] ([menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level])
    SELECT N'System settings', N'SET_SYSTEM', id, N'/admin/core/systemsetting/', N'bi-gear', 6, 1
    FROM [dbo].[menus] WHERE [menu_code] = N'SETTINGS';
GO

PRINT 'Settings menu children updated.';
GO
