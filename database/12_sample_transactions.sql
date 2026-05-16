-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — SAMPLE TRANSACTIONS
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Test queries and dummy transactions
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- 1. Test Balance Allocation
-- ============================================================
-- Allocate 1000 balance to employee ID 1
EXEC [dbo].[usp_AllocateBalance] 
    @EmployeeId = 1, 
    @Amount = 1000.00, 
    @AllocationType = 'ADVANCE_TOPUP', 
    @Remarks = 'Initial test top-up', 
    @CreatedBy = 1;

-- Allocate 500 balance to employee ID 2
EXEC [dbo].[usp_AllocateBalance] 
    @EmployeeId = 2, 
    @Amount = 500.00, 
    @AllocationType = 'ADVANCE_TOPUP', 
    @Remarks = 'Initial test top-up', 
    @CreatedBy = 1;

-- ============================================================
-- 2. Test POS Sale (Employee ID 1 buys something for 150)
-- ============================================================
-- Using the stored procedure created earlier
EXEC [dbo].[usp_ProcessEmployeeSale]
    @EmployeeCardNumber = 'RFID-0001-A1B2-C3D4',
    @MenuItemIds = '3',     -- Assuming Rice with Chicken
    @Quantities = '1',
    @CreatedBy = 4;         -- Cashier user ID

-- ============================================================
-- 3. Check Order and Queue Status
-- ============================================================
SELECT * FROM [dbo].[orders] ORDER BY id DESC;
SELECT * FROM [dbo].[kitchen_queue] ORDER BY id DESC;
SELECT * FROM [dbo].[distribution_queue] ORDER BY id DESC;

-- ============================================================
-- 4. Check Updated Balance
-- ============================================================
SELECT * FROM [dbo].[vw_EmployeeBalanceStatus] WHERE employee_code = 'EMP001';

-- ============================================================
-- 5. Test Kitchen Updating Status
-- ============================================================
-- Simulate kitchen staff taking the order
UPDATE [dbo].[kitchen_queue]
SET queue_status = 'IN_PROGRESS', started_at = SYSDATETIME(), assigned_to = 5
WHERE token_number = 1 AND queue_date = CAST(SYSDATETIME() AS DATE);

UPDATE [dbo].[orders] SET kitchen_status = 'IN_PROGRESS' WHERE token_number = 1;

-- Simulate kitchen staff finishing the order
UPDATE [dbo].[kitchen_queue]
SET queue_status = 'READY', completed_at = SYSDATETIME()
WHERE token_number = 1 AND queue_date = CAST(SYSDATETIME() AS DATE);

UPDATE [dbo].[orders] SET kitchen_status = 'READY', distribution_status = 'READY_FOR_PICKUP' WHERE token_number = 1;

-- ============================================================
-- 6. Check Views
-- ============================================================
SELECT * FROM [dbo].[vw_DailySalesSummary];
SELECT * FROM [dbo].[vw_LowStockAlerts];

PRINT 'Sample transactions completed.';
GO
