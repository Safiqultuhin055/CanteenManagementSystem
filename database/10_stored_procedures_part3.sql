-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — STORED PROCEDURES (Part 3)
-- Description     : Card validation, token generation, stock checks,
--                   guest/cash sales, kitchen/distribution workflow,
--                   employee requests, audit helper
-- Run Order       : After Part 1 and Part 2
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- FUNCTION: fn_GetNextDailyToken
-- Purpose: Daily token resets; unique per calendar day
-- ============================================================
CREATE OR ALTER FUNCTION [dbo].[fn_GetNextDailyToken]()
RETURNS INT
AS
BEGIN
    DECLARE @NextToken INT;
    SELECT @NextToken = ISNULL(MAX([token_number]), 0) + 1
    FROM [dbo].[orders]
    WHERE [order_date] = CAST(SYSDATETIME() AS DATE);
    RETURN @NextToken;
END;
GO

-- ============================================================
-- SP: usp_ValidateEmployeeCard
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ValidateEmployeeCard]
    @CardNumber NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        DECLARE @CardId INT, @EmployeeId INT, @Status NVARCHAR(20), @IsActive BIT;

        SELECT TOP 1
            @CardId = ec.[id],
            @EmployeeId = ec.[employee_id],
            @Status = ec.[card_status],
            @IsActive = ec.[is_active]
        FROM [dbo].[employee_cards] ec
        WHERE ec.[card_number] = @CardNumber
          AND ec.[is_deleted] = 0
        ORDER BY ec.[id] DESC;

        IF @CardId IS NULL
        BEGIN
            SELECT 0 AS [Success], N'Card not found' AS [Message];
            RETURN;
        END

        IF @IsActive = 0 OR @Status <> N'ACTIVE'
        BEGIN
            SELECT 0 AS [Success], N'Card is inactive or not usable' AS [Message];
            RETURN;
        END

        -- Only one ACTIVE card per employee (business rule)
        IF EXISTS (
            SELECT 1 FROM [dbo].[employee_cards]
            WHERE [employee_id] = @EmployeeId AND [is_active] = 1 AND [card_status] = N'ACTIVE'
              AND [is_deleted] = 0 AND [id] <> @CardId
        )
        BEGIN
            SELECT 0 AS [Success], N'Multiple active cards detected for employee' AS [Message];
            RETURN;
        END

        SELECT
            1 AS [Success],
            N'Card valid' AS [Message],
            ec.[id] AS [card_id],
            e.[id] AS [employee_id],
            e.[employee_code],
            e.[full_name],
            d.[department_name],
            eb.[advance_balance],
            eb.[credit_limit],
            eb.[credit_used],
            (eb.[credit_limit] - eb.[credit_used]) AS [available_credit],
            (eb.[advance_balance] + (eb.[credit_limit] - eb.[credit_used])) AS [purchasing_power]
        FROM [dbo].[employee_cards] ec
        INNER JOIN [dbo].[employees] e ON ec.[employee_id] = e.[id]
        INNER JOIN [dbo].[departments] d ON e.[department_id] = d.[id]
        LEFT JOIN [dbo].[employee_balances] eb ON e.[id] = eb.[employee_id]
        WHERE ec.[id] = @CardId
          AND e.[is_active] = 1 AND e.[is_deleted] = 0;
    END TRY
    BEGIN CATCH
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_ValidateFoodStock
-- Purpose: Ensure daily food stock available; no negative stock
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ValidateFoodStock]
    @MenuItemId INT,
    @Quantity INT,
    @StockDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET @StockDate = ISNULL(@StockDate, CAST(SYSDATETIME() AS DATE));

    DECLARE @Remaining INT, @IsAvailable BIT;

    SELECT
        @Remaining = [remaining_quantity],
        @IsAvailable = [is_available]
    FROM [dbo].[daily_food_stock]
    WHERE [menu_item_id] = @MenuItemId
      AND [stock_date] = @StockDate
      AND [is_deleted] = 0;

    IF @Remaining IS NULL OR @IsAvailable = 0
    BEGIN
        SELECT 0 AS [Success], N'Item not available for sale today' AS [Message];
        RETURN;
    END

    IF @Remaining < @Quantity
    BEGIN
        SELECT 0 AS [Success], N'Insufficient stock' AS [Message], @Remaining AS [available_quantity];
        RETURN;
    END

    SELECT 1 AS [Success], N'Stock available' AS [Message], @Remaining AS [available_quantity];
END;
GO

-- ============================================================
-- SP: usp_InsertAuditLog
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_InsertAuditLog]
    @UserId INT = NULL,
    @Action NVARCHAR(100),
    @TableName NVARCHAR(100) = NULL,
    @RecordId INT = NULL,
    @Module NVARCHAR(100) = NULL,
    @Description NVARCHAR(1000) = NULL,
    @OldValues NVARCHAR(MAX) = NULL,
    @NewValues NVARCHAR(MAX) = NULL,
    @IPAddress NVARCHAR(45) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO [dbo].[audit_logs] (
        [user_id], [action], [table_name], [record_id], [module],
        [description], [old_values], [new_values], [ip_address]
    )
    VALUES (
        @UserId, @Action, @TableName, @RecordId, @Module,
        @Description, @OldValues, @NewValues, @IPAddress
    );
    SELECT SCOPE_IDENTITY() AS [audit_log_id];
END;
GO

-- ============================================================
-- SP: usp_UpdateKitchenStatus
-- Purpose: Kitchen workflow; creates distribution queue when READY
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_UpdateKitchenStatus]
    @QueueId INT,
    @NewStatus NVARCHAR(20),
    @UpdatedBy INT = NULL,
    @Remarks NVARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @OrderId INT, @TokenNumber INT, @OldStatus NVARCHAR(20);

        SELECT @OrderId = [order_id], @TokenNumber = [token_number], @OldStatus = [queue_status]
        FROM [dbo].[kitchen_queue]
        WHERE [id] = @QueueId AND [is_active] = 1;

        IF @OrderId IS NULL
            THROW 50010, 'Kitchen queue entry not found', 1;

        UPDATE [dbo].[kitchen_queue]
        SET [queue_status] = @NewStatus,
            [started_at] = CASE WHEN @NewStatus = N'IN_PROGRESS' AND [started_at] IS NULL THEN SYSDATETIME() ELSE [started_at] END,
            [completed_at] = CASE WHEN @NewStatus = N'READY' THEN SYSDATETIME() ELSE [completed_at] END,
            [updated_at] = SYSDATETIME(),
            [remarks] = ISNULL(@Remarks, [remarks])
        WHERE [id] = @QueueId;

        UPDATE [dbo].[orders]
        SET [kitchen_status] = @NewStatus,
            [order_status] = CASE WHEN @NewStatus = N'READY' THEN N'READY' ELSE [order_status] END,
            [updated_by] = @UpdatedBy,
            [updated_at] = SYSDATETIME()
        WHERE [id] = @OrderId;

        INSERT INTO [dbo].[token_status_history] (
            [order_id], [token_number], [status_from], [status_to], [status_type], [changed_by], [remarks]
        )
        VALUES (@OrderId, @TokenNumber, @OldStatus, @NewStatus, N'KITCHEN', @UpdatedBy, @Remarks);

        IF @NewStatus = N'READY'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM [dbo].[distribution_queue] WHERE [order_id] = @OrderId)
            BEGIN
                INSERT INTO [dbo].[distribution_queue] ([order_id], [token_number], [queue_status])
                VALUES (@OrderId, @TokenNumber, N'PENDING');

                UPDATE [dbo].[orders]
                SET [distribution_status] = N'READY_FOR_PICKUP'
                WHERE [id] = @OrderId;
            END
        END

        EXEC [dbo].[usp_InsertAuditLog]
            @UserId = @UpdatedBy,
            @Action = N'KITCHEN_STATUS_UPDATE',
            @TableName = N'kitchen_queue',
            @RecordId = @QueueId,
            @Module = N'Kitchen',
            @Description = CONCAT(N'Status: ', @OldStatus, N' -> ', @NewStatus);

        COMMIT TRANSACTION;
        SELECT 1 AS [Success], N'Kitchen status updated' AS [Message];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_CompleteDistribution
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_CompleteDistribution]
    @TokenNumber INT,
    @HandledBy INT = NULL,
    @CardVerified BIT = 0,
    @Remarks NVARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @QueueId INT, @OrderId INT, @OldStatus NVARCHAR(20);

        SELECT TOP 1
            @QueueId = [id],
            @OrderId = [order_id],
            @OldStatus = [queue_status]
        FROM [dbo].[distribution_queue]
        WHERE [token_number] = @TokenNumber
          AND [queue_date] = CAST(SYSDATETIME() AS DATE)
          AND [queue_status] IN (N'PENDING', N'CALLED')
        ORDER BY [id];

        IF @QueueId IS NULL
            THROW 50011, 'Token not found in distribution queue', 1;

        UPDATE [dbo].[distribution_queue]
        SET [queue_status] = N'PICKED_UP',
            [picked_up_at] = SYSDATETIME(),
            [handled_by] = @HandledBy,
            [remarks] = ISNULL(@Remarks, [remarks]),
            [updated_at] = SYSDATETIME()
        WHERE [id] = @QueueId;

        UPDATE [dbo].[orders]
        SET [distribution_status] = N'PICKED_UP',
            [order_status] = N'DELIVERED',
            [updated_by] = @HandledBy,
            [updated_at] = SYSDATETIME()
        WHERE [id] = @OrderId;

        INSERT INTO [dbo].[token_status_history] (
            [order_id], [token_number], [status_from], [status_to], [status_type], [changed_by], [remarks]
        )
        VALUES (@OrderId, @TokenNumber, @OldStatus, N'PICKED_UP', N'DISTRIBUTION', @HandledBy,
                CONCAT(N'Card verified: ', CAST(@CardVerified AS NVARCHAR(5)), N'; ', ISNULL(@Remarks, N'')));

        EXEC [dbo].[usp_InsertAuditLog]
            @UserId = @HandledBy,
            @Action = N'DISTRIBUTION_COMPLETE',
            @TableName = N'distribution_queue',
            @RecordId = @QueueId,
            @Module = N'Distribution',
            @Description = CONCAT(N'Token ', @TokenNumber, N' picked up');

        COMMIT TRANSACTION;
        SELECT 1 AS [Success], N'Distribution completed' AS [Message];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_ProcessCashSale
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ProcessCashSale]
    @CustomerName NVARCHAR(300) = NULL,
    @MenuItemId INT,
    @Quantity INT,
    @CashReceived DECIMAL(18,2),
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        CREATE TABLE #StockResult ([Success] INT, [Message] NVARCHAR(200), [available_quantity] INT);
        INSERT INTO #StockResult EXEC [dbo].[usp_ValidateFoodStock] @MenuItemId, @Quantity;
        IF NOT EXISTS (SELECT 1 FROM #StockResult WHERE [Success] = 1)
        BEGIN
            SELECT [Success], [Message] FROM #StockResult;
            ROLLBACK TRANSACTION;
            RETURN;
        END

        DECLARE @UnitPrice DECIMAL(18,2), @ItemName NVARCHAR(300), @TaxRate DECIMAL(5,2);
        SELECT @UnitPrice = [unit_price], @ItemName = [item_name], @TaxRate = [tax_rate]
        FROM [dbo].[menu_items] WHERE [id] = @MenuItemId AND [is_active] = 1;

        DECLARE @LineTotal DECIMAL(18,2) = @UnitPrice * @Quantity;
        DECLARE @TaxAmount DECIMAL(18,2) = ROUND(@LineTotal * @TaxRate / 100.0, 2);
        DECLARE @Total DECIMAL(18,2) = @LineTotal + @TaxAmount;

        IF @CashReceived < @Total
            THROW 50012, 'Insufficient cash received', 1;

        DECLARE @TokenNumber INT = [dbo].[fn_GetNextDailyToken]();
        DECLARE @OrderNumber NVARCHAR(50) = CONCAT(N'ORD-', FORMAT(SYSDATETIME(), 'yyyyMMdd'), N'-', FORMAT(NEXT VALUE FOR [dbo].[seq_order], '0000'));

        INSERT INTO [dbo].[orders] (
            [order_number], [token_number], [order_type], [customer_name],
            [subtotal], [tax_amount], [total_amount], [payment_method], [payment_status],
            [cash_received], [change_given], [created_by]
        )
        VALUES (
            @OrderNumber, @TokenNumber, N'CASH', @CustomerName,
            @LineTotal, @TaxAmount, @Total, N'CASH', N'PAID',
            @CashReceived, @CashReceived - @Total, @CreatedBy
        );

        DECLARE @OrderId INT = SCOPE_IDENTITY();

        DECLARE @DailyStockId INT;
        SELECT @DailyStockId = [id] FROM [dbo].[daily_food_stock]
        WHERE [menu_item_id] = @MenuItemId AND [stock_date] = CAST(SYSDATETIME() AS DATE);

        INSERT INTO [dbo].[order_details] (
            [order_id], [menu_item_id], [daily_food_stock_id], [item_name],
            [quantity], [unit_price], [tax_rate], [tax_amount], [total_price]
        )
        VALUES (
            @OrderId, @MenuItemId, @DailyStockId, @ItemName,
            @Quantity, @UnitPrice, @TaxRate, @TaxAmount, @Total
        );

        UPDATE [dbo].[daily_food_stock]
        SET [sold_quantity] = [sold_quantity] + @Quantity,
            [updated_at] = SYSDATETIME()
        WHERE [id] = @DailyStockId;

        INSERT INTO [dbo].[kitchen_queue] ([order_id], [token_number])
        VALUES (@OrderId, @TokenNumber);

        INSERT INTO [dbo].[payments] (
            [payment_number], [order_id], [payment_method], [amount], [payment_status], [created_by]
        )
        VALUES (
            CONCAT(N'PAY-', FORMAT(SYSDATETIME(), 'yyyyMMdd'), N'-', FORMAT(NEXT VALUE FOR [dbo].[seq_payment], '0000')),
            @OrderId, N'CASH', @Total, N'COMPLETED', @CreatedBy
        );

        EXEC [dbo].[usp_InsertAuditLog] @UserId = @CreatedBy, @Action = N'CASH_SALE',
            @TableName = N'orders', @RecordId = @OrderId, @Module = N'POS',
            @Description = CONCAT(N'Cash order ', @OrderNumber);

        COMMIT TRANSACTION;
        SELECT 1 AS [Success], N'Cash sale completed' AS [Message], @OrderNumber AS [order_number], @TokenNumber AS [token_number];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_SubmitEmployeeRequest
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_SubmitEmployeeRequest]
    @EmployeeId INT,
    @RequestType NVARCHAR(50),
    @DeliveryLocation NVARCHAR(300) = NULL,
    @RequiredByTime DATETIME2(7) = NULL,
    @MenuItemId INT,
    @Quantity INT,
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @ItemName NVARCHAR(300), @UnitPrice DECIMAL(18,2);
        SELECT @ItemName = [item_name], @UnitPrice = [unit_price]
        FROM [dbo].[menu_items] WHERE [id] = @MenuItemId AND [is_active] = 1;

        IF @ItemName IS NULL
            THROW 50014, 'Invalid menu item', 1;

        DECLARE @LineTotal DECIMAL(18,2) = @UnitPrice * @Quantity;
        DECLARE @RequestNumber NVARCHAR(50) = CONCAT(N'REQ-', FORMAT(SYSDATETIME(), 'yyyyMMdd'), N'-', FORMAT(NEXT VALUE FOR [dbo].[seq_order], '0000'));

        INSERT INTO [dbo].[employee_requests] (
            [request_number], [employee_id], [request_type], [delivery_location],
            [required_by_time], [total_amount], [created_by]
        )
        VALUES (
            @RequestNumber, @EmployeeId, @RequestType, @DeliveryLocation,
            @RequiredByTime, @LineTotal, @CreatedBy
        );

        DECLARE @RequestId INT = SCOPE_IDENTITY();

        INSERT INTO [dbo].[employee_request_items] (
            [request_id], [menu_item_id], [item_name], [quantity], [unit_price], [total_price]
        )
        VALUES (@RequestId, @MenuItemId, @ItemName, @Quantity, @UnitPrice, @LineTotal);

        INSERT INTO [dbo].[employee_request_approvals] ([request_id], [approval_level], [approver_id], [approval_status])
        SELECT @RequestId, 1, [id], N'PENDING'
        FROM [dbo].[users] u
        INNER JOIN [dbo].[user_roles] ur ON u.[id] = ur.[user_id]
        INNER JOIN [dbo].[roles] r ON ur.[role_id] = r.[id]
        WHERE r.[role_code] IN (N'MANAGER', N'ADMIN', N'SUPER_ADMIN')
          AND ur.[is_active] = 1 AND u.[is_active] = 1
          AND u.[is_deleted] = 0;

        COMMIT TRANSACTION;
        SELECT 1 AS [Success], N'Request submitted' AS [Message], @RequestNumber AS [request_number], @RequestId AS [request_id];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_ApproveEmployeeRequest
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ApproveEmployeeRequest]
    @RequestId INT,
    @ApproverId INT,
    @Approve BIT,  -- 1 = approve, 0 = reject
    @Comments NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF @Approve = 1
        BEGIN
            UPDATE [dbo].[employee_requests]
            SET [request_status] = N'APPROVED',
                [approved_by] = @ApproverId,
                [approved_at] = SYSDATETIME(),
                [updated_by] = @ApproverId,
                [updated_at] = SYSDATETIME()
            WHERE [id] = @RequestId AND [request_status] = N'PENDING';

            UPDATE [dbo].[employee_request_approvals]
            SET [approval_status] = N'APPROVED', [acted_at] = SYSDATETIME(), [comments] = @Comments
            WHERE [request_id] = @RequestId AND [approver_id] = @ApproverId;
        END
        ELSE
        BEGIN
            UPDATE [dbo].[employee_requests]
            SET [request_status] = N'REJECTED',
                [rejected_by] = @ApproverId,
                [rejected_at] = SYSDATETIME(),
                [rejection_reason] = @Comments,
                [updated_by] = @ApproverId,
                [updated_at] = SYSDATETIME()
            WHERE [id] = @RequestId AND [request_status] = N'PENDING';

            UPDATE [dbo].[employee_request_approvals]
            SET [approval_status] = N'REJECTED', [acted_at] = SYSDATETIME(), [comments] = @Comments
            WHERE [request_id] = @RequestId AND [approver_id] = @ApproverId;
        END

        EXEC [dbo].[usp_InsertAuditLog] @UserId = @ApproverId,
            @Action = CASE WHEN @Approve = 1 THEN N'REQUEST_APPROVED' ELSE N'REQUEST_REJECTED' END,
            @TableName = N'employee_requests', @RecordId = @RequestId, @Module = N'Requests';

        COMMIT TRANSACTION;
        SELECT 1 AS [Success], N'Request updated' AS [Message];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS [Success], ERROR_MESSAGE() AS [Message];
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_RunInventoryAlerts
-- Purpose: Low stock + expiry notifications
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_RunInventoryAlerts]
    @CreatedBy INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @LowStockThreshold INT = 5;
    DECLARE @ExpiryDays INT = 3;

    SELECT @LowStockThreshold = TRY_CAST([setting_value] AS INT)
    FROM [dbo].[system_settings] WHERE [setting_key] = N'LOW_STOCK_THRESHOLD';

    SELECT @ExpiryDays = TRY_CAST([setting_value] AS INT)
    FROM [dbo].[system_settings] WHERE [setting_key] = N'EXPIRY_ALERT_DAYS';

    -- Low stock: raw materials below minimum OR daily food remaining < threshold
    INSERT INTO [dbo].[notifications] (
        [notification_type], [title], [message], [reference_table], [reference_id], [priority], [created_by]
    )
    SELECT N'LOW_STOCK', N'Low Stock Alert',
           CONCAT(rm.[material_name], N' stock is low: ', rms.[current_quantity], N' ', rm.[unit_of_measure]),
           N'raw_materials', rm.[id], N'HIGH', @CreatedBy
    FROM [dbo].[raw_material_stock] rms
    INNER JOIN [dbo].[raw_materials] rm ON rms.[raw_material_id] = rm.[id]
    WHERE rms.[current_quantity] < ISNULL(rm.[minimum_stock_level], @LowStockThreshold)
      AND rm.[is_active] = 1 AND rm.[is_deleted] = 0
      AND NOT EXISTS (
          SELECT 1 FROM [dbo].[notifications] n
          WHERE n.[notification_type] = N'LOW_STOCK' AND n.[reference_id] = rm.[id]
            AND n.[is_read] = 0 AND CAST(n.[created_at] AS DATE) = CAST(SYSDATETIME() AS DATE)
      );

    -- Expiry within N days on purchase detail batches
    INSERT INTO [dbo].[notifications] (
        [notification_type], [title], [message], [reference_table], [reference_id], [priority], [created_by]
    )
    SELECT DISTINCT N'EXPIRY_ALERT', N'Expiry Alert',
           CONCAT(rm.[material_name], N' expires on ', CONVERT(NVARCHAR(10), spd.[expiry_date], 120)),
           N'raw_materials', rm.[id], N'MEDIUM', @CreatedBy
    FROM [dbo].[stock_purchase_details] spd
    INNER JOIN [dbo].[raw_materials] rm ON spd.[raw_material_id] = rm.[id]
    WHERE spd.[expiry_date] IS NOT NULL
      AND spd.[expiry_date] <= DATEADD(DAY, @ExpiryDays, CAST(SYSDATETIME() AS DATE))
      AND spd.[expiry_date] >= CAST(SYSDATETIME() AS DATE)
      AND NOT EXISTS (
          SELECT 1 FROM [dbo].[notifications] n
          WHERE n.[notification_type] = N'EXPIRY_ALERT' AND n.[reference_id] = rm.[id]
            AND n.[is_read] = 0 AND CAST(n.[created_at] AS DATE) = CAST(SYSDATETIME() AS DATE)
      );

    SELECT 1 AS [Success], N'Inventory alerts processed' AS [Message];
END;
GO

PRINT 'Stored Procedures Part 3 created successfully.';
GO
