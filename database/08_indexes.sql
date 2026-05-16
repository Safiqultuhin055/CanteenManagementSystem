-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — PERFORMANCE INDEXES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Non-clustered indexes for optimized queries
--                   Covering indexes for Django ORM performance
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- SECURITY & USERS INDEXES
-- ============================================================

-- Fast user lookup by username (login)
CREATE NONCLUSTERED INDEX [IX_users_username_active]
    ON [dbo].[users] ([username], [is_active], [is_deleted])
    INCLUDE ([password_hash], [full_name], [employee_id]);
GO

-- User email lookup
CREATE NONCLUSTERED INDEX [IX_users_email]
    ON [dbo].[users] ([email])
    WHERE [email] IS NOT NULL AND [is_deleted] = 0;
GO

-- Active sessions lookup
CREATE NONCLUSTERED INDEX [IX_user_sessions_active]
    ON [dbo].[user_sessions] ([user_id], [is_active])
    INCLUDE ([session_key], [last_activity]);
GO

-- Login history by user and date
CREATE NONCLUSTERED INDEX [IX_login_history_user_date]
    ON [dbo].[login_history] ([user_id], [login_at] DESC)
    INCLUDE ([login_status], [ip_address]);
GO

-- Login history by date (reporting)
CREATE NONCLUSTERED INDEX [IX_login_history_date]
    ON [dbo].[login_history] ([login_at] DESC)
    INCLUDE ([user_id], [username], [login_status]);
GO

-- Role permissions lookup
CREATE NONCLUSTERED INDEX [IX_role_permissions_role]
    ON [dbo].[role_permissions] ([role_id], [is_active])
    INCLUDE ([permission_id]);
GO

-- User roles lookup
CREATE NONCLUSTERED INDEX [IX_user_roles_user]
    ON [dbo].[user_roles] ([user_id], [is_active])
    INCLUDE ([role_id]);
GO

-- Password history by user
CREATE NONCLUSTERED INDEX [IX_password_history_user]
    ON [dbo].[password_history] ([user_id], [changed_at] DESC);
GO

-- ============================================================
-- EMPLOYEE MANAGEMENT INDEXES
-- ============================================================

-- Employee lookup by code
CREATE NONCLUSTERED INDEX [IX_employees_code]
    ON [dbo].[employees] ([employee_code])
    WHERE [is_deleted] = 0;
GO

-- Employees by department
CREATE NONCLUSTERED INDEX [IX_employees_department]
    ON [dbo].[employees] ([department_id], [is_active])
    INCLUDE ([employee_code], [full_name]);
GO

-- Active employees search
CREATE NONCLUSTERED INDEX [IX_employees_active]
    ON [dbo].[employees] ([is_active], [is_deleted])
    INCLUDE ([employee_code], [full_name], [department_id]);
GO

-- Card lookup by number (RFID scan)
CREATE NONCLUSTERED INDEX [IX_employee_cards_number]
    ON [dbo].[employee_cards] ([card_number], [card_status])
    INCLUDE ([employee_id], [card_type]);
GO

-- Active cards by employee
CREATE NONCLUSTERED INDEX [IX_employee_cards_employee_active]
    ON [dbo].[employee_cards] ([employee_id], [is_active])
    WHERE [card_status] = 'ACTIVE' AND [is_deleted] = 0;
GO

-- ============================================================
-- FOOD & INVENTORY INDEXES
-- ============================================================

-- Menu items by category
CREATE NONCLUSTERED INDEX [IX_menu_items_category]
    ON [dbo].[menu_items] ([category_id], [is_available], [is_active])
    INCLUDE ([item_name], [unit_price], [item_code]);
GO

-- Menu items barcode lookup
CREATE NONCLUSTERED INDEX [IX_menu_items_barcode]
    ON [dbo].[menu_items] ([barcode])
    WHERE [barcode] IS NOT NULL AND [is_deleted] = 0;
GO

-- Daily food stock by date
CREATE NONCLUSTERED INDEX [IX_daily_food_stock_date]
    ON [dbo].[daily_food_stock] ([stock_date], [is_available])
    INCLUDE ([menu_item_id], [prepared_quantity], [sold_quantity], [unit_price]);
GO

-- Daily food stock - available items for POS
CREATE NONCLUSTERED INDEX [IX_daily_food_stock_available]
    ON [dbo].[daily_food_stock] ([stock_date], [menu_item_id], [is_available])
    INCLUDE ([prepared_quantity], [sold_quantity], [waste_quantity], [unit_price])
    WHERE [is_deleted] = 0;
GO

-- Raw material stock levels (low stock alerts)
CREATE NONCLUSTERED INDEX [IX_raw_material_stock_levels]
    ON [dbo].[raw_material_stock] ([current_quantity])
    INCLUDE ([raw_material_id], [expiry_date]);
GO

-- Stock purchases by date
CREATE NONCLUSTERED INDEX [IX_stock_purchases_date]
    ON [dbo].[stock_purchases] ([purchase_date] DESC, [purchase_status])
    INCLUDE ([supplier_id], [net_amount]);
GO

-- Stock purchases by supplier
CREATE NONCLUSTERED INDEX [IX_stock_purchases_supplier]
    ON [dbo].[stock_purchases] ([supplier_id], [purchase_date] DESC)
    WHERE [is_deleted] = 0;
GO

-- Waste records by date
CREATE NONCLUSTERED INDEX [IX_waste_records_date]
    ON [dbo].[waste_records] ([waste_date] DESC, [waste_type])
    INCLUDE ([menu_item_id], [raw_material_id], [quantity], [estimated_cost]);
GO

-- ============================================================
-- BALANCE & CREDIT INDEXES
-- ============================================================

-- Employee balance lookup
CREATE NONCLUSTERED INDEX [IX_employee_balances_employee]
    ON [dbo].[employee_balances] ([employee_id])
    INCLUDE ([advance_balance], [credit_limit], [credit_used]);
GO

-- Balance allocations by employee and date
CREATE NONCLUSTERED INDEX [IX_balance_allocations_employee_date]
    ON [dbo].[balance_allocations] ([employee_id], [allocation_date] DESC)
    INCLUDE ([allocation_type], [amount]);
GO

-- Monthly allowances lookup
CREATE NONCLUSTERED INDEX [IX_monthly_allowances_period]
    ON [dbo].[monthly_allowances] ([allowance_year], [allowance_month], [allocation_status])
    INCLUDE ([department_id], [total_amount]);
GO

-- Card transactions by employee
CREATE NONCLUSTERED INDEX [IX_card_transactions_employee]
    ON [dbo].[card_transactions] ([employee_id], [transaction_date] DESC)
    INCLUDE ([transaction_type], [amount]);
GO

-- Card transactions by date (reporting)
CREATE NONCLUSTERED INDEX [IX_card_transactions_date]
    ON [dbo].[card_transactions] ([transaction_date] DESC)
    INCLUDE ([employee_id], [transaction_type], [amount]);
GO

-- Credit limits by employee
CREATE NONCLUSTERED INDEX [IX_credit_limits_employee]
    ON [dbo].[credit_limits] ([employee_id], [is_active])
    WHERE [approval_status] = 'APPROVED' AND [is_deleted] = 0;
GO

-- ============================================================
-- SALES & POS INDEXES
-- ============================================================

-- Orders by date (daily reporting)
CREATE NONCLUSTERED INDEX [IX_orders_date]
    ON [dbo].[orders] ([order_date] DESC, [order_status])
    INCLUDE ([order_number], [token_number], [total_amount], [order_type]);
GO

-- Orders by employee
CREATE NONCLUSTERED INDEX [IX_orders_employee]
    ON [dbo].[orders] ([employee_id], [order_date] DESC)
    INCLUDE ([order_number], [total_amount], [order_status])
    WHERE [is_deleted] = 0;
GO

-- Orders by token number (kitchen/distribution display)
CREATE NONCLUSTERED INDEX [IX_orders_token_date]
    ON [dbo].[orders] ([order_date], [token_number])
    INCLUDE ([order_status], [kitchen_status], [distribution_status]);
GO

-- Kitchen status lookup (pending orders)
CREATE NONCLUSTERED INDEX [IX_orders_kitchen_status]
    ON [dbo].[orders] ([kitchen_status], [order_date])
    INCLUDE ([token_number], [order_number])
    WHERE [is_deleted] = 0 AND [order_status] <> 'CANCELLED';
GO

-- Order details by order
CREATE NONCLUSTERED INDEX [IX_order_details_order]
    ON [dbo].[order_details] ([order_id])
    INCLUDE ([menu_item_id], [quantity], [total_price], [item_status]);
GO

-- Guest cards active lookup
CREATE NONCLUSTERED INDEX [IX_guest_cards_active]
    ON [dbo].[guest_cards] ([card_number], [card_status])
    INCLUDE ([guest_name], [remaining_balance])
    WHERE [is_deleted] = 0;
GO

-- Kitchen queue by date and status
CREATE NONCLUSTERED INDEX [IX_kitchen_queue_date_status]
    ON [dbo].[kitchen_queue] ([queue_date], [queue_status])
    INCLUDE ([order_id], [token_number], [priority]);
GO

-- Distribution queue by date and status
CREATE NONCLUSTERED INDEX [IX_distribution_queue_date_status]
    ON [dbo].[distribution_queue] ([queue_date], [queue_status])
    INCLUDE ([order_id], [token_number]);
GO

-- Payments by order
CREATE NONCLUSTERED INDEX [IX_payments_order]
    ON [dbo].[payments] ([order_id])
    INCLUDE ([payment_method], [amount], [payment_status]);
GO

-- ============================================================
-- SYSTEM & MONITORING INDEXES
-- ============================================================

-- Audit logs by date (recent first)
CREATE NONCLUSTERED INDEX [IX_audit_logs_date]
    ON [dbo].[audit_logs] ([created_at] DESC)
    INCLUDE ([user_id], [action], [table_name], [module]);
GO

-- Audit logs by user
CREATE NONCLUSTERED INDEX [IX_audit_logs_user]
    ON [dbo].[audit_logs] ([user_id], [created_at] DESC)
    INCLUDE ([action], [table_name]);
GO

-- Audit logs by table/action
CREATE NONCLUSTERED INDEX [IX_audit_logs_table_action]
    ON [dbo].[audit_logs] ([table_name], [action], [created_at] DESC)
    INCLUDE ([user_id], [record_id]);
GO

-- Activity logs by date
CREATE NONCLUSTERED INDEX [IX_activity_logs_date]
    ON [dbo].[activity_logs] ([created_at] DESC)
    INCLUDE ([user_id], [activity_type], [module]);
GO

-- Activity logs by user
CREATE NONCLUSTERED INDEX [IX_activity_logs_user]
    ON [dbo].[activity_logs] ([user_id], [created_at] DESC)
    INCLUDE ([activity_type], [page_url]);
GO

-- Notifications unread by user
CREATE NONCLUSTERED INDEX [IX_notifications_user_unread]
    ON [dbo].[notifications] ([target_user_id], [is_read], [is_active])
    INCLUDE ([notification_type], [title], [severity], [created_at])
    WHERE [is_deleted] = 0;
GO

-- Notifications by type (alert monitoring)
CREATE NONCLUSTERED INDEX [IX_notifications_type]
    ON [dbo].[notifications] ([notification_type], [created_at] DESC)
    WHERE [is_active] = 1 AND [is_deleted] = 0;
GO

PRINT '=====================================================';
PRINT 'All performance indexes created successfully.';
PRINT '=====================================================';
GO
