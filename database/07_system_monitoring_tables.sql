-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — SYSTEM & MONITORING TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Notifications, system settings,
--                   audit logs, activity logs
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: notifications
-- Purpose: System alerts and notifications
-- Django:  Notification model
-- Notes:   - Low stock, expiry, system alerts, etc.
-- ============================================================
CREATE TABLE [dbo].[notifications] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [notification_type]     NVARCHAR(50)        NOT NULL,
        -- LOW_STOCK, EXPIRY_ALERT, SYSTEM_ALERT, BALANCE_LOW,
        -- CREDIT_LIMIT, ORDER_ALERT, MAINTENANCE
    [title]                 NVARCHAR(300)       NOT NULL,
    [message]               NVARCHAR(2000)      NOT NULL,
    [severity]              NVARCHAR(20)        NOT NULL DEFAULT 'INFO',
        -- INFO, WARNING, CRITICAL, SUCCESS
    [target_user_id]        INT                 NULL,       -- specific user, NULL = broadcast
    [target_role_id]        INT                 NULL,       -- target role
    [reference_type]        NVARCHAR(50)        NULL,       -- 'ORDER', 'STOCK', 'EMPLOYEE'
    [reference_id]          INT                 NULL,       -- FK to referenced record
    [is_read]               BIT                 NOT NULL DEFAULT 0,
    [read_at]               DATETIME2(7)        NULL,
    [expires_at]            DATETIME2(7)        NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_notifications] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_notifications_target_user] FOREIGN KEY ([target_user_id])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [FK_notifications_target_role] FOREIGN KEY ([target_role_id])
        REFERENCES [dbo].[roles]([id]),
    CONSTRAINT [CK_notifications_type] CHECK ([notification_type] IN (
        'LOW_STOCK', 'EXPIRY_ALERT', 'SYSTEM_ALERT', 'BALANCE_LOW',
        'CREDIT_LIMIT', 'ORDER_ALERT', 'MAINTENANCE'
    )),
    CONSTRAINT [CK_notifications_severity] CHECK ([severity] IN ('INFO', 'WARNING', 'CRITICAL', 'SUCCESS'))
);
GO

-- ============================================================
-- TABLE: system_settings
-- Purpose: Application configuration key-value store
-- Django:  SystemSetting model
-- Notes:   - Stores configurable system parameters
--          - e.g., low_stock_threshold, token_reset_time
-- ============================================================
CREATE TABLE [dbo].[system_settings] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [setting_key]       NVARCHAR(200)       NOT NULL,
    [setting_value]     NVARCHAR(2000)      NOT NULL,
    [setting_type]      NVARCHAR(50)        NOT NULL DEFAULT 'STRING',
        -- STRING, INTEGER, DECIMAL, BOOLEAN, JSON
    [category]          NVARCHAR(100)       NOT NULL DEFAULT 'GENERAL',
        -- GENERAL, POS, KITCHEN, INVENTORY, SECURITY, NOTIFICATION
    [description]       NVARCHAR(500)       NULL,
    [is_editable]       BIT                 NOT NULL DEFAULT 1,
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [is_deleted]        BIT                 NOT NULL DEFAULT 0,
    [created_by]        INT                 NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]        INT                 NULL,
    [updated_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_system_settings] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_system_settings_key] UNIQUE ([setting_key]),
    CONSTRAINT [CK_system_settings_type] CHECK ([setting_type] IN (
        'STRING', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'JSON'
    ))
);
GO

-- ============================================================
-- TABLE: audit_logs
-- Purpose: Complete audit trail for all critical operations
-- Django:  AuditLog model (populated via middleware/signals)
-- Notes:   - Records every CREATE, UPDATE, DELETE, LOGIN, etc.
--          - Stores old/new values for change tracking
-- ============================================================
CREATE TABLE [dbo].[audit_logs] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [user_id]           INT                 NULL,
    [username]          NVARCHAR(150)       NULL,
    [action]            NVARCHAR(50)        NOT NULL,
        -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT, PASSWORD_CHANGE,
        -- ACTIVATION, DEACTIVATION, SALE, BALANCE_ALLOCATION,
        -- STOCK_UPDATE, CARD_ACTIVATION, CARD_DEACTIVATION,
        -- ROLE_ASSIGNMENT, PERMISSION_CHANGE
    [table_name]        NVARCHAR(200)       NULL,
    [record_id]         INT                 NULL,
    [old_values]        NVARCHAR(MAX)       NULL,   -- JSON of old values
    [new_values]        NVARCHAR(MAX)       NULL,   -- JSON of new values
    [ip_address]        NVARCHAR(45)        NULL,
    [user_agent]        NVARCHAR(500)       NULL,
    [module]            NVARCHAR(100)       NULL,   -- 'Users', 'Orders', 'Inventory'
    [description]       NVARCHAR(1000)      NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_audit_logs] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_audit_logs_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id])
);
GO

-- ============================================================
-- TABLE: activity_logs
-- Purpose: General user activity tracking (page views, actions)
-- Django:  ActivityLog model (populated via middleware)
-- ============================================================
CREATE TABLE [dbo].[activity_logs] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [user_id]           INT                 NULL,
    [activity_type]     NVARCHAR(50)        NOT NULL,
        -- PAGE_VIEW, BUTTON_CLICK, API_CALL, SEARCH,
        -- REPORT_EXPORT, PRINT, FILE_UPLOAD
    [module]            NVARCHAR(100)       NULL,
    [page_url]          NVARCHAR(500)       NULL,
    [http_method]       NVARCHAR(10)        NULL,
    [request_data]      NVARCHAR(MAX)       NULL,
    [response_status]   INT                 NULL,   -- HTTP status code
    [duration_ms]       INT                 NULL,   -- request duration in ms
    [ip_address]        NVARCHAR(45)        NULL,
    [user_agent]        NVARCHAR(500)       NULL,
    [session_key]       NVARCHAR(200)       NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_activity_logs] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_activity_logs_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_activity_logs_type] CHECK ([activity_type] IN (
        'PAGE_VIEW', 'BUTTON_CLICK', 'API_CALL', 'SEARCH',
        'REPORT_EXPORT', 'PRINT', 'FILE_UPLOAD'
    ))
);
GO

PRINT '=============================================================';
PRINT 'System & Monitoring tables created successfully (4 tables).';
PRINT '=============================================================';
GO
