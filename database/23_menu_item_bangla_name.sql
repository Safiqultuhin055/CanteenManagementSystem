-- Ensure menu_items.item_name_bn exists (safe to re-run)
USE [CanteenManagementDB];
GO

IF COL_LENGTH('dbo.menu_items', 'item_name_bn') IS NULL
BEGIN
    ALTER TABLE [dbo].[menu_items]
    ADD [item_name_bn] NVARCHAR(200) NULL;
    PRINT 'Added menu_items.item_name_bn';
END
ELSE
    PRINT 'menu_items.item_name_bn already exists';
GO
