-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — SEED / MASTER DATA
-- Database Engine : Microsoft SQL Server 2019+
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- 1. ROLES (6 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[roles] ON;
INSERT INTO [dbo].[roles] ([id],[role_name],[role_code],[description],[priority],[is_active])
VALUES
(1, N'Super Administrator', N'SUPER_ADMIN', N'Full system access', 0, 1),
(2, N'Administrator',       N'ADMIN',       N'Administrative access', 1, 1),
(3, N'Manager',             N'MANAGER',     N'Management access', 2, 1),
(4, N'Cashier',             N'CASHIER',     N'POS and billing access', 3, 1),
(5, N'Kitchen Staff',       N'KITCHEN',     N'Kitchen display and processing', 4, 1),
(6, N'Distribution Staff',  N'DISTRIBUTION',N'Distribution counter access', 5, 1);
SET IDENTITY_INSERT [dbo].[roles] OFF;
GO

-- ============================================================
-- 2. PERMISSIONS (30 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[permissions] ON;
INSERT INTO [dbo].[permissions] ([id],[permission_name],[permission_code],[module])
VALUES
(1,  N'View Dashboard',        N'DASHBOARD_VIEW',      N'Dashboard'),
(2,  N'Manage Users',          N'USER_MANAGE',          N'Users'),
(3,  N'Create User',           N'USER_CREATE',          N'Users'),
(4,  N'Edit User',             N'USER_EDIT',            N'Users'),
(5,  N'Delete User',           N'USER_DELETE',          N'Users'),
(6,  N'View Employees',        N'EMPLOYEE_VIEW',        N'Employees'),
(7,  N'Manage Employees',      N'EMPLOYEE_MANAGE',      N'Employees'),
(8,  N'View Orders',           N'ORDER_VIEW',           N'Orders'),
(9,  N'Create Order',          N'ORDER_CREATE',         N'Orders'),
(10, N'Cancel Order',          N'ORDER_CANCEL',         N'Orders'),
(11, N'View Inventory',        N'INVENTORY_VIEW',       N'Inventory'),
(12, N'Manage Inventory',      N'INVENTORY_MANAGE',     N'Inventory'),
(13, N'View Balance',          N'BALANCE_VIEW',         N'Balance'),
(14, N'Allocate Balance',      N'BALANCE_ALLOCATE',     N'Balance'),
(15, N'Manage Credit',         N'CREDIT_MANAGE',        N'Balance'),
(16, N'View Reports',          N'REPORT_VIEW',          N'Reports'),
(17, N'Export Reports',        N'REPORT_EXPORT',        N'Reports'),
(18, N'View Kitchen Queue',    N'KITCHEN_VIEW',         N'Kitchen'),
(19, N'Update Kitchen Status', N'KITCHEN_UPDATE',       N'Kitchen'),
(20, N'View Distribution',     N'DISTRIBUTION_VIEW',    N'Distribution'),
(21, N'Update Distribution',   N'DISTRIBUTION_UPDATE',  N'Distribution'),
(22, N'Manage Cards',          N'CARD_MANAGE',          N'Cards'),
(23, N'Manage Guest Cards',    N'GUEST_CARD_MANAGE',    N'Cards'),
(24, N'View Audit Logs',       N'AUDIT_VIEW',           N'System'),
(25, N'Manage Settings',       N'SETTINGS_MANAGE',      N'System'),
(26, N'Manage Roles',          N'ROLE_MANAGE',          N'Security'),
(27, N'Manage Permissions',    N'PERMISSION_MANAGE',    N'Security'),
(28, N'Manage Departments',    N'DEPARTMENT_MANAGE',    N'Organization'),
(29, N'Manage Suppliers',      N'SUPPLIER_MANAGE',      N'Inventory'),
(30, N'Manage Menu Items',     N'MENU_ITEM_MANAGE',     N'Inventory');
SET IDENTITY_INSERT [dbo].[permissions] OFF;
GO

-- ============================================================
-- 3. ROLE_PERMISSIONS (Admin gets all, others get subset)
-- ============================================================
-- Super Admin gets all permissions
INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active],[created_by])
SELECT 1, [id], 1, NULL FROM [dbo].[permissions];
GO

-- Admin gets all except PERMISSION_MANAGE
INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active],[created_by])
SELECT 2, [id], 1, NULL FROM [dbo].[permissions] WHERE [permission_code] != 'PERMISSION_MANAGE';
GO

-- Cashier permissions
INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active],[created_by])
SELECT 4, [id], 1, NULL FROM [dbo].[permissions]
WHERE [permission_code] IN ('DASHBOARD_VIEW','ORDER_VIEW','ORDER_CREATE','BALANCE_VIEW','GUEST_CARD_MANAGE','KITCHEN_VIEW');
GO

-- Kitchen permissions
INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active],[created_by])
SELECT 5, [id], 1, NULL FROM [dbo].[permissions]
WHERE [permission_code] IN ('DASHBOARD_VIEW','KITCHEN_VIEW','KITCHEN_UPDATE','ORDER_VIEW');
GO

-- Distribution permissions
INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active],[created_by])
SELECT 6, [id], 1, NULL FROM [dbo].[permissions]
WHERE [permission_code] IN ('DASHBOARD_VIEW','DISTRIBUTION_VIEW','DISTRIBUTION_UPDATE','ORDER_VIEW');
GO

-- ============================================================
-- 4. MENUS (Navigation structure)
-- ============================================================
SET IDENTITY_INSERT [dbo].[menus] ON;
INSERT INTO [dbo].[menus] ([id],[menu_name],[menu_code],[parent_id],[url],[icon_class],[display_order],[menu_level])
VALUES
(1,  N'Dashboard',        N'DASHBOARD',     NULL, N'/dashboard/',         N'bi-speedometer2',   1, 0),
(2,  N'POS',              N'POS',           NULL, N'/pos/',               N'bi-cart3',           2, 0),
(3,  N'Orders',           N'ORDERS',        NULL, NULL,                   N'bi-receipt',         3, 0),
(4,  N'Order List',       N'ORDER_LIST',    3,    N'/orders/',                    N'bi-list-ul',         1, 1),
(5,  N'Kitchen Display',  N'KITCHEN',       3,    N'/kitchen/',                   N'bi-fire',            2, 1),
(6,  N'Distribution',     N'DISTRIBUTION',  3,    N'/distribution/',              N'bi-box-seam',        3, 1),
(7,  N'Token Display',    N'TOKEN_DISPLAY', 3,    N'/distribution/display/',      N'bi-ticket',          4, 1),
(8,  N'Employees',        N'EMPLOYEES',     NULL, NULL,                           N'bi-people',          4, 0),
(9,  N'Employee List',    N'EMP_LIST',      8,    N'/employees/',                 N'bi-person-lines-fill',1, 1),
(10, N'Cards',            N'CARDS',         8,    N'/cards/',                     N'bi-credit-card',     2, 1),
(11, N'Balance',          N'BALANCE',       8,    N'/balance/',                   N'bi-wallet2',         3, 1),
(12, N'Inventory',        N'INVENTORY',     NULL, NULL,                           N'bi-box',             5, 0),
(13, N'Menu Items',       N'MENU_ITEMS',    12,   N'/menu-items/',                N'bi-cup-hot',         1, 1),
(14, N'Food Categories',  N'CATEGORIES',    12,   N'/categories/',                N'bi-tags',            2, 1),
(15, N'Daily Stock',      N'DAILY_STOCK',   12,   N'/daily-stock/',               N'bi-calendar-day',    3, 1),
(16, N'Raw Materials',    N'RAW_MATERIALS', 12,   N'/raw-materials/',             N'bi-basket',          4, 1),
(17, N'Purchases',        N'PURCHASES',     12,   N'/purchases/',                 N'bi-truck',           5, 1),
(18, N'Waste Management', N'WASTE',         12,   N'/waste/',                     N'bi-trash',           6, 1),
(19, N'Suppliers',        N'SUPPLIERS',     12,   N'/suppliers/',                 N'bi-shop',            7, 1),
(20, N'Reports',          N'REPORTS',       NULL, N'/reports/',                   N'bi-graph-up',        6, 0),
(21, N'Administration',   N'ADMIN',         NULL, NULL,                           N'bi-gear',            7, 0),
(22, N'Users',            N'USERS',         21,   N'/users/',                     N'bi-person-gear',     1, 1),
(23, N'Roles',            N'ROLES',         21,   N'/roles/',                     N'bi-shield-lock',     2, 1),
(24, N'Departments',      N'DEPARTMENTS',   21,   N'/departments/',               N'bi-building',        3, 1),
(25, N'Settings',         N'SETTINGS',      21,   N'/settings/',                  N'bi-sliders',         4, 1),
(26, N'Audit Logs',       N'AUDIT_LOGS',    21,   N'/audit-logs/',                N'bi-journal-text',    5, 1),
(27, N'Guest Cards',      N'GUEST_CARDS',   NULL, N'/guest-cards/',               N'bi-person-badge',    8, 0);
SET IDENTITY_INSERT [dbo].[menus] OFF;
GO

-- ============================================================
-- 5. DEPARTMENTS (10 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[departments] ON;
INSERT INTO [dbo].[departments] ([id],[department_name],[department_code],[description])
VALUES
(1,  N'Administration',   N'ADMIN',  N'Administrative department'),
(2,  N'Human Resources',  N'HR',     N'HR and recruitment'),
(3,  N'Finance',          N'FIN',    N'Finance and accounting'),
(4,  N'Information Technology', N'IT', N'IT and systems'),
(5,  N'Operations',       N'OPS',    N'Operations management'),
(6,  N'Sales',            N'SALES',  N'Sales department'),
(7,  N'Marketing',        N'MKT',    N'Marketing and communications'),
(8,  N'Engineering',      N'ENG',    N'Engineering department'),
(9,  N'Quality Assurance',N'QA',     N'Quality control'),
(10, N'Logistics',        N'LOG',    N'Supply chain and logistics');
SET IDENTITY_INSERT [dbo].[departments] OFF;
GO

-- ============================================================
-- 6. EMPLOYEES (12 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[employees] ON;
INSERT INTO [dbo].[employees] ([id],[employee_code],[first_name],[last_name],[full_name],[email],[phone],[department_id],[designation],[employee_type])
VALUES
(1,  N'EMP001', N'MD',      N'SAFIQUL ISLAM', N'MD SAFIQUL ISLAM',    N'safiqul@company.com',  N'+8801711000001', 1, N'System Admin',     N'PERMANENT'),
(2,  N'EMP002', N'Ahmed',   N'Rahman',        N'Ahmed Rahman',        N'ahmed@company.com',    N'+8801711000002', 2, N'HR Manager',       N'PERMANENT'),
(3,  N'EMP003', N'Fatima',  N'Begum',         N'Fatima Begum',        N'fatima@company.com',   N'+8801711000003', 3, N'Finance Officer',  N'PERMANENT'),
(4,  N'EMP004', N'Karim',   N'Hossain',       N'Karim Hossain',       N'karim@company.com',    N'+8801711000004', 4, N'IT Manager',       N'PERMANENT'),
(5,  N'EMP005', N'Nasreen',  N'Akter',        N'Nasreen Akter',       N'nasreen@company.com',  N'+8801711000005', 5, N'Operations Lead',  N'PERMANENT'),
(6,  N'EMP006', N'Rahim',   N'Uddin',         N'Rahim Uddin',         N'rahim@company.com',    N'+8801711000006', 6, N'Sales Executive',  N'PERMANENT'),
(7,  N'EMP007', N'Sumaiya', N'Khan',          N'Sumaiya Khan',        N'sumaiya@company.com',  N'+8801711000007', 7, N'Marketing Head',   N'PERMANENT'),
(8,  N'EMP008', N'Tanvir',  N'Ahmed',         N'Tanvir Ahmed',        N'tanvir@company.com',   N'+8801711000008', 8, N'Senior Engineer',  N'PERMANENT'),
(9,  N'EMP009', N'Ritu',    N'Das',           N'Ritu Das',            N'ritu@company.com',     N'+8801711000009', 9, N'QA Analyst',       N'PERMANENT'),
(10, N'EMP010', N'Jamal',   N'Hasan',         N'Jamal Hasan',         N'jamal@company.com',    N'+8801711000010', 10,N'Logistics Officer',N'PERMANENT'),
(11, N'EMP011', N'Shanta',  N'Roy',           N'Shanta Roy',          N'shanta@company.com',   N'+8801711000011', 4, N'Developer',        N'CONTRACT'),
(12, N'EMP012', N'Farhan',  N'Ali',           N'Farhan Ali',          N'farhan@company.com',   N'+8801711000012', 8, N'Junior Engineer',  N'INTERN');
SET IDENTITY_INSERT [dbo].[employees] OFF;
GO

-- ============================================================
-- 7. USERS (Default admin + sample users)
-- All users are created with the raw password: Admin@123
-- password_hash = Django pbkdf2_sha256 hash for 'Admin@123'
-- ============================================================
DECLARE @default_hash NVARCHAR(256) = N'pbkdf2_sha256$1200000$fpWAI0lfnTVF4tCHSiYeO3$y6K8aQtZOnDKmWgywG/WHt0k7EIDyYKux3IkR+Ek888=';

SET IDENTITY_INSERT [dbo].[users] ON;
INSERT INTO [dbo].[users] ([id],[username],[email],[password_hash],[first_name],[last_name],[full_name],[employee_id],[is_superuser],[is_staff],[must_change_password])
VALUES
(1, N'superadmin',      N'superadmin@company.com',  @default_hash, N'Super',    N'Admin',    N'Super Admin',       NULL, 1, 1, 1),
(2, N'shafiqultuhin',   N'safiqul@company.com',     @default_hash, N'MD',       N'SAFIQUL',  N'MD SAFIQUL ISLAM',  1,    1, 1, 1),
(3, N'ahmed.rahman',    N'ahmed@company.com',        @default_hash, N'Ahmed',    N'Rahman',   N'Ahmed Rahman',      2,    0, 1, 1),
(4, N'cashier1',        N'cashier1@company.com',     @default_hash, N'Cashier',  N'One',      N'Cashier One',       NULL, 0, 1, 1),
(5, N'kitchen1',        N'kitchen1@company.com',     @default_hash, N'Kitchen',  N'Staff',    N'Kitchen Staff One', NULL, 0, 1, 1);
SET IDENTITY_INSERT [dbo].[users] OFF;
GO

-- ============================================================
-- 8. USER_ROLES
-- ============================================================
INSERT INTO [dbo].[user_roles] ([user_id],[role_id],[created_by])
VALUES (1,1,NULL),(2,2,1),(3,3,1),(4,4,1),(5,5,1);
GO

-- ============================================================
-- 9. EMPLOYEE CARDS (10 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[employee_cards] ON;
INSERT INTO [dbo].[employee_cards] ([id],[employee_id],[card_number],[card_type],[card_status])
VALUES
(1,  1, N'RFID-0001-A1B2-C3D4', N'RFID', N'ACTIVE'),
(2,  2, N'RFID-0002-E5F6-G7H8', N'RFID', N'ACTIVE'),
(3,  3, N'RFID-0003-I9J0-K1L2', N'RFID', N'ACTIVE'),
(4,  4, N'RFID-0004-M3N4-O5P6', N'RFID', N'ACTIVE'),
(5,  5, N'RFID-0005-Q7R8-S9T0', N'RFID', N'ACTIVE'),
(6,  6, N'RFID-0006-U1V2-W3X4', N'RFID', N'ACTIVE'),
(7,  7, N'RFID-0007-Y5Z6-A7B8', N'RFID', N'ACTIVE'),
(8,  8, N'RFID-0008-C9D0-E1F2', N'RFID', N'ACTIVE'),
(9,  9, N'RFID-0009-G3H4-I5J6', N'RFID', N'ACTIVE'),
(10, 10,N'RFID-0010-K7L8-M9N0', N'RFID', N'ACTIVE');
SET IDENTITY_INSERT [dbo].[employee_cards] OFF;
GO

-- ============================================================
-- 10. FOOD CATEGORIES (8 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[food_categories] ON;
INSERT INTO [dbo].[food_categories] ([id],[category_name],[category_code],[display_order])
VALUES
(1, N'Breakfast',    N'BRK', 1),
(2, N'Lunch',        N'LUN', 2),
(3, N'Dinner',       N'DIN', 3),
(4, N'Snacks',       N'SNK', 4),
(5, N'Beverages',    N'BEV', 5),
(6, N'Desserts',     N'DES', 6),
(7, N'Special Menu', N'SPL', 7),
(8, N'Combo Meals',  N'CMB', 8);
SET IDENTITY_INSERT [dbo].[food_categories] OFF;
GO

-- ============================================================
-- 11. MENU ITEMS (15 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[menu_items] ON;
INSERT INTO [dbo].[menu_items] ([id],[item_name],[item_code],[category_id],[unit_price],[cost_price],[unit_of_measure],[is_vegetarian])
VALUES
(1,  N'Paratha with Egg',     N'BRK001', 1, 50.00,  30.00, N'Plate', 0),
(2,  N'Toast with Butter',    N'BRK002', 1, 30.00,  15.00, N'Plate', 1),
(3,  N'Rice with Chicken',    N'LUN001', 2, 120.00, 70.00, N'Plate', 0),
(4,  N'Rice with Fish',       N'LUN002', 2, 100.00, 60.00, N'Plate', 0),
(5,  N'Vegetable Rice',       N'LUN003', 2, 80.00,  40.00, N'Plate', 1),
(6,  N'Chicken Biryani',      N'LUN004', 2, 150.00, 90.00, N'Plate', 0),
(7,  N'Beef Curry Rice',      N'DIN001', 3, 130.00, 75.00, N'Plate', 0),
(8,  N'Samosa',               N'SNK001', 4, 20.00,  10.00, N'Piece', 1),
(9,  N'Chicken Roll',         N'SNK002', 4, 40.00,  25.00, N'Piece', 0),
(10, N'Tea',                  N'BEV001', 5, 15.00,  5.00,  N'Cup',   1),
(11, N'Coffee',               N'BEV002', 5, 25.00,  10.00, N'Cup',   1),
(12, N'Mango Juice',          N'BEV003', 5, 35.00,  15.00, N'Glass', 1),
(13, N'Payesh',               N'DES001', 6, 40.00,  20.00, N'Bowl',  1),
(14, N'Special Thali',        N'SPL001', 7, 200.00,120.00, N'Plate', 0),
(15, N'Lunch Combo',          N'CMB001', 8, 160.00, 95.00, N'Plate', 0);
SET IDENTITY_INSERT [dbo].[menu_items] OFF;
GO

-- ============================================================
-- 12. SUPPLIERS (5 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[suppliers] ON;
INSERT INTO [dbo].[suppliers] ([id],[supplier_name],[supplier_code],[contact_person],[phone])
VALUES
(1, N'Fresh Farms Ltd',       N'SUP001', N'Mr. Kamal',   N'+8801811000001'),
(2, N'Dhaka Spice Traders',   N'SUP002', N'Mr. Hashem',  N'+8801811000002'),
(3, N'City Fish Market',      N'SUP003', N'Mr. Jalal',   N'+8801811000003'),
(4, N'Prime Meat Supplies',   N'SUP004', N'Mr. Rafiq',   N'+8801811000004'),
(5, N'Bengal Grocery Store',   N'SUP005', N'Mr. Salam',   N'+8801811000005');
SET IDENTITY_INSERT [dbo].[suppliers] OFF;
GO

-- ============================================================
-- 13. RAW MATERIALS (10 rows)
-- ============================================================
SET IDENTITY_INSERT [dbo].[raw_materials] ON;
INSERT INTO [dbo].[raw_materials] ([id],[material_name],[material_code],[category],[unit_of_measure],[minimum_stock_level],[default_supplier_id],[is_perishable],[shelf_life_days])
VALUES
(1,  N'Rice',          N'RM001', N'Grains',      N'Kg',     50.000, 1, 0, 365),
(2,  N'Chicken',       N'RM002', N'Meat',        N'Kg',     10.000, 4, 1, 3),
(3,  N'Fish',          N'RM003', N'Seafood',     N'Kg',     8.000,  3, 1, 2),
(4,  N'Cooking Oil',   N'RM004', N'Oils',        N'Liter',  10.000, 5, 0, 180),
(5,  N'Onion',         N'RM005', N'Vegetables',  N'Kg',     15.000, 1, 1, 14),
(6,  N'Potato',        N'RM006', N'Vegetables',  N'Kg',     20.000, 1, 1, 30),
(7,  N'Egg',           N'RM007', N'Dairy',       N'Piece',  100.000,1, 1, 21),
(8,  N'Flour',         N'RM008', N'Grains',      N'Kg',     20.000, 5, 0, 180),
(9,  N'Sugar',         N'RM009', N'Sweeteners',  N'Kg',     10.000, 5, 0, 365),
(10, N'Tea Leaves',    N'RM010', N'Beverages',   N'Kg',     5.000,  2, 0, 365);
SET IDENTITY_INSERT [dbo].[raw_materials] OFF;
GO

-- Initialize raw material stock
INSERT INTO [dbo].[raw_material_stock] ([raw_material_id],[current_quantity],[last_purchase_price],[average_price])
VALUES
(1, 100.000, 65.00, 63.00),(2, 25.000, 350.00, 340.00),(3, 15.000, 400.00, 380.00),
(4, 20.000, 180.00, 175.00),(5, 30.000, 50.00, 48.00),(6, 40.000, 30.00, 28.00),
(7, 200.000, 12.00, 11.50),(8, 30.000, 55.00, 52.00),(9, 15.000, 95.00, 90.00),
(10, 8.000, 600.00, 580.00);
GO

-- ============================================================
-- 14. EMPLOYEE BALANCES (10 rows)
-- ============================================================
INSERT INTO [dbo].[employee_balances] ([employee_id],[advance_balance],[credit_limit],[credit_used])
VALUES
(1, 5000.00, 2000.00, 0.00),(2, 3000.00, 1500.00, 0.00),(3, 2500.00, 1000.00, 0.00),
(4, 2000.00, 1000.00, 0.00),(5, 3500.00, 1500.00, 0.00),(6, 2000.00, 500.00, 0.00),
(7, 4000.00, 2000.00, 0.00),(8, 3000.00, 1500.00, 0.00),(9, 2500.00, 1000.00, 0.00),
(10, 2000.00, 500.00, 0.00);
GO

-- ============================================================
-- 15. SYSTEM SETTINGS
-- ============================================================
INSERT INTO [dbo].[system_settings] ([setting_key],[setting_value],[setting_type],[category],[description])
VALUES
(N'LOW_STOCK_THRESHOLD',        N'5',      N'INTEGER', N'INVENTORY',     N'Alert when food stock falls below this'),
(N'EXPIRY_ALERT_DAYS',          N'3',      N'INTEGER', N'INVENTORY',     N'Alert days before expiry'),
(N'TOKEN_RESET_TIME',           N'00:00',  N'STRING',  N'POS',           N'Daily token reset time (HH:mm)'),
(N'MAX_LOGIN_ATTEMPTS',         N'5',      N'INTEGER', N'SECURITY',      N'Account lockout after N failed logins'),
(N'ACCOUNT_LOCKOUT_MINUTES',    N'30',     N'INTEGER', N'SECURITY',      N'Lockout duration in minutes'),
(N'SESSION_TIMEOUT_MINUTES',    N'30',     N'INTEGER', N'SECURITY',      N'Session timeout in minutes'),
(N'PASSWORD_MIN_LENGTH',        N'8',      N'INTEGER', N'SECURITY',      N'Minimum password length'),
(N'PASSWORD_HISTORY_COUNT',     N'5',      N'INTEGER', N'SECURITY',      N'Cannot reuse last N passwords'),
(N'RECEIPT_HEADER',             N'Company Canteen', N'STRING', N'POS',    N'Receipt header text'),
(N'RECEIPT_FOOTER',             N'Thank you for dining with us!', N'STRING', N'POS', N'Receipt footer text'),
(N'CURRENCY_SYMBOL',            N'৳',      N'STRING',  N'GENERAL',       N'Currency symbol'),
(N'TAX_ENABLED',                N'false',  N'BOOLEAN', N'POS',           N'Enable tax calculation'),
(N'DEFAULT_TAX_RATE',           N'0',      N'DECIMAL', N'POS',           N'Default tax percentage');
GO

PRINT '=============================================';
PRINT 'Seed data inserted successfully.';
PRINT '=============================================';
GO
