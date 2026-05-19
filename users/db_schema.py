"""Idempotent SQL Server schema helpers."""
from django.db import connection

_CREATE_USER_PERMISSIONS = """
IF NOT EXISTS (
    SELECT 1 FROM sys.tables
    WHERE name = N'user_permissions' AND schema_id = SCHEMA_ID(N'dbo')
)
BEGIN
    CREATE TABLE [dbo].[user_permissions] (
        [id]            INT IDENTITY(1,1)   NOT NULL,
        [user_id]       INT                 NOT NULL,
        [permission_id] INT                 NOT NULL,
        [is_active]     BIT                 NOT NULL DEFAULT 1,
        [is_deleted]    BIT                 NOT NULL DEFAULT 0,
        [created_by]    INT                 NULL,
        [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
        [updated_by]    INT                 NULL,
        [updated_at]    DATETIME2(7)        NULL,
        CONSTRAINT [PK_user_permissions] PRIMARY KEY CLUSTERED ([id]),
        CONSTRAINT [FK_user_permissions_user] FOREIGN KEY ([user_id])
            REFERENCES [dbo].[users]([id]),
        CONSTRAINT [FK_user_permissions_permission] FOREIGN KEY ([permission_id])
            REFERENCES [dbo].[permissions]([id]),
        CONSTRAINT [UQ_user_permissions] UNIQUE ([user_id], [permission_id])
    );
    CREATE NONCLUSTERED INDEX [IX_user_permissions_user]
        ON [dbo].[user_permissions] ([user_id], [is_active], [is_deleted]);
END
"""


_CREATE_USER_MENU_GRANTS = """
IF NOT EXISTS (
    SELECT 1 FROM sys.tables
    WHERE name = N'user_menu_grants' AND schema_id = SCHEMA_ID(N'dbo')
)
BEGIN
    CREATE TABLE [dbo].[user_menu_grants] (
        [id]            INT IDENTITY(1,1)   NOT NULL,
        [user_id]       INT                 NOT NULL,
        [menu_id]       INT                 NOT NULL,
        [is_active]     BIT                 NOT NULL DEFAULT 1,
        [is_deleted]    BIT                 NOT NULL DEFAULT 0,
        [created_by]    INT                 NULL,
        [created_at]    DATETIME2(7)        NOT NULL DEFAULT SYSDATETIME(),
        [updated_by]    INT                 NULL,
        [updated_at]    DATETIME2(7)        NULL,
        CONSTRAINT [PK_user_menu_grants] PRIMARY KEY CLUSTERED ([id]),
        CONSTRAINT [FK_user_menu_grants_user] FOREIGN KEY ([user_id])
            REFERENCES [dbo].[users]([id]),
        CONSTRAINT [FK_user_menu_grants_menu] FOREIGN KEY ([menu_id])
            REFERENCES [dbo].[menus]([id]),
        CONSTRAINT [UQ_user_menu_grants] UNIQUE ([user_id], [menu_id])
    );
    CREATE NONCLUSTERED INDEX [IX_user_menu_grants_user]
        ON [dbo].[user_menu_grants] ([user_id], [is_active], [is_deleted]);
END
"""


def ensure_user_permissions_table():
    with connection.cursor() as cursor:
        cursor.execute(_CREATE_USER_PERMISSIONS)


def ensure_user_menu_grants_table():
    with connection.cursor() as cursor:
        cursor.execute(_CREATE_USER_MENU_GRANTS)


def ensure_user_access_schema():
    ensure_user_permissions_table()
    ensure_user_menu_grants_table()
