-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — DATABASE CREATION SCRIPT
-- Database Engine : Microsoft SQL Server 2019+
-- Django Driver   : mssql-django
-- Author          : System Architect
-- Created         : 2026-05-15
-- Description     : Creates the CanteenManagementDB database
--                   with proper configuration for Django ORM
-- ============================================================

USE [master];
GO

-- ============================================================
-- 1. DROP DATABASE IF EXISTS (development only)
-- ============================================================
IF EXISTS (SELECT 1 FROM sys.databases WHERE name = N'CanteenManagementDB')
BEGIN
    ALTER DATABASE [CanteenManagementDB] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [CanteenManagementDB];
END
GO

-- ============================================================
-- 2. CREATE DATABASE
-- ============================================================
CREATE DATABASE [CanteenManagementDB]
ON PRIMARY
(
    NAME       = N'CanteenManagementDB_Data',
    FILENAME   = N'C:\SQLData\CanteenManagementDB_Data.mdf',
    SIZE       = 100MB,
    MAXSIZE    = UNLIMITED,
    FILEGROWTH = 50MB
)
LOG ON
(
    NAME       = N'CanteenManagementDB_Log',
    FILENAME   = N'C:\SQLData\CanteenManagementDB_Log.ldf',
    SIZE       = 50MB,
    MAXSIZE    = UNLIMITED,
    FILEGROWTH = 25MB
);
GO

-- ============================================================
-- 3. DATABASE CONFIGURATION
-- ============================================================
ALTER DATABASE [CanteenManagementDB] SET COMPATIBILITY_LEVEL = 150;  -- SQL Server 2019
GO

ALTER DATABASE [CanteenManagementDB] SET RECOVERY FULL;
GO

ALTER DATABASE [CanteenManagementDB] SET READ_COMMITTED_SNAPSHOT ON;
GO

ALTER DATABASE [CanteenManagementDB] SET ALLOW_SNAPSHOT_ISOLATION ON;
GO

-- Enable query store for performance monitoring
ALTER DATABASE [CanteenManagementDB] SET QUERY_STORE = ON
(
    OPERATION_MODE          = READ_WRITE,
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    INTERVAL_LENGTH_MINUTES = 60,
    MAX_STORAGE_SIZE_MB     = 256,
    QUERY_CAPTURE_MODE      = AUTO,
    SIZE_BASED_CLEANUP_MODE = AUTO
);
GO

-- ============================================================
-- 4. SWITCH TO THE NEW DATABASE
-- ============================================================
USE [CanteenManagementDB];
GO

-- ============================================================
-- 5. NOTES FOR DJANGO ORM COMPATIBILITY
-- ============================================================
-- All tables use dbo schema (Django default)
-- All tables use 'id' INT IDENTITY(1,1) as PK
-- Table names: lowercase with underscores (Django convention)
-- Boolean: BIT (maps to BooleanField)
-- DateTime: DATETIME2 (maps to DateTimeField)
-- Money: DECIMAL(18,2) (maps to DecimalField)
-- Strings: NVARCHAR (maps to CharField with Unicode)
-- ============================================================

PRINT '====================================================';
PRINT 'Database [CanteenManagementDB] created successfully.';
PRINT '====================================================';
GO
