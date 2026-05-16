-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — EMPLOYEE MANAGEMENT TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Departments, Employees, Employee Cards
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: departments
-- Purpose: Organization departments
-- Django:  Department model
-- ============================================================
CREATE TABLE [dbo].[departments] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [department_name]   NVARCHAR(200)       NOT NULL,
    [department_code]   NVARCHAR(50)        NOT NULL,
    [description]       NVARCHAR(500)       NULL,
    [head_employee_id]  INT                 NULL,       -- FK to employees (set after employees created)
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [is_deleted]        BIT                 NOT NULL DEFAULT 0,
    [created_by]        INT                 NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]        INT                 NULL,
    [updated_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_departments] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_departments_code] UNIQUE ([department_code]),
    CONSTRAINT [UQ_departments_name] UNIQUE ([department_name])
);
GO

-- ============================================================
-- TABLE: employees
-- Purpose: Employee master data
-- Django:  Employee model
-- Notes:   - Linked to users table via users.employee_id
--          - employee_code is the external HR reference
-- ============================================================
CREATE TABLE [dbo].[employees] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [employee_code]         NVARCHAR(50)        NOT NULL,   -- HR system ID / badge number
    [first_name]            NVARCHAR(150)       NOT NULL,
    [last_name]             NVARCHAR(150)       NULL,
    [full_name]             NVARCHAR(300)       NOT NULL,
    [email]                 NVARCHAR(254)       NULL,
    [phone]                 NVARCHAR(20)        NULL,
    [department_id]         INT                 NOT NULL,
    [designation]           NVARCHAR(200)       NULL,
    [date_of_joining]       DATE                NULL,
    [date_of_leaving]       DATE                NULL,
    [employee_type]         NVARCHAR(50)        NOT NULL DEFAULT 'PERMANENT',
        -- PERMANENT, CONTRACT, TEMPORARY, INTERN
    [profile_image]         NVARCHAR(500)       NULL,
    [address]               NVARCHAR(500)       NULL,
    [emergency_contact]     NVARCHAR(20)        NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_employees] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_employees_code] UNIQUE ([employee_code]),
    CONSTRAINT [FK_employees_department] FOREIGN KEY ([department_id])
        REFERENCES [dbo].[departments]([id]),
    CONSTRAINT [CK_employees_type] CHECK ([employee_type] IN (
        'PERMANENT', 'CONTRACT', 'TEMPORARY', 'INTERN'
    ))
);
GO

-- Add FK from departments.head_employee_id to employees.id
ALTER TABLE [dbo].[departments]
    ADD CONSTRAINT [FK_departments_head_employee]
    FOREIGN KEY ([head_employee_id]) REFERENCES [dbo].[employees]([id]);
GO

-- Add FK from users.employee_id to employees.id
ALTER TABLE [dbo].[users]
    ADD CONSTRAINT [FK_users_employee]
    FOREIGN KEY ([employee_id]) REFERENCES [dbo].[employees]([id]);
GO

-- ============================================================
-- TABLE: employee_cards
-- Purpose: RFID/NFC card assignment & lifecycle management
-- Django:  EmployeeCard model
-- Notes:   - Only ONE active card per employee at a time
--          - Lost/deactivated cards remain in history
--          - Guest cards handled separately in guest_cards table
-- ============================================================
CREATE TABLE [dbo].[employee_cards] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [employee_id]           INT                 NOT NULL,
    [card_number]           NVARCHAR(100)       NOT NULL,   -- RFID/NFC card UID
    [card_type]             NVARCHAR(50)        NOT NULL DEFAULT 'RFID',
        -- RFID, NFC, BARCODE
    [issued_date]           DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [expiry_date]           DATE                NULL,
    [card_status]           NVARCHAR(20)        NOT NULL DEFAULT 'ACTIVE',
        -- ACTIVE, INACTIVE, LOST, DAMAGED, EXPIRED, REPLACED
    [deactivated_at]        DATETIME2(7)        NULL,
    [deactivation_reason]   NVARCHAR(200)       NULL,
    [replaced_by_card_id]   INT                 NULL,       -- FK to replacement card
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_employee_cards] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_employee_cards_number] UNIQUE ([card_number]),
    CONSTRAINT [FK_employee_cards_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_employee_cards_replaced_by] FOREIGN KEY ([replaced_by_card_id])
        REFERENCES [dbo].[employee_cards]([id]),
    CONSTRAINT [CK_employee_cards_type] CHECK ([card_type] IN ('RFID', 'NFC', 'BARCODE')),
    CONSTRAINT [CK_employee_cards_status] CHECK ([card_status] IN (
        'ACTIVE', 'INACTIVE', 'LOST', 'DAMAGED', 'EXPIRED', 'REPLACED'
    ))
);
GO

PRINT '============================================================';
PRINT 'Employee Management tables created successfully (3 tables).';
PRINT '============================================================';
GO
