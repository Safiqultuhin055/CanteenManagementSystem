-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — SALES & POS TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Guest cards, orders, order details,
--                   payments, kitchen queue, distribution queue,
--                   token status history
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: guest_cards
-- Purpose: Temporary RFID/NFC cards for guests/visitors
-- Django:  GuestCard model
-- Notes:   - Separate from employee cards
--          - Can be reusable (reassigned to new guest)
--          - Deposit may be required
-- ============================================================
CREATE TABLE [dbo].[guest_cards] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [card_number]           NVARCHAR(100)       NOT NULL,
    [guest_name]            NVARCHAR(300)       NOT NULL,
    [guest_phone]           NVARCHAR(20)        NULL,
    [guest_company]         NVARCHAR(200)       NULL,
    [host_employee_id]      INT                 NULL,       -- sponsoring employee
    [card_type]             NVARCHAR(50)        NOT NULL DEFAULT 'RFID',
    [issued_date]           DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [return_date]           DATE                NULL,
    [deposit_amount]        DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [deposit_returned]      BIT                 NOT NULL DEFAULT 0,
    [loaded_balance]        DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [used_balance]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [remaining_balance]     AS ([loaded_balance] - [used_balance]) PERSISTED,
    [card_status]           NVARCHAR(20)        NOT NULL DEFAULT 'ACTIVE',
        -- ACTIVE, RETURNED, EXPIRED, LOST
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_guest_cards] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_guest_cards_number] UNIQUE ([card_number]),
    CONSTRAINT [FK_guest_cards_host] FOREIGN KEY ([host_employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [CK_guest_cards_type] CHECK ([card_type] IN ('RFID', 'NFC', 'BARCODE')),
    CONSTRAINT [CK_guest_cards_status] CHECK ([card_status] IN ('ACTIVE', 'RETURNED', 'EXPIRED', 'LOST')),
    CONSTRAINT [CK_guest_cards_deposit] CHECK ([deposit_amount] >= 0),
    CONSTRAINT [CK_guest_cards_loaded] CHECK ([loaded_balance] >= 0),
    CONSTRAINT [CK_guest_cards_used] CHECK ([used_balance] >= 0)
);
GO

-- ============================================================
-- TABLE: orders
-- Purpose: POS order header (employee card, guest card, or cash)
-- Django:  Order model
-- Notes:   - token_number resets daily
--          - order_type: EMPLOYEE, GUEST, CASH
-- ============================================================
CREATE TABLE [dbo].[orders] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [order_number]          NVARCHAR(50)        NOT NULL,   -- ORD-20260515-0001
    [token_number]          INT                 NOT NULL,   -- daily sequential: 1, 2, 3...
    [order_date]            DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [order_time]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [order_type]            NVARCHAR(20)        NOT NULL DEFAULT 'EMPLOYEE',
        -- EMPLOYEE, GUEST, CASH
    [employee_id]           INT                 NULL,       -- FK for employee orders
    [employee_card_id]      INT                 NULL,       -- FK for card used
    [guest_card_id]         INT                 NULL,       -- FK for guest orders
    [customer_name]         NVARCHAR(300)       NULL,       -- for cash billing
    [subtotal]              DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [tax_amount]            DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [discount_amount]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [total_amount]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [payment_method]        NVARCHAR(20)        NOT NULL DEFAULT 'CARD',
        -- CARD, CASH, CREDIT, MIXED
    [payment_status]        NVARCHAR(20)        NOT NULL DEFAULT 'PAID',
        -- PAID, PENDING, PARTIALLY_PAID, REFUNDED
    [order_status]          NVARCHAR(20)        NOT NULL DEFAULT 'PLACED',
        -- PLACED, CONFIRMED, PREPARING, READY, DELIVERED, CANCELLED
    [kitchen_status]        NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, IN_PROGRESS, READY, SERVED
    [distribution_status]   NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, READY_FOR_PICKUP, PICKED_UP, DELIVERED
    [advance_deducted]      DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [credit_deducted]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [cash_received]         DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [change_given]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [remarks]               NVARCHAR(500)       NULL,
    [cancelled_at]          DATETIME2(7)        NULL,
    [cancelled_by]          INT                 NULL,
    [cancellation_reason]   NVARCHAR(500)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,       -- cashier
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_orders] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_orders_number] UNIQUE ([order_number]),
    CONSTRAINT [UQ_orders_token_date] UNIQUE ([token_number], [order_date]),
    CONSTRAINT [FK_orders_employee] FOREIGN KEY ([employee_id])
        REFERENCES [dbo].[employees]([id]),
    CONSTRAINT [FK_orders_employee_card] FOREIGN KEY ([employee_card_id])
        REFERENCES [dbo].[employee_cards]([id]),
    CONSTRAINT [FK_orders_guest_card] FOREIGN KEY ([guest_card_id])
        REFERENCES [dbo].[guest_cards]([id]),
    CONSTRAINT [FK_orders_cancelled_by] FOREIGN KEY ([cancelled_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_orders_type] CHECK ([order_type] IN ('EMPLOYEE', 'GUEST', 'CASH')),
    CONSTRAINT [CK_orders_payment_method] CHECK ([payment_method] IN ('CARD', 'CASH', 'CREDIT', 'MIXED')),
    CONSTRAINT [CK_orders_payment_status] CHECK ([payment_status] IN ('PAID', 'PENDING', 'PARTIALLY_PAID', 'REFUNDED')),
    CONSTRAINT [CK_orders_status] CHECK ([order_status] IN (
        'PLACED', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'CANCELLED'
    )),
    CONSTRAINT [CK_orders_kitchen_status] CHECK ([kitchen_status] IN (
        'PENDING', 'IN_PROGRESS', 'READY', 'SERVED'
    )),
    CONSTRAINT [CK_orders_distribution_status] CHECK ([distribution_status] IN (
        'PENDING', 'READY_FOR_PICKUP', 'PICKED_UP', 'DELIVERED'
    )),
    CONSTRAINT [CK_orders_total] CHECK ([total_amount] >= 0),
    CONSTRAINT [CK_orders_subtotal] CHECK ([subtotal] >= 0)
);
GO

-- ============================================================
-- TABLE: order_details
-- Purpose: Line items for each order
-- Django:  OrderDetail model
-- ============================================================
CREATE TABLE [dbo].[order_details] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [order_id]              INT                 NOT NULL,
    [menu_item_id]          INT                 NOT NULL,
    [daily_food_stock_id]   INT                 NULL,       -- link to daily stock entry
    [item_name]             NVARCHAR(300)       NOT NULL,   -- snapshot of item name
    [quantity]              INT                 NOT NULL DEFAULT 1,
    [unit_price]            DECIMAL(18,2)       NOT NULL,   -- snapshot of price at order time
    [tax_rate]              DECIMAL(5,2)        NOT NULL DEFAULT 0.00,
    [tax_amount]            DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [discount_amount]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [total_price]           DECIMAL(18,2)       NOT NULL,
    [special_instructions]  NVARCHAR(300)       NULL,
    [item_status]           NVARCHAR(20)        NOT NULL DEFAULT 'ORDERED',
        -- ORDERED, PREPARING, READY, SERVED, CANCELLED
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_order_details] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_order_details_order] FOREIGN KEY ([order_id])
        REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [FK_order_details_menu_item] FOREIGN KEY ([menu_item_id])
        REFERENCES [dbo].[menu_items]([id]),
    CONSTRAINT [FK_order_details_daily_stock] FOREIGN KEY ([daily_food_stock_id])
        REFERENCES [dbo].[daily_food_stock]([id]),
    CONSTRAINT [CK_order_details_qty] CHECK ([quantity] > 0),
    CONSTRAINT [CK_order_details_price] CHECK ([unit_price] >= 0),
    CONSTRAINT [CK_order_details_total] CHECK ([total_price] >= 0),
    CONSTRAINT [CK_order_details_status] CHECK ([item_status] IN (
        'ORDERED', 'PREPARING', 'READY', 'SERVED', 'CANCELLED'
    ))
);
GO

-- ============================================================
-- TABLE: payments
-- Purpose: Payment records for orders
-- Django:  Payment model
-- Notes:   - An order can have multiple payments (split pay)
-- ============================================================
CREATE TABLE [dbo].[payments] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [payment_number]        NVARCHAR(50)        NOT NULL,   -- PAY-20260515-0001
    [order_id]              INT                 NOT NULL,
    [payment_method]        NVARCHAR(20)        NOT NULL,
        -- CARD, CASH, CREDIT
    [amount]                DECIMAL(18,2)       NOT NULL,
    [payment_date]          DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [payment_status]        NVARCHAR(20)        NOT NULL DEFAULT 'COMPLETED',
        -- COMPLETED, PENDING, FAILED, REFUNDED
    [employee_card_id]      INT                 NULL,
    [guest_card_id]         INT                 NULL,
    [transaction_id]        INT                 NULL,       -- FK to card_transactions
    [receipt_number]        NVARCHAR(50)        NULL,
    [remarks]               NVARCHAR(300)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_payments] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_payments_number] UNIQUE ([payment_number]),
    CONSTRAINT [FK_payments_order] FOREIGN KEY ([order_id])
        REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [FK_payments_employee_card] FOREIGN KEY ([employee_card_id])
        REFERENCES [dbo].[employee_cards]([id]),
    CONSTRAINT [FK_payments_guest_card] FOREIGN KEY ([guest_card_id])
        REFERENCES [dbo].[guest_cards]([id]),
    CONSTRAINT [FK_payments_transaction] FOREIGN KEY ([transaction_id])
        REFERENCES [dbo].[card_transactions]([id]),
    CONSTRAINT [CK_payments_method] CHECK ([payment_method] IN ('CARD', 'CASH', 'CREDIT')),
    CONSTRAINT [CK_payments_amount] CHECK ([amount] > 0),
    CONSTRAINT [CK_payments_status] CHECK ([payment_status] IN ('COMPLETED', 'PENDING', 'FAILED', 'REFUNDED'))
);
GO

-- ============================================================
-- TABLE: kitchen_queue
-- Purpose: Kitchen display queue for order processing
-- Django:  KitchenQueue model
-- Notes:   - One entry per order for kitchen tracking
--          - Supports real-time display
-- ============================================================
CREATE TABLE [dbo].[kitchen_queue] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [order_id]              INT                 NOT NULL,
    [token_number]          INT                 NOT NULL,
    [queue_date]            DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [queue_status]          NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, IN_PROGRESS, READY, SERVED, CANCELLED
    [priority]              INT                 NOT NULL DEFAULT 0,   -- 0=normal, 1=high
    [estimated_time_min]    INT                 NULL,
    [accepted_at]           DATETIME2(7)        NULL,
    [started_at]            DATETIME2(7)        NULL,
    [completed_at]          DATETIME2(7)        NULL,
    [assigned_to]           INT                 NULL,       -- kitchen staff user_id
    [remarks]               NVARCHAR(300)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_kitchen_queue] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_kitchen_queue_order] FOREIGN KEY ([order_id])
        REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [FK_kitchen_queue_assigned_to] FOREIGN KEY ([assigned_to])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [UQ_kitchen_queue_order] UNIQUE ([order_id]),
    CONSTRAINT [CK_kitchen_queue_status] CHECK ([queue_status] IN (
        'PENDING', 'IN_PROGRESS', 'READY', 'SERVED', 'CANCELLED'
    ))
);
GO

-- ============================================================
-- TABLE: distribution_queue
-- Purpose: Distribution counter queue for order pickup
-- Django:  DistributionQueue model
-- ============================================================
CREATE TABLE [dbo].[distribution_queue] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [order_id]              INT                 NOT NULL,
    [token_number]          INT                 NOT NULL,
    [queue_date]            DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [queue_status]          NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, READY_FOR_PICKUP, PICKED_UP, NOT_COLLECTED
    [called_at]             DATETIME2(7)        NULL,       -- when token was called
    [picked_up_at]          DATETIME2(7)        NULL,
    [counter_number]        INT                 NULL,       -- distribution counter #
    [handled_by]            INT                 NULL,       -- distribution staff
    [remarks]               NVARCHAR(300)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_distribution_queue] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_distribution_queue_order] FOREIGN KEY ([order_id])
        REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [FK_distribution_queue_handled_by] FOREIGN KEY ([handled_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [UQ_distribution_queue_order] UNIQUE ([order_id]),
    CONSTRAINT [CK_distribution_queue_status] CHECK ([queue_status] IN (
        'PENDING', 'READY_FOR_PICKUP', 'PICKED_UP', 'NOT_COLLECTED'
    ))
);
GO

-- ============================================================
-- TABLE: token_status_history
-- Purpose: Track token status changes over time
-- Django:  TokenStatusHistory model
-- ============================================================
CREATE TABLE [dbo].[token_status_history] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [order_id]              INT                 NOT NULL,
    [token_number]          INT                 NOT NULL,
    [status_from]           NVARCHAR(30)        NULL,
    [status_to]             NVARCHAR(30)        NOT NULL,
    [status_type]           NVARCHAR(20)        NOT NULL,   -- 'KITCHEN', 'DISTRIBUTION', 'ORDER'
    [changed_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [changed_by]            INT                 NULL,
    [remarks]               NVARCHAR(300)       NULL,

    CONSTRAINT [PK_token_status_history] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_token_status_history_order] FOREIGN KEY ([order_id])
        REFERENCES [dbo].[orders]([id]),
    CONSTRAINT [FK_token_status_history_changed_by] FOREIGN KEY ([changed_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_token_status_history_type] CHECK ([status_type] IN ('KITCHEN', 'DISTRIBUTION', 'ORDER'))
);
GO

PRINT '==========================================================';
PRINT 'Sales & POS tables created successfully (7 tables).';
PRINT '==========================================================';
GO
