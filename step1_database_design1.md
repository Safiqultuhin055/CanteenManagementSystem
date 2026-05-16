# Canteen Management System — Step 1: Database Design & Architecture

> [!NOTE]
> All requested SQL scripts (Database Creation, Tables, Constraints, Indexes, Seed Data, Stored Procedures, and Views) have already been securely generated and saved into the `database\` directory of your project workspace. This document provides the high-level architectural overview, ERD, Business Flows, and Django compatibility notes for your review before we proceed.

## 1. Entity Relationship Diagram (ERD)

The database is normalized and designed with strict adherence to SQL Server best practices, including proper Foreign Key constraints and schema grouping.

```mermaid
erDiagram
    %% Security & Users
    USERS ||--o{ USER_ROLES : "assigned"
    ROLES ||--o{ USER_ROLES : "grants"
    ROLES ||--o{ ROLE_PERMISSIONS : "has"
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : "granted by"
    USERS ||--o{ LOGIN_HISTORY : "logs"

    %% Employees
    DEPARTMENTS ||--o{ EMPLOYEES : "contains"
    EMPLOYEES ||--o{ EMPLOYEE_CARDS : "holds"
    EMPLOYEES ||--o| USERS : "links to"
    EMPLOYEES ||--o| EMPLOYEE_BALANCES : "has"
    EMPLOYEES ||--o{ BALANCE_ALLOCATIONS : "receives"

    %% Inventory & Food
    FOOD_CATEGORIES ||--o{ MENU_ITEMS : "contains"
    SUPPLIERS ||--o{ STOCK_PURCHASES : "supplies"
    STOCK_PURCHASES ||--o{ STOCK_PURCHASE_DETAILS : "contains"
    RAW_MATERIALS ||--o{ STOCK_PURCHASE_DETAILS : "purchased as"
    RAW_MATERIALS ||--o| RAW_MATERIAL_STOCK : "tracked in"
    
    %% POS & Sales
    EMPLOYEE_CARDS ||--o{ ORDERS : "pays for"
    USERS ||--o{ ORDERS : "processed by"
    ORDERS ||--o{ ORDER_DETAILS : "contains"
    MENU_ITEMS ||--o{ ORDER_DETAILS : "ordered in"
    ORDERS ||--o| PAYMENTS : "paid via"
    ORDERS ||--o| KITCHEN_QUEUE : "sent to"
    ORDERS ||--o| DISTRIBUTION_QUEUE : "distributed via"
```

---

## 2. Business Flow Charts

### Main Canteen Flow (POS to Distribution)
```mermaid
flowchart TD
    Start([Start Sale]) --> ScanCard[Scan RFID/NFC Card]
    ScanCard --> Validate{Card Valid & Active?}
    Validate -- No --> ErrorCard[Show Invalid Card Error]
    Validate -- Yes --> CheckBalance[Check Employee Balance & Credit Limit]
    CheckBalance --> SelectItems[Select Menu Items]
    SelectItems --> CheckStock{Stock Available?}
    CheckStock -- No --> ErrorStock[Show Out of Stock Error]
    CheckStock -- Yes --> CreateOrder[Create POS Order]
    
    CreateOrder --> Deduct[Deduct Balance / Register Credit]
    Deduct --> GenToken[Generate Daily Token & Print Receipt]
    
    GenToken --> KDS[Send to Kitchen Display System]
    KDS --> Prepare[Chef Prepares Food]
    Prepare --> UpdateStock[Auto-Deduct Raw Materials]
    UpdateStock --> Distribution[Send to Distribution Counter]
    
    Distribution --> Handover[Handover to Employee]
    Handover --> Audit[Log Transaction & Complete]
    Audit --> End([Transaction Closed])
```

### Monthly Balance Allocation Flow
```mermaid
flowchart TD
    Start([Month Start]) --> SelectDept[Select Department/Employees]
    SelectDept --> EnterAmount[Enter Allowance Amount]
    EnterAmount --> ValidateRules{Validate Limits & Roles?}
    ValidateRules -- No --> Error[Reject Allocation]
    ValidateRules -- Yes --> SP[Execute Balance Allocation SP]
    
    SP --> UpdateBal[Update EmployeeBalances Table]
    UpdateBal --> LogTrans[Log in CardTransactions]
    LogTrans --> AuditLog[Write to AuditLogs]
    AuditLog --> Notify[Send Notification to Employee]
    Notify --> End([Allocation Complete])
```

### Kitchen Workflow
```mermaid
flowchart TD
    NewOrder([New Order Received]) --> Queue[Added to KitchenQueue]
    Queue --> StatusPending[Status: PENDING]
    StatusPending --> DisplayKDS[Display on Kitchen Monitor]
    
    DisplayKDS --> Accept[Chef Accepts Order]
    Accept --> StatusPrep[Status: PREPARING]
    
    StatusPrep --> Complete[Preparation Complete]
    Complete --> StatusReady[Status: READY]
    
    StatusReady --> DistQueue[Move to DistributionQueue]
    DistQueue --> NotifyScreen[Update Token Display Screen]
```

---

## 3. Django ORM Compatibility Notes

To ensure seamless integration with `mssql-django`, the database schema follows these rules:
1. **Primary Keys**: All tables use an `id` column defined as `INT IDENTITY(1,1)`, which maps perfectly to Django's default AutoField.
2. **Naming Conventions**: Table names use lowercase with underscores (e.g., `employee_cards`), which aligns with Django's `db_table` meta options.
3. **Data Types**:
   - `BIT` is used for booleans (`is_active`, `is_deleted`) to map to `models.BooleanField()`.
   - `DATETIME2(7)` is used for timestamps to map accurately to `models.DateTimeField()`.
   - `DECIMAL(18,2)` is used for financial fields to map to `models.DecimalField()`.
   - `NVARCHAR` is used for all text to fully support Django's Unicode expectations for `CharField` and `TextField`.
4. **Soft Deletes**: The `is_deleted` column on major tables allows overriding the Django `Manager` to filter out deleted records without losing historical data.
5. **Auditing**: `created_by`, `created_at`, `updated_by`, and `updated_at` are pre-defined, ready to be handled via a custom Django model mixin.

---

## 4. Performance Recommendations

1. **Indexing**: Non-clustered indexes are applied on all Foreign Keys (e.g., `user_id`, `employee_id`) and highly queried columns like `card_number` and `order_date`.
2. **Query Store**: Query Store has been enabled in the `01_create_database.sql` script to help analyze query performance natively within SQL Server.
3. **Transaction Safety**: All Stored Procedures (e.g., `sp_ProcessPOSOrder`) utilize `BEGIN TRY ... BEGIN CATCH` blocks and `SET XACT_ABORT ON` to ensure rollback on failure, avoiding partial data commits.
4. **Connection Pooling**: When configuring `DATABASES` in Django, ensure connection pooling is handled properly in production via ODBC settings to avoid exhaustion under heavy POS load.
