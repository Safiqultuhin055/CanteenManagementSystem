-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — REPORTING VIEWS
-- Database Engine : Microsoft SQL Server 2019+
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- VIEW: vw_DailySalesSummary
-- ============================================================
CREATE OR ALTER VIEW [dbo].[vw_DailySalesSummary]
AS
SELECT 
    order_date,
    COUNT(id) AS total_orders,
    SUM(CASE WHEN order_type = 'EMPLOYEE' THEN 1 ELSE 0 END) AS employee_orders,
    SUM(CASE WHEN order_type = 'GUEST' THEN 1 ELSE 0 END) AS guest_orders,
    SUM(CASE WHEN order_type = 'CASH' THEN 1 ELSE 0 END) AS cash_orders,
    SUM(total_amount) AS total_revenue,
    SUM(advance_deducted) AS total_advance_deducted,
    SUM(credit_deducted) AS total_credit_deducted,
    SUM(cash_received) AS total_cash_received
FROM [dbo].[orders]
WHERE order_status != 'CANCELLED' AND is_deleted = 0
GROUP BY order_date;
GO

-- ============================================================
-- VIEW: vw_EmployeeBalanceStatus
-- ============================================================
CREATE OR ALTER VIEW [dbo].[vw_EmployeeBalanceStatus]
AS
SELECT 
    e.employee_code,
    e.full_name,
    d.department_name,
    eb.advance_balance,
    eb.credit_limit,
    eb.credit_used,
    (eb.credit_limit - eb.credit_used) AS available_credit,
    (eb.advance_balance + (eb.credit_limit - eb.credit_used)) AS total_purchasing_power,
    eb.total_spent,
    eb.last_transaction_at
FROM [dbo].[employee_balances] eb
JOIN [dbo].[employees] e ON eb.employee_id = e.id
JOIN [dbo].[departments] d ON e.department_id = d.id
WHERE e.is_active = 1 AND e.is_deleted = 0;
GO

-- ============================================================
-- VIEW: vw_LowStockAlerts
-- ============================================================
CREATE OR ALTER VIEW [dbo].[vw_LowStockAlerts]
AS
SELECT 
    rm.material_code,
    rm.material_name,
    rm.category,
    s.supplier_name,
    rms.current_quantity,
    rm.minimum_stock_level,
    rm.unit_of_measure,
    (rm.minimum_stock_level - rms.current_quantity) AS deficit
FROM [dbo].[raw_material_stock] rms
JOIN [dbo].[raw_materials] rm ON rms.raw_material_id = rm.id
LEFT JOIN [dbo].[suppliers] s ON rm.default_supplier_id = s.id
WHERE rms.current_quantity <= rm.minimum_stock_level
AND rm.is_active = 1 AND rm.is_deleted = 0;
GO

-- ============================================================
-- VIEW: vw_KitchenPendingOrders
-- ============================================================
CREATE OR ALTER VIEW [dbo].[vw_KitchenPendingOrders]
AS
SELECT 
    kq.token_number,
    o.order_number,
    o.order_time,
    kq.queue_status,
    kq.priority,
    o.order_type,
    DATEDIFF(MINUTE, o.order_time, SYSDATETIME()) AS wait_time_minutes
FROM [dbo].[kitchen_queue] kq
JOIN [dbo].[orders] o ON kq.order_id = o.id
WHERE kq.queue_status IN ('PENDING', 'IN_PROGRESS')
AND o.order_date = CAST(SYSDATETIME() AS DATE);
GO

-- ============================================================
-- VIEW: vw_TopSellingItems
-- ============================================================
CREATE OR ALTER VIEW [dbo].[vw_TopSellingItems]
AS
SELECT TOP 100
    mi.item_code,
    mi.item_name,
    fc.category_name,
    COUNT(od.id) AS times_ordered,
    SUM(od.quantity) AS total_quantity_sold,
    SUM(od.total_price) AS total_revenue
FROM [dbo].[order_details] od
JOIN [dbo].[menu_items] mi ON od.menu_item_id = mi.id
JOIN [dbo].[food_categories] fc ON mi.category_id = fc.id
JOIN [dbo].[orders] o ON od.order_id = o.id
WHERE o.order_status != 'CANCELLED'
GROUP BY mi.item_code, mi.item_name, fc.category_name
ORDER BY total_quantity_sold DESC;
GO

PRINT 'Reporting Views created successfully.';
GO
