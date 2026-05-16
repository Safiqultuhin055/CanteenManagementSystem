-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — FOOD & INVENTORY TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Food categories, menu items, suppliers,
--                   raw materials, stock, purchases, preparation,
--                   daily food stock, waste records
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: food_categories
-- Purpose: Categorize menu items (Breakfast, Lunch, Snacks, etc.)
-- Django:  FoodCategory model
-- ============================================================
CREATE TABLE [dbo].[food_categories] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [category_name]     NVARCHAR(200)       NOT NULL,
    [category_code]     NVARCHAR(50)        NOT NULL,
    [description]       NVARCHAR(500)       NULL,
    [display_order]     INT                 NOT NULL DEFAULT 0,
    [image_path]        NVARCHAR(500)       NULL,
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [is_deleted]        BIT                 NOT NULL DEFAULT 0,
    [created_by]        INT                 NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]        INT                 NULL,
    [updated_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_food_categories] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_food_categories_code] UNIQUE ([category_code]),
    CONSTRAINT [UQ_food_categories_name] UNIQUE ([category_name])
);
GO

-- ============================================================
-- TABLE: menu_items
-- Purpose: Individual food/drink items available for sale
-- Django:  MenuItem model
-- ============================================================
CREATE TABLE [dbo].[menu_items] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [item_name]             NVARCHAR(300)       NOT NULL,
    [item_code]             NVARCHAR(50)        NOT NULL,
    [category_id]           INT                 NOT NULL,
    [description]           NVARCHAR(500)       NULL,
    [unit_price]            DECIMAL(18,2)       NOT NULL,
    [cost_price]            DECIMAL(18,2)       NULL,       -- for profit calculation
    [unit_of_measure]       NVARCHAR(50)        NOT NULL DEFAULT 'Plate',
        -- Plate, Piece, Cup, Bowl, Glass, Kg, Liter
    [preparation_time_min]  INT                 NULL,       -- estimated prep time in minutes
    [calorie_count]         INT                 NULL,
    [is_vegetarian]         BIT                 NOT NULL DEFAULT 0,
    [tax_rate]              DECIMAL(5,2)        NOT NULL DEFAULT 0.00,  -- GST/VAT percentage
    [barcode]               NVARCHAR(100)       NULL,
    [image_path]            NVARCHAR(500)       NULL,
    [display_order]         INT                 NOT NULL DEFAULT 0,
    [is_available]          BIT                 NOT NULL DEFAULT 1,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_menu_items] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_menu_items_code] UNIQUE ([item_code]),
    CONSTRAINT [FK_menu_items_category] FOREIGN KEY ([category_id])
        REFERENCES [dbo].[food_categories]([id]),
    CONSTRAINT [CK_menu_items_unit_price] CHECK ([unit_price] >= 0),
    CONSTRAINT [CK_menu_items_cost_price] CHECK ([cost_price] IS NULL OR [cost_price] >= 0),
    CONSTRAINT [CK_menu_items_tax_rate] CHECK ([tax_rate] >= 0 AND [tax_rate] <= 100)
);
GO

-- ============================================================
-- TABLE: suppliers
-- Purpose: Vendor/supplier master for raw material procurement
-- Django:  Supplier model
-- ============================================================
CREATE TABLE [dbo].[suppliers] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [supplier_name]     NVARCHAR(300)       NOT NULL,
    [supplier_code]     NVARCHAR(50)        NOT NULL,
    [contact_person]    NVARCHAR(200)       NULL,
    [phone]             NVARCHAR(20)        NULL,
    [email]             NVARCHAR(254)       NULL,
    [address]           NVARCHAR(500)       NULL,
    [city]              NVARCHAR(100)       NULL,
    [tax_id]            NVARCHAR(50)        NULL,       -- VAT/GST registration
    [payment_terms]     NVARCHAR(200)       NULL,       -- e.g., 'Net 30'
    [rating]            DECIMAL(3,2)        NULL,       -- 0.00 to 5.00
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [is_deleted]        BIT                 NOT NULL DEFAULT 0,
    [created_by]        INT                 NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]        INT                 NULL,
    [updated_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_suppliers] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_suppliers_code] UNIQUE ([supplier_code]),
    CONSTRAINT [CK_suppliers_rating] CHECK ([rating] IS NULL OR ([rating] >= 0 AND [rating] <= 5))
);
GO

-- ============================================================
-- TABLE: raw_materials
-- Purpose: Raw ingredients used for food preparation
-- Django:  RawMaterial model
-- ============================================================
CREATE TABLE [dbo].[raw_materials] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [material_name]         NVARCHAR(300)       NOT NULL,
    [material_code]         NVARCHAR(50)        NOT NULL,
    [category]              NVARCHAR(100)       NULL,   -- Vegetables, Spices, Oils, etc.
    [unit_of_measure]       NVARCHAR(50)        NOT NULL DEFAULT 'Kg',
        -- Kg, Liter, Piece, Packet, Dozen
    [minimum_stock_level]   DECIMAL(18,3)       NOT NULL DEFAULT 5.000,  -- low stock threshold
    [reorder_level]         DECIMAL(18,3)       NULL,
    [default_supplier_id]   INT                 NULL,
    [is_perishable]         BIT                 NOT NULL DEFAULT 1,
    [shelf_life_days]       INT                 NULL,
    [storage_instructions]  NVARCHAR(500)       NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_raw_materials] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_raw_materials_code] UNIQUE ([material_code]),
    CONSTRAINT [FK_raw_materials_supplier] FOREIGN KEY ([default_supplier_id])
        REFERENCES [dbo].[suppliers]([id]),
    CONSTRAINT [CK_raw_materials_min_stock] CHECK ([minimum_stock_level] >= 0)
);
GO

-- ============================================================
-- TABLE: raw_material_stock
-- Purpose: Current stock levels for raw materials
-- Django:  RawMaterialStock model
-- Notes:   - One record per material (running balance)
--          - Stock cannot go negative
-- ============================================================
CREATE TABLE [dbo].[raw_material_stock] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [raw_material_id]       INT                 NOT NULL,
    [current_quantity]      DECIMAL(18,3)       NOT NULL DEFAULT 0.000,
    [last_purchase_price]   DECIMAL(18,2)       NULL,
    [average_price]         DECIMAL(18,2)       NULL,
    [last_restocked_at]     DATETIME2(7)        NULL,
    [expiry_date]           DATE                NULL,       -- nearest expiry batch
    [updated_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_raw_material_stock] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_raw_material_stock_material] UNIQUE ([raw_material_id]),
    CONSTRAINT [FK_raw_material_stock_material] FOREIGN KEY ([raw_material_id])
        REFERENCES [dbo].[raw_materials]([id]),
    CONSTRAINT [CK_raw_material_stock_qty] CHECK ([current_quantity] >= 0)
);
GO

-- ============================================================
-- TABLE: stock_purchases
-- Purpose: Purchase order header for raw materials
-- Django:  StockPurchase model
-- ============================================================
CREATE TABLE [dbo].[stock_purchases] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [purchase_number]       NVARCHAR(50)        NOT NULL,   -- auto-generated: PO-20260515-001
    [supplier_id]           INT                 NOT NULL,
    [purchase_date]         DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [total_amount]          DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [discount_amount]       DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [tax_amount]            DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [net_amount]            DECIMAL(18,2)       NOT NULL DEFAULT 0.00,
    [payment_status]        NVARCHAR(20)        NOT NULL DEFAULT 'PENDING',
        -- PENDING, PARTIAL, PAID
    [payment_date]          DATE                NULL,
    [invoice_number]        NVARCHAR(100)       NULL,
    [remarks]               NVARCHAR(500)       NULL,
    [approved_by]           INT                 NULL,
    [approved_at]           DATETIME2(7)        NULL,
    [purchase_status]       NVARCHAR(20)        NOT NULL DEFAULT 'DRAFT',
        -- DRAFT, SUBMITTED, APPROVED, RECEIVED, CANCELLED
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_stock_purchases] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_stock_purchases_number] UNIQUE ([purchase_number]),
    CONSTRAINT [FK_stock_purchases_supplier] FOREIGN KEY ([supplier_id])
        REFERENCES [dbo].[suppliers]([id]),
    CONSTRAINT [FK_stock_purchases_approved_by] FOREIGN KEY ([approved_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_stock_purchases_total] CHECK ([total_amount] >= 0),
    CONSTRAINT [CK_stock_purchases_net] CHECK ([net_amount] >= 0),
    CONSTRAINT [CK_stock_purchases_payment_status] CHECK ([payment_status] IN ('PENDING', 'PARTIAL', 'PAID')),
    CONSTRAINT [CK_stock_purchases_status] CHECK ([purchase_status] IN (
        'DRAFT', 'SUBMITTED', 'APPROVED', 'RECEIVED', 'CANCELLED'
    ))
);
GO

-- ============================================================
-- TABLE: stock_purchase_details
-- Purpose: Line items for each purchase order
-- Django:  StockPurchaseDetail model
-- ============================================================
CREATE TABLE [dbo].[stock_purchase_details] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [purchase_id]           INT                 NOT NULL,
    [raw_material_id]       INT                 NOT NULL,
    [quantity]              DECIMAL(18,3)       NOT NULL,
    [unit_price]            DECIMAL(18,2)       NOT NULL,
    [total_price]           DECIMAL(18,2)       NOT NULL,
    [received_quantity]     DECIMAL(18,3)       NOT NULL DEFAULT 0.000,
    [manufacturing_date]    DATE                NULL,
    [expiry_date]           DATE                NULL,
    [batch_number]          NVARCHAR(100)       NULL,
    [remarks]               NVARCHAR(300)       NULL,

    CONSTRAINT [PK_stock_purchase_details] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_stock_purchase_details_purchase] FOREIGN KEY ([purchase_id])
        REFERENCES [dbo].[stock_purchases]([id]),
    CONSTRAINT [FK_stock_purchase_details_material] FOREIGN KEY ([raw_material_id])
        REFERENCES [dbo].[raw_materials]([id]),
    CONSTRAINT [CK_stock_purchase_details_qty] CHECK ([quantity] > 0),
    CONSTRAINT [CK_stock_purchase_details_price] CHECK ([unit_price] >= 0),
    CONSTRAINT [CK_stock_purchase_details_total] CHECK ([total_price] >= 0)
);
GO

-- ============================================================
-- TABLE: daily_food_stock
-- Purpose: Daily prepared food stock available for sale
-- Django:  DailyFoodStock model
-- Notes:   - Reset/created daily
--          - Tracks prepared quantity vs sold quantity
--          - Stock cannot go negative
-- ============================================================
CREATE TABLE [dbo].[daily_food_stock] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [menu_item_id]          INT                 NOT NULL,
    [stock_date]            DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [prepared_quantity]     INT                 NOT NULL DEFAULT 0,
    [sold_quantity]         INT                 NOT NULL DEFAULT 0,
    [waste_quantity]        INT                 NOT NULL DEFAULT 0,
    [remaining_quantity]    AS ([prepared_quantity] - [sold_quantity] - [waste_quantity]) PERSISTED,
    [unit_price]            DECIMAL(18,2)       NOT NULL,   -- price for the day
    [preparation_time]      DATETIME2(7)        NULL,       -- when preparation started
    [ready_time]            DATETIME2(7)        NULL,       -- when food was ready
    [prepared_by]           INT                 NULL,
    [remarks]               NVARCHAR(300)       NULL,
    [is_available]          BIT                 NOT NULL DEFAULT 1,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_daily_food_stock] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_daily_food_stock_menu_item] FOREIGN KEY ([menu_item_id])
        REFERENCES [dbo].[menu_items]([id]),
    CONSTRAINT [FK_daily_food_stock_prepared_by] FOREIGN KEY ([prepared_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [UQ_daily_food_stock_item_date] UNIQUE ([menu_item_id], [stock_date]),
    CONSTRAINT [CK_daily_food_stock_prepared_qty] CHECK ([prepared_quantity] >= 0),
    CONSTRAINT [CK_daily_food_stock_sold_qty] CHECK ([sold_quantity] >= 0),
    CONSTRAINT [CK_daily_food_stock_waste_qty] CHECK ([waste_quantity] >= 0)
);
GO

-- ============================================================
-- TABLE: food_preparation
-- Purpose: Track raw material usage during food preparation
-- Django:  FoodPreparation model
-- Notes:   - Links menu items to raw materials consumed
-- ============================================================
CREATE TABLE [dbo].[food_preparation] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [daily_food_stock_id]   INT                 NOT NULL,
    [raw_material_id]       INT                 NOT NULL,
    [quantity_used]         DECIMAL(18,3)       NOT NULL,
    [unit_of_measure]       NVARCHAR(50)        NOT NULL,
    [remarks]               NVARCHAR(300)       NULL,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_food_preparation] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_food_preparation_daily_stock] FOREIGN KEY ([daily_food_stock_id])
        REFERENCES [dbo].[daily_food_stock]([id]),
    CONSTRAINT [FK_food_preparation_material] FOREIGN KEY ([raw_material_id])
        REFERENCES [dbo].[raw_materials]([id]),
    CONSTRAINT [CK_food_preparation_qty] CHECK ([quantity_used] > 0)
);
GO

-- ============================================================
-- TABLE: waste_records
-- Purpose: Track food waste and raw material waste
-- Django:  WasteRecord model
-- ============================================================
CREATE TABLE [dbo].[waste_records] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [waste_date]            DATE                NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE),
    [waste_type]            NVARCHAR(50)        NOT NULL DEFAULT 'FOOD',
        -- FOOD, RAW_MATERIAL
    [menu_item_id]          INT                 NULL,       -- if waste_type = FOOD
    [raw_material_id]       INT                 NULL,       -- if waste_type = RAW_MATERIAL
    [quantity]              DECIMAL(18,3)       NOT NULL,
    [unit_of_measure]       NVARCHAR(50)        NOT NULL,
    [estimated_cost]        DECIMAL(18,2)       NULL,
    [waste_reason]          NVARCHAR(100)       NOT NULL,
        -- EXPIRED, SPOILED, OVERPRODUCTION, QUALITY_ISSUE, OTHER
    [remarks]               NVARCHAR(500)       NULL,
    [reported_by]           INT                 NULL,
    [verified_by]           INT                 NULL,
    [verified_at]           DATETIME2(7)        NULL,
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_waste_records] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_waste_records_menu_item] FOREIGN KEY ([menu_item_id])
        REFERENCES [dbo].[menu_items]([id]),
    CONSTRAINT [FK_waste_records_material] FOREIGN KEY ([raw_material_id])
        REFERENCES [dbo].[raw_materials]([id]),
    CONSTRAINT [FK_waste_records_reported_by] FOREIGN KEY ([reported_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [FK_waste_records_verified_by] FOREIGN KEY ([verified_by])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_waste_records_type] CHECK ([waste_type] IN ('FOOD', 'RAW_MATERIAL')),
    CONSTRAINT [CK_waste_records_qty] CHECK ([quantity] > 0),
    CONSTRAINT [CK_waste_records_reason] CHECK ([waste_reason] IN (
        'EXPIRED', 'SPOILED', 'OVERPRODUCTION', 'QUALITY_ISSUE', 'OTHER'
    ))
);
GO

PRINT '=============================================================';
PRINT 'Food & Inventory tables created successfully (10 tables).';
PRINT '=============================================================';
GO
