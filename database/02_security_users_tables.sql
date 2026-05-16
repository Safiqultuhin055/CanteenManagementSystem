-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — SECURITY & USERS TABLES
-- Database Engine : Microsoft SQL Server 2019+
-- Description     : Security, authentication, authorization,
--                   role management, session & login tracking
-- ============================================================

USE [CanteenManagementDB];
GO

-- ============================================================
-- TABLE: roles
-- Purpose: Define system roles (Admin, Manager, Cashier, etc.)
-- Django:  maps to custom Role model
-- ============================================================
CREATE TABLE [dbo].[roles] (
    [id]            INT IDENTITY(1,1)   NOT NULL,
    [role_name]     NVARCHAR(100)       NOT NULL,
    [role_code]     NVARCHAR(50)        NOT NULL,   -- e.g., 'ADMIN', 'CASHIER'
    [description]   NVARCHAR(500)       NULL,
    [priority]      INT                 NOT NULL DEFAULT 0,  -- lower = higher priority
    [is_active]     BIT                 NOT NULL DEFAULT 1,
    [is_deleted]    BIT                 NOT NULL DEFAULT 0,
    [created_by]    INT                 NULL,
    [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]    INT                 NULL,
    [updated_at]    DATETIME2(7)        NULL,

    CONSTRAINT [PK_roles] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_roles_role_code] UNIQUE ([role_code]),
    CONSTRAINT [UQ_roles_role_name] UNIQUE ([role_name]),
    CONSTRAINT [CK_roles_priority] CHECK ([priority] >= 0)
);
GO

-- ============================================================
-- TABLE: permissions
-- Purpose: Granular permission definitions
-- Django:  maps to custom Permission model
-- ============================================================
CREATE TABLE [dbo].[permissions] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [permission_name]   NVARCHAR(200)       NOT NULL,
    [permission_code]   NVARCHAR(100)       NOT NULL,  -- e.g., 'USER_CREATE', 'ORDER_VIEW'
    [module]            NVARCHAR(100)       NOT NULL,  -- e.g., 'Users', 'Orders', 'Inventory'
    [description]       NVARCHAR(500)       NULL,
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [is_deleted]        BIT                 NOT NULL DEFAULT 0,
    [created_by]        INT                 NULL,
    [created_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]        INT                 NULL,
    [updated_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_permissions] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_permissions_code] UNIQUE ([permission_code])
);
GO

-- ============================================================
-- TABLE: menus
-- Purpose: Application menu structure for navigation
-- Django:  maps to Menu model (self-referencing for hierarchy)
-- ============================================================
CREATE TABLE [dbo].[menus] (
    [id]            INT IDENTITY(1,1)   NOT NULL,
    [menu_name]     NVARCHAR(200)       NOT NULL,
    [menu_code]     NVARCHAR(100)       NOT NULL,
    [parent_id]     INT                 NULL,       -- self-referencing FK
    [url]           NVARCHAR(500)       NULL,       -- Django URL name or path
    [icon_class]    NVARCHAR(100)       NULL,       -- Bootstrap icon class
    [display_order] INT                 NOT NULL DEFAULT 0,
    [menu_level]    INT                 NOT NULL DEFAULT 0,  -- 0=root, 1=child, etc.
    [is_visible]    BIT                 NOT NULL DEFAULT 1,
    [is_active]     BIT                 NOT NULL DEFAULT 1,
    [is_deleted]    BIT                 NOT NULL DEFAULT 0,
    [created_by]    INT                 NULL,
    [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]    INT                 NULL,
    [updated_at]    DATETIME2(7)        NULL,

    CONSTRAINT [PK_menus] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_menus_menu_code] UNIQUE ([menu_code]),
    CONSTRAINT [FK_menus_parent] FOREIGN KEY ([parent_id])
        REFERENCES [dbo].[menus]([id]),
    CONSTRAINT [CK_menus_level] CHECK ([menu_level] >= 0)
);
GO

-- ============================================================
-- TABLE: menu_permissions
-- Purpose: Map menus to required permissions
-- Django:  ManyToMany through table
-- ============================================================
CREATE TABLE [dbo].[menu_permissions] (
    [id]            INT IDENTITY(1,1)   NOT NULL,
    [menu_id]       INT                 NOT NULL,
    [permission_id] INT                 NOT NULL,
    [is_active]     BIT                 NOT NULL DEFAULT 1,
    [created_by]    INT                 NULL,
    [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT [PK_menu_permissions] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_menu_permissions_menu] FOREIGN KEY ([menu_id])
        REFERENCES [dbo].[menus]([id]),
    CONSTRAINT [FK_menu_permissions_permission] FOREIGN KEY ([permission_id])
        REFERENCES [dbo].[permissions]([id]),
    CONSTRAINT [UQ_menu_permissions] UNIQUE ([menu_id], [permission_id])
);
GO

-- ============================================================
-- TABLE: role_permissions
-- Purpose: Assign permissions to roles
-- Django:  ManyToMany through table
-- ============================================================
CREATE TABLE [dbo].[role_permissions] (
    [id]            INT IDENTITY(1,1)   NOT NULL,
    [role_id]       INT                 NOT NULL,
    [permission_id] INT                 NOT NULL,
    [is_active]     BIT                 NOT NULL DEFAULT 1,
    [is_deleted]    BIT                 NOT NULL DEFAULT 0,
    [created_by]    INT                 NULL,
    [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]    INT                 NULL,
    [updated_at]    DATETIME2(7)        NULL,

    CONSTRAINT [PK_role_permissions] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_role_permissions_role] FOREIGN KEY ([role_id])
        REFERENCES [dbo].[roles]([id]),
    CONSTRAINT [FK_role_permissions_permission] FOREIGN KEY ([permission_id])
        REFERENCES [dbo].[permissions]([id]),
    CONSTRAINT [UQ_role_permissions] UNIQUE ([role_id], [permission_id])
);
GO

-- ============================================================
-- TABLE: users
-- Purpose: System users (authentication & profile)
-- Django:  Custom user model extending AbstractBaseUser
-- Notes:   - password_hash stores Django's hashed password
--          - Separate from employees table; linked via employee_id
-- ============================================================
CREATE TABLE [dbo].[users] (
    [id]                    INT IDENTITY(1,1)   NOT NULL,
    [username]              NVARCHAR(150)       NOT NULL,
    [email]                 NVARCHAR(254)       NULL,
    [password_hash]         NVARCHAR(256)       NOT NULL,   -- Django password hash
    [first_name]            NVARCHAR(150)       NULL,
    [last_name]             NVARCHAR(150)       NULL,
    [full_name]             NVARCHAR(300)       NULL,
    [phone]                 NVARCHAR(20)        NULL,
    [employee_id]           INT                 NULL,       -- FK to employees (nullable for admin)
    [profile_image]         NVARCHAR(500)       NULL,       -- path to profile image
    [is_superuser]          BIT                 NOT NULL DEFAULT 0,
    [is_staff]              BIT                 NOT NULL DEFAULT 1,
    [must_change_password]  BIT                 NOT NULL DEFAULT 1,
    [password_changed_at]   DATETIME2(7)        NULL,
    [last_login]            DATETIME2(7)        NULL,
    [failed_login_count]    INT                 NOT NULL DEFAULT 0,
    [locked_until]          DATETIME2(7)        NULL,       -- account lockout
    [is_active]             BIT                 NOT NULL DEFAULT 1,
    [is_deleted]            BIT                 NOT NULL DEFAULT 0,
    [created_by]            INT                 NULL,
    [created_at]            DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]            INT                 NULL,
    [updated_at]            DATETIME2(7)        NULL,

    CONSTRAINT [PK_users] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [UQ_users_username] UNIQUE ([username]),
    CONSTRAINT [UQ_users_email] UNIQUE ([email]),
    CONSTRAINT [CK_users_failed_login] CHECK ([failed_login_count] >= 0)
);
GO

-- ============================================================
-- TABLE: user_roles
-- Purpose: Assign roles to users (many-to-many)
-- Django:  ManyToMany through table
-- ============================================================
CREATE TABLE [dbo].[user_roles] (
    [id]            INT IDENTITY(1,1)   NOT NULL,
    [user_id]       INT                 NOT NULL,
    [role_id]       INT                 NOT NULL,
    [assigned_at]   DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [is_active]     BIT                 NOT NULL DEFAULT 1,
    [is_deleted]    BIT                 NOT NULL DEFAULT 0,
    [created_by]    INT                 NULL,
    [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [updated_by]    INT                 NULL,
    [updated_at]    DATETIME2(7)        NULL,

    CONSTRAINT [PK_user_roles] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_user_roles_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [FK_user_roles_role] FOREIGN KEY ([role_id])
        REFERENCES [dbo].[roles]([id]),
    CONSTRAINT [UQ_user_roles] UNIQUE ([user_id], [role_id])
);
GO

-- ============================================================
-- TABLE: password_history
-- Purpose: Track password changes for security compliance
-- Django:  PasswordHistory model
-- ============================================================
CREATE TABLE [dbo].[password_history] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [user_id]           INT                 NOT NULL,
    [password_hash]     NVARCHAR(256)       NOT NULL,
    [changed_at]        DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [changed_by]        INT                 NULL,       -- who changed it (admin or self)
    [change_reason]     NVARCHAR(100)       NULL,       -- 'SELF_CHANGE', 'ADMIN_RESET', 'FORCED'
    [ip_address]        NVARCHAR(45)        NULL,

    CONSTRAINT [PK_password_history] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_password_history_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id])
);
GO

-- ============================================================
-- TABLE: user_sessions
-- Purpose: Track active user sessions
-- Django:  Session tracking model
-- ============================================================
CREATE TABLE [dbo].[user_sessions] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [user_id]           INT                 NOT NULL,
    [session_key]       NVARCHAR(200)       NOT NULL,   -- Django session key
    [ip_address]        NVARCHAR(45)        NULL,
    [user_agent]        NVARCHAR(500)       NULL,
    [device_type]       NVARCHAR(50)        NULL,       -- 'Desktop', 'Mobile', 'Tablet'
    [login_at]          DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [logout_at]         DATETIME2(7)        NULL,
    [last_activity]     DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [is_active]         BIT                 NOT NULL DEFAULT 1,
    [expired_at]        DATETIME2(7)        NULL,

    CONSTRAINT [PK_user_sessions] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_user_sessions_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [UQ_user_sessions_key] UNIQUE ([session_key])
);
GO

-- ============================================================
-- TABLE: login_history
-- Purpose: Complete login/logout audit trail
-- Django:  LoginHistory model
-- ============================================================
CREATE TABLE [dbo].[login_history] (
    [id]                INT IDENTITY(1,1)   NOT NULL,
    [user_id]           INT                 NULL,       -- NULL if login failed with unknown user
    [username]          NVARCHAR(150)       NOT NULL,   -- store attempted username
    [login_at]          DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
    [logout_at]         DATETIME2(7)        NULL,
    [ip_address]        NVARCHAR(45)        NULL,
    [user_agent]        NVARCHAR(500)       NULL,
    [login_status]      NVARCHAR(20)        NOT NULL DEFAULT 'SUCCESS',  -- 'SUCCESS', 'FAILED', 'LOCKED'
    [failure_reason]    NVARCHAR(200)       NULL,
    [session_duration]  INT                 NULL,       -- duration in seconds

    CONSTRAINT [PK_login_history] PRIMARY KEY CLUSTERED ([id]),
    CONSTRAINT [FK_login_history_user] FOREIGN KEY ([user_id])
        REFERENCES [dbo].[users]([id]),
    CONSTRAINT [CK_login_history_status] CHECK ([login_status] IN ('SUCCESS', 'FAILED', 'LOCKED', 'EXPIRED'))
);
GO

PRINT '==========================================================';
PRINT 'Security & Users tables created successfully (10 tables).';
PRINT '==========================================================';
GO
