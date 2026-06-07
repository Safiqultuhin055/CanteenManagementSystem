-- Store menu item images in SQL Server (VARBINARY MAX) — like Oracle BLOB
USE [CanteenManagementDB];
GO

IF COL_LENGTH('dbo.menu_items', 'image_data') IS NULL
BEGIN
    ALTER TABLE [dbo].[menu_items]
    ADD [image_data] VARBINARY(MAX) NULL;
    PRINT 'Added menu_items.image_data';
END
GO

IF COL_LENGTH('dbo.menu_items', 'image_content_type') IS NULL
BEGIN
    ALTER TABLE [dbo].[menu_items]
    ADD [image_content_type] NVARCHAR(100) NULL;
    PRINT 'Added menu_items.image_content_type';
END
GO

PRINT 'Menu item image BLOB columns ready.';
GO
