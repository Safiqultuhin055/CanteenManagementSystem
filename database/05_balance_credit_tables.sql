-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — BALANCE & CREDIT TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Employee balances, allocations, monthly
--                   allowances, credit limits, card transactions
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: employee_balances
-- Purpose: Current balance snapshot per employee
-- Django:  EmployeeBalance model
-- Notes:   - One record per employee (running balance)
--          - advance_balance = prepaid balance
--          - credit_used = currently consumed credit
--          - Deduction order: advance → credit → reject
-- ============================================================
CREATE TABLE [dbo].[employee_balances] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [employee_id]           INT                 NOT NULL,
    [advance_balance]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,  -- prepaid balance
    [credit_limit]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,  -- approved credit limit
    [credit_used]           DECIMAL(18,2)       NOT NULL DEFAULT 0.00,  -- current credit usage
    [total_allocated]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,  -- lifetime allocations
    [total_spent]           DECIMAL(18,2)       NOT NULL DEFAULT 0.00,  -- lifetime spending
    [last_transaction_at]   DATETIME2(7)        NULL,
    [updated_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_employee_balances] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_employee_balances_employee] UNIQUE ([employee_id]),
    CONSTRAINT [FK_employee_balances_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [CK_employee_balances_advance] CHECK ([advance_balance] >= 0),
    CONSTRAINT [CK_employee_balances_credit_limit] CHECK ([credit_limit] >= 0),
    CONSTRAINT [CK_employee_balances_credit_used] CHECK ([credit_used] >= 0)
);
GO

-- ============================================================
-- TABLE: balance_allocations
-- Purpose: Track every balance allocation/top-up/adjustment
-- Django:  BalanceAllocation model
-- ============================================================
CREATE TABLE [dbo].[balance_allocations] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [employee_id]           INT                 NOT NULL,
    [allocation_type]       NVARCHAR(50)        NOT NULL,
        -- ADVANCE_TOPUP, MONTHLY_ALLOWANCE, CREDIT_ADJUSTMENT,
        -- REFUND, MANUAL_ADJUSTMENT, OPENING_BALANCE
    [amount]                DECIMAL(18,2)       NOT NULL,
    [balance_before]        DECIMAL(18,2)       NOT NULL,
    [balance_after]         DECIMAL(18,2)       NOT NULL,
    [allocation_date]       DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [reference_number]      NVARCHAR(100)       NULL,
    [remarks]               NVARCHAR(500)       NULL,
    [approved_by]           INT                 NULL,
    [approved_at]           DATETIME2(7)        NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_balance_allocations] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_balance_allocations_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_balance_allocations_approved_by] FOREIGN KEY ([approved_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_balance_allocations_amount] CHECK ([amount] != 0),
    CONSTRAINT [CK_balance_allocations_type] CHECK ([allocation_type] IN (
        'ADVANCE_TOPUP', 'MONTHLY_ALLOWANCE', 'CREDIT_ADJUSTMENT',
        'REFUND', 'MANUAL_ADJUSTMENT', 'OPENING_BALANCE'
    ))
);
GO

-- ============================================================
-- TABLE: monthly_allowances
-- Purpose: Bulk monthly balance allocation records
-- Django:  MonthlyAllowance model
-- Notes:   - Supports bulk allocation for a department or all
-- ============================================================
CREATE TABLE [dbo].[monthly_allowances] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [allowance_month]       INT                 NOT NULL,   -- 1-12
    [allowance_year]        INT                 NOT NULL,   -- e.g., 2026
    [department_id]         INT                 NULL,       -- NULL = all departments
    [amount_per_employee]   DECIMAL(18,2)       NOT NULL,
    [total_employees]       INT                 NOT NULL DEFAULT 0,
    [total_amount]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [allocation_status]     NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, PROCESSING, COMPLETED, FAILED
    [allocated_at]          DATETIME2(7)        NULL,
    [allocated_by]          INT                 NULL,
    [remarks]               NVARCHAR(500)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_monthly_allowances] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_monthly_allowances_department] FOREIGN KEY ([department_id])
        REFERENCES [dbo].[departments]([id]),
    CONSTRAINT [FK_monthly_allowances_allocated_by] FOREIGN KEY ([allocated_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_monthly_allowances_month] CHECK ([allowance_month] BETWEEN 1 AND 12),
    CONSTRAINT [CK_monthly_allowances_year] CHECK ([allowance_year] BETWEEN 2000 AND 2099),
    CONSTRAINT [CK_monthly_allowances_amount] CHECK ([amount_per_employee] > 0),
    CONSTRAINT [CK_monthly_allowances_status] CHECK ([allocation_status] IN (
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    ))
);
GO

-- ============================================================
-- TABLE: credit_limits
-- Purpose: Credit limit approval history
-- Django:  CreditLimit model
-- ============================================================
CREATE TABLE [dbo].[credit_limits] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [employee_id]           INT                 NOT NULL,
    [previous_limit]        DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [new_limit]             DECIMAL(18,2)       NOT NULL,
    [effective_from]        DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [effective_to]          DATE                NULL,
    [approved_by]           INT                 NULL,
    [approved_at]           DATETIME2(7)        NULL,
    [approval_status]       NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, APPROVED, REJECTED
    [reason]                NVARCHAR(500)       NULL,
    [remarks]               NVARCHAR(500)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_credit_limits] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_credit_limits_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_credit_limits_approved_by] FOREIGN KEY ([approved_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_credit_limits_new] CHECK ([new_limit] >= 0),
    CONSTRAINT [CK_credit_limits_status] CHECK ([approval_status] IN ('PENDING', 'APPROVED', 'REJECTED'))
);
GO

-- ============================================================
-- TABLE: card_transactions
-- Purpose: Complete transaction history for every card swipe
-- Django:  CardTransaction model
-- Notes:   - Every financial movement is recorded here
--          - Supports DEBIT and CREDIT transactions
-- ============================================================
CREATE TABLE [dbo].[card_transactions] (
    [id]                        INT IDENTITY(1,1)   NOT NULL,
    [transaction_number]        NVARCHAR(50)        NOT NULL,  -- auto: TXN-20260515-0001
    [employee_id]               INT                 NULL,       -- NULL for guest
    [card_id]                   INT                 NULL,       -- employee_card or guest_card FK
    [transaction_type]          NVARCHAR(50)        NOT NULL,
        -- SALE_DEBIT, ADVANCE_TOPUP, MONTHLY_ALLOWANCE, CREDIT_DEBIT,
        -- REFUND, MANUAL_ADJUSTMENT, CASH_SALE
    [transaction_date]          DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [amount]                    DECIMAL(18,2)       NOT NULL,
    [advance_balance_before]    DECIMAL(18,2)       NULL,
    [advance_balance_after]     DECIMAL(18,2)       NULL,
    [credit_used_before]        DECIMAL(18,2)       NULL,
    [credit_used_after]         DECIMAL(18,2)       NULL,
    [order_id]                  INT                 NULL,       -- FK to orders
    [payment_id]                INT                 NULL,       -- FK to payments
    [reference_number]          NVARCHAR(100)       NULL,
    [remarks]                   NVARCHAR(500)       NULL,
    [is_active]                 BIT                 NOT NULL DEFAULT 1,
    [is_deleted]                BIT                 NOT NULL DEFAULT 0,
    [created_by]                INT                 NULL,
    [created_at]                DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_card_transactions] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_card_transactions_number] UNIQUE ([transaction_number]),
    CONSTRAINT [FK_card_transactions_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_card_transactions_card] FOREIGN KEY ([card_id])
        REFERENCES [dbo].[employee_cards]([id]),
    CONSTRAINT [CK_card_transactions_amount] CHECK ([amount] != 0),
    CONSTRAINT [CK_card_transactions_type] CHECK ([transaction_type] IN (
        'SALE_DEBIT', 'ADVANCE_TOPUP', 'MONTHLY_ALLOWANCE', 'CREDIT_DEBIT',
        'REFUND', 'MANUAL_ADJUSTMENT', 'CASH_SALE'
    ))
);
GO

PRINT '===========================================================';
PRINT 'Balance & Credit tables created successfully (5 tables).';
PRINT '===========================================================';
GO
