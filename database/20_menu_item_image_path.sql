-- Ensure menu_items.image_path exists (safe to re-run)
USE [CanteenManagementDB];
GO

IF COL_LENGTH('dbo.menu_items', 'image_path') IS NULL
BEGIN
    ALTER TABLE [dbo].[menu_items]
    ADD [image_path] NVARCHAR(500) NULL;
    PRINT 'Added menu_items.image_path';
END
ELSE
    PRINT 'menu_items.image_path already exists';
GO
