-- Ensure daily_food_stock.expired_date exists (safe to re-run)
USE [CanteenManagementDB];
GO

IF COL_LENGTH('dbo.daily_food_stock', 'expired_date') IS NULL
BEGIN
    ALTER TABLE [dbo].[daily_food_stock]
    ADD [expired_date] DATE NULL;
    PRINT 'Added daily_food_stock.expired_date';
END
ELSE
    PRINT 'daily_food_stock.expired_date already exists';
GO
