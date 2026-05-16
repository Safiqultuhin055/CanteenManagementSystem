-- Fix menu URLs for existing databases (run once)
USE [CanteenManagementDB];
GO

UPDATE [dbo].[menus] SET [url] = N'/users/' WHERE [menu_code] = N'USERS';
UPDATE [dbo].[menus] SET [url] = N'/roles/' WHERE [menu_code] = N'ROLES';
UPDATE [dbo].[menus] SET [url] = N'/departments/' WHERE [menu_code] = N'DEPARTMENTS';
UPDATE [dbo].[menus] SET [url] = N'/settings/' WHERE [menu_code] = N'SETTINGS';
UPDATE [dbo].[menus] SET [url] = N'/audit-logs/' WHERE [menu_code] = N'AUDIT_LOGS';
UPDATE [dbo].[menus] SET [url] = N'/orders/' WHERE [menu_code] = N'ORDER_LIST';
UPDATE [dbo].[menus] SET [url] = N'/distribution/display/' WHERE [menu_code] = N'TOKEN_DISPLAY';
UPDATE [dbo].[menus] SET [url] = N'/employees/' WHERE [menu_code] = N'EMP_LIST';
UPDATE [dbo].[menus] SET [url] = N'/cards/' WHERE [menu_code] = N'CARDS';
UPDATE [dbo].[menus] SET [url] = N'/balance/' WHERE [menu_code] = N'BALANCE';
UPDATE [dbo].[menus] SET [url] = N'/menu-items/' WHERE [menu_code] = N'MENU_ITEMS';
UPDATE [dbo].[menus] SET [url] = N'/categories/' WHERE [menu_code] = N'CATEGORIES';
UPDATE [dbo].[menus] SET [url] = N'/daily-stock/' WHERE [menu_code] = N'DAILY_STOCK';
UPDATE [dbo].[menus] SET [url] = N'/raw-materials/' WHERE [menu_code] = N'RAW_MATERIALS';
UPDATE [dbo].[menus] SET [url] = N'/suppliers/' WHERE [menu_code] = N'SUPPLIERS';
UPDATE [dbo].[menus] SET [url] = N'/waste/' WHERE [menu_code] = N'WASTE';
UPDATE [dbo].[menus] SET [url] = N'/purchases/' WHERE [menu_code] = N'PURCHASES';
UPDATE [dbo].[menus] SET [url] = N'/guest-cards/' WHERE [menu_code] = N'GUEST_CARDS';
GO

PRINT 'Menu URLs updated for Django redirects.';
GO
