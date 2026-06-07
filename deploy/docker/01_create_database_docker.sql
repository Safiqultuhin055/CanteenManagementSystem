-- Docker SQL Server: create CanteenManagementDB (default data paths)
USE [master];
GO

IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = N'CanteenManagementDB')
BEGIN
    CREATE DATABASE [CanteenManagementDB];
END
GO

USE [CanteenManagementDB];
GO

PRINT 'CanteenManagementDB ready.';
GO
