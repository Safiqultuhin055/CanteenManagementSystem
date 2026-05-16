-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — MASTER EXECUTION SCRIPT
-- Run scripts in this exact order on SQL Server 2019+
-- ============================================================

:r 01_create_database.sql
:r 02_security_users_tables.sql
:r 03_employee_tables.sql
:r 04_food_inventory_tables.sql
:r 05_balance_credit_tables.sql
:r 06_sales_pos_tables.sql
:r 06b_employee_request_tables.sql
:r 07_system_monitoring_tables.sql
:r 08_indexes.sql
:r 09_seed_data.sql
:r 13_menu_permissions_and_help.sql
:r Speed_data.sql
:r 10_stored_procedures_part1.sql
:r 10_stored_procedures_part2.sql
:r 10_stored_procedures_part3.sql
:r 11_views.sql
:r 11_views_part2.sql
:r 12_sample_transactions.sql

-- Note: :r requires SQLCMD mode in SSMS
-- Alternative: execute each file manually in the order above
