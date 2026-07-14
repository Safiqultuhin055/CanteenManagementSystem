-- Voice ordering request logs — captures what customers ask the Bangla voice
-- assistant so demand can be analysed (what they say, which products they want).
-- Safe to re-run.
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'voice_request_logs')
BEGIN
    CREATE TABLE [dbo].[voice_request_logs] (
        [id]                INT IDENTITY(1,1) PRIMARY KEY,
        [customer_name]     NVARCHAR(300) NULL,       -- card holder / guest, if known
        [user_text]         NVARCHAR(MAX) NULL,       -- the customer's last spoken request
        [reply_text]        NVARCHAR(MAX) NULL,       -- assistant reply for this turn
        [provider]          NVARCHAR(50)  NULL,       -- anthropic | gemini | local
        [item_count]        INT NOT NULL DEFAULT 0,   -- distinct lines in the order snapshot
        [qty_total]         INT NOT NULL DEFAULT 0,
        [subtotal]          DECIMAL(18,2) NOT NULL DEFAULT 0.00,
        [needs_more_info]   BIT NOT NULL DEFAULT 0,   -- assistant was waiting on the customer
        [ready_to_confirm]  BIT NOT NULL DEFAULT 0,   -- true = confirmed demand (strongest signal)
        [issues]            NVARCHAR(MAX) NULL,        -- stock/availability notes raised this turn
        [created_at]        DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );
    PRINT 'Created table voice_request_logs';
END
ELSE
    PRINT 'voice_request_logs already exists';
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_voice_request_logs_created')
    CREATE INDEX [IX_voice_request_logs_created]
        ON [dbo].[voice_request_logs] ([created_at], [ready_to_confirm]);
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'voice_request_items')
BEGIN
    CREATE TABLE [dbo].[voice_request_items] (
        [id]                    INT IDENTITY(1,1) PRIMARY KEY,
        [voice_request_log_id]  INT NOT NULL,
        [menu_item_id]          INT NULL,             -- matched menu item (NULL if item was dropped)
        [item_name]             NVARCHAR(300) NULL,
        [item_name_bn]          NVARCHAR(300) NULL,
        [quantity]              INT NOT NULL DEFAULT 0,
        [unit_price]            DECIMAL(18,2) NOT NULL DEFAULT 0.00,
        [line_total]            DECIMAL(18,2) NOT NULL DEFAULT 0.00,
        [created_at]            DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT [FK_voice_request_items_log] FOREIGN KEY ([voice_request_log_id])
            REFERENCES [dbo].[voice_request_logs] ([id]) ON DELETE CASCADE
    );
    PRINT 'Created table voice_request_items';
END
ELSE
    PRINT 'voice_request_items already exists';
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_voice_request_items_menu_item')
    CREATE INDEX [IX_voice_request_items_menu_item]
        ON [dbo].[voice_request_items] ([menu_item_id], [created_at]);
GO
