-- Optional POS receipt address/phone (safe to re-run)
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[system_settings] WHERE [setting_key] = N'RECEIPT_ADDRESS')
BEGIN
    INSERT INTO [dbo].[system_settings] ([setting_key],[setting_value],[setting_type],[category],[description])
    VALUES (N'RECEIPT_ADDRESS', N'Staff Canteen', N'STRING', N'POS', N'Receipt address line');
END
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[system_settings] WHERE [setting_key] = N'RECEIPT_PHONE')
BEGIN
    INSERT INTO [dbo].[system_settings] ([setting_key],[setting_value],[setting_type],[category],[description])
    VALUES (N'RECEIPT_PHONE', N'', N'STRING', N'POS', N'Receipt telephone line');
END
GO
