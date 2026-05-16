-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — EMPLOYEE REQUEST TABLES
-- Run Order: After 06_sales_pos_tables.sql (FK to orders)
-- ============================================================

USE [CanteenManagementDB];
GO

CREATE TABLE [dbo].[employee_requests] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [request_number]        NVARCHAR(50)        NOT NULL,
    [employee_id]           INT                 NOT NULL,
    [request_date]          DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [request_time]          DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [request_type]          NVARCHAR(50)        NOT NULL DEFAULT 'DESK_DELIVERY',
    [delivery_location]     NVARCHAR(300)       NULL,
    [required_by_time]      DATETIME2(7)        NULL,
    [total_amount]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [request_status]        NVARCHAR(30)        NOT NULL DEFAULT 'PENDING',
    [remarks]               NVARCHAR(500)       NULL,
    [approved_by]           INT                 NULL,
    [approved_at]           DATETIME2(7)        NULL,
    [rejected_by]           INT                 NULL,
    [rejected_at]           DATETIME2(7)        NULL,
    [rejection_reason]      NVARCHAR(500)       NULL,
    [fulfilled_order_id]    INT                 NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_employee_requests] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_employee_requests_number] UNIQUE ([request_number]),
    CONSTRAINT [FK_employee_requests_employee] FOREIGN KEY ([employee_id]) REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_employee_requests_approved_by] FOREIGN KEY ([approved_by]) REFERENCES [dbo].[users]([id]),
    CONSTRAINT [FK_employee_requests_rejected_by] FOREIGN KEY ([rejected_by]) REFERENCES [dbo].[users]([id]),
    CONSTRAINT [FK_employee_requests_fulfilled_order] FOREIGN KEY ([fulfilled_order_id]) REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [CK_employee_requests_type] CHECK ([request_type] IN ('DESK_DELIVERY','ADVANCE_PURCHASE','SPECIAL_MEAL')),
    CONSTRAINT [CK_employee_requests_status] CHECK ([request_status] IN ('PENDING','APPROVED','REJECTED','CANCELLED','FULFILLED')),
    CONSTRAINT [CK_employee_requests_total] CHECK ([total_amount] >= 0)
);
GO

CREATE TABLE [dbo].[employee_request_items] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [request_id]            INT                 NOT NULL,
    [menu_item_id]          INT                 NOT NULL,
    [item_name]             NVARCHAR(300)       NOT NULL,
    [quantity]              INT                 NOT NULL DEFAULT 1,
    [unit_price]            DECIMAL(18,2)       NOT NULL,
    [total_price]           DECIMAL(18,2)       NOT NULL,
    [special_instructions]  NVARCHAR(300)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_employee_request_items] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_employee_request_items_request] FOREIGN KEY ([request_id]) REFERENCES [dbo].[employee_requests]([id]) ON DELETE CASCADE,
    CONSTRAINT [FK_employee_request_items_menu_item] FOREIGN KEY ([menu_item_id]) REFERENCES [dbo].[menu_items]([id]),
    CONSTRAINT [CK_employee_request_items_qty] CHECK ([quantity] > 0)
);
GO

CREATE TABLE [dbo].[employee_request_approvals] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [request_id]            INT                 NOT NULL,
    [approval_level]        INT                 NOT NULL DEFAULT 1,
    [approver_id]           INT                 NOT NULL,
    [approval_status]       NVARCHAR(20)        NOT NULL,
    [comments]              NVARCHAR(500)       NULL,
    [acted_at]              DATETIME2(7)        NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_employee_request_approvals] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_employee_request_approvals_request] FOREIGN KEY ([request_id]) REFERENCES [dbo].[employee_requests]([id]) ON DELETE CASCADE,
    CONSTRAINT [FK_employee_request_approvals_approver] FOREIGN KEY ([approver_id]) REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_employee_request_approvals_status] CHECK ([approval_status] IN ('PENDING','APPROVED','REJECTED'))
);
GO

PRINT 'Employee request tables created successfully.';
GO
