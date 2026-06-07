-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — REPORTING VIEWS (Part 2)
-- ============================================================

USE [CanteenManagementDB];
GO

CREATE OR ALTER VIEW [dbo].[vw_MonthlySalesSummary]
AS
SELECT
    YEAR([order_date]) AS [sales_year],
    MONTH([order_date]) AS [sales_month],
    COUNT([id]) AS [total_orders],
    SUM([total_amount]) AS [total_revenue],
    SUM([advance_deducted]) AS [total_advance],
    SUM([credit_deducted]) AS [total_credit],
    SUM([cash_received]) AS [total_cash]
FROM [dbo].[orders]
WHERE [is_deleted] = 0 AND [order_status] <> N'CANCELLED'
GROUP BY YEAR([order_date]), MONTH([order_date]);
GO

CREATE OR ALTER VIEW [dbo].[vw_CreditUsage]
AS
SELECT
    e.[employee_code],
    e.[full_name],
    d.[department_name],
    eb.[credit_limit],
    eb.[credit_used],
    (eb.[credit_limit] - eb.[credit_used]) AS [available_credit],
    CASE WHEN eb.[credit_limit] > 0
         THEN CAST(eb.[credit_used] * 100.0 / eb.[credit_limit] AS DECIMAL(5,2))
         ELSE 0 END AS [usage_percent]
FROM [dbo].[employee_balances] eb
INNER JOIN [dbo].[employees] e ON eb.[employee_id] = e.[id]
INNER JOIN [dbo].[departments] d ON e.[department_id] = d.[id]
WHERE e.[is_deleted] = 0;
GO

CREATE OR ALTER VIEW [dbo].[vw_ExpiryAlerts]
AS
SELECT
    rm.[material_code],
    rm.[material_name],
    spd.[expiry_date],
    DATEDIFF(DAY, CAST(SYSDATETIME() AS DATE), spd.[expiry_date]) AS [days_until_expiry],
    spd.[quantity],
    rm.[unit_of_measure]
FROM [dbo].[stock_purchase_details] spd
INNER JOIN [dbo].[raw_materials] rm ON spd.[raw_material_id] = rm.[id]
WHERE spd.[expiry_date] IS NOT NULL
  AND spd.[expiry_date] <= DATEADD(DAY, 3, CAST(SYSDATETIME() AS DATE))
  AND spd.[expiry_date] >= CAST(SYSDATETIME() AS DATE)
  AND rm.[is_active] = 1;
GO

CREATE OR ALTER VIEW [dbo].[vw_DistributionPendingOrders]
AS
SELECT
    dq.[token_number],
    o.[order_number],
    o.[order_time],
    dq.[queue_status],
    dq.[counter_number],
    DATEDIFF(MINUTE, kq.[completed_at], SYSDATETIME()) AS [waiting_since_ready_min]
FROM [dbo].[distribution_queue] dq
INNER JOIN [dbo].[orders] o ON dq.[order_id] = o.[id]
LEFT JOIN [dbo].[kitchen_queue] kq ON kq.[order_id] = o.[id]
WHERE dq.[queue_status] IN (N'PENDING', N'CALLED')
  AND dq.[queue_date] = CAST(SYSDATETIME() AS DATE);
GO

CREATE OR ALTER VIEW [dbo].[vw_EmployeeTransactionHistory]
AS
SELECT
    ct.[transaction_number],
    ct.[transaction_date],
    ct.[transaction_type],
    e.[employee_code],
    e.[full_name],
    ct.[amount],
    ct.[advance_balance_before],
    ct.[advance_balance_after],
    ct.[credit_used_before],
    ct.[credit_used_after],
    ct.[order_id]
FROM [dbo].[card_transactions] ct
LEFT JOIN [dbo].[employees] e ON ct.[employee_id] = e.[id]
WHERE ct.[is_deleted] = 0;
GO

CREATE OR ALTER VIEW [dbo].[vw_WasteSummary]
AS
SELECT
    [waste_date],
    [waste_type],
    COUNT([id]) AS [waste_entries],
    SUM([quantity]) AS [total_quantity],
    SUM(ISNULL([estimated_cost], 0)) AS [total_estimated_cost]
FROM [dbo].[waste_records]
WHERE [is_deleted] = 0
GROUP BY [waste_date], [waste_type];
GO

CREATE OR ALTER VIEW [dbo].[vw_DepartmentWiseSales]
AS
SELECT
    d.[department_code],
    d.[department_name],
    COUNT(o.[id]) AS [order_count],
    SUM(o.[total_amount]) AS [total_sales]
FROM [dbo].[orders] o
INNER JOIN [dbo].[employees] e ON o.[employee_id] = e.[id]
INNER JOIN [dbo].[departments] d ON e.[department_id] = d.[id]
WHERE o.[order_type] = N'EMPLOYEE' AND o.[is_deleted] = 0
GROUP BY d.[department_code], d.[department_name];
GO

CREATE OR ALTER VIEW [dbo].[vw_UserActivityLogs]
AS
SELECT
    al.[id],
    al.[user_id],
    u.[username],
    u.[full_name],
    al.[activity_type] AS [action],
    al.[module],
    al.[page_url] AS [description],
    al.[ip_address],
    al.[created_at]
FROM [dbo].[activity_logs] al
LEFT JOIN [dbo].[users] u ON al.[user_id] = u.[id];
GO

CREATE OR ALTER VIEW [dbo].[vw_EmployeeRequestStatus]
AS
SELECT
    er.[request_number],
    er.[request_date],
    e.[employee_code],
    e.[full_name],
    er.[request_type],
    er.[request_status],
    er.[total_amount],
    er.[delivery_location],
    er.[required_by_time],
    er.[approved_at],
    er.[rejected_at]
FROM [dbo].[employee_requests] er
INNER JOIN [dbo].[employees] e ON er.[employee_id] = e.[id]
WHERE er.[is_deleted] = 0;
GO

PRINT 'Reporting Views Part 2 created successfully.';
GO
