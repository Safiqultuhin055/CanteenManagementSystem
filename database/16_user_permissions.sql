-- ============================================================
-- User-specific permissions (user-wise menu access grants)
-- Run on existing CanteenManagementDB
-- ============================================================
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = N'user_permissions' AND schema_id = SCHEMA_ID(N'dbo'))
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
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN')
BEGIN
    INSERT INTO [dbo].[permissions] ([permission_name],[permission_code],[module])
    VALUES (N'Assign User Menu Permissions', N'USER_MENU_ASSIGN', N'Security');
END
GO

DECLARE @AssignPermId INT = (SELECT [id] FROM [dbo].[permissions] WHERE [permission_code] = N'USER_MENU_ASSIGN');
IF @AssignPermId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [dbo].[role_permissions] WHERE [role_id] = 1 AND [permission_id] = @AssignPermId)
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active]) VALUES (1, @AssignPermId, 1);
    IF NOT EXISTS (SELECT 1 FROM [dbo].[role_permissions] WHERE [role_id] = 2 AND [permission_id] = @AssignPermId)
        INSERT INTO [dbo].[role_permissions] ([role_id],[permission_id],[is_active]) VALUES (2, @AssignPermId, 1);
END
GO

PRINT 'user_permissions table ready.';
GO
