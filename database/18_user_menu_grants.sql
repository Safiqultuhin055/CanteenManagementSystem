-- Explicit per-user menu assignments (checkbox on / soft delete off)
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'user_menu_grants' AND schema_id = SCHEMA_ID(N'dbo'))
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
GO

PRINT 'user_menu_grants table ready.';
GO
