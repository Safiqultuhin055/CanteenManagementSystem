-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — STORED PROCEDURES (Part 1)
-- ============================================================
USE [CanteenManagementDB];
GO

-- ============================================================
-- SP: usp_ValidateUserLogin
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ValidateUserLogin]
    @Username NVARCHAR(150),
    @IPAddress NVARCHAR(45) = NULL,
    @UserAgent NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        DECLARE @UserId INT, @PasswordHash NVARCHAR(256), @IsActive BIT,
                @IsDeleted BIT, @FailedCount INT, @LockedUntil DATETIME2;

        SELECT @UserId=id, @PasswordHash=password_hash, @IsActive=is_active,
               @IsDeleted=is_deleted, @FailedCount=failed_login_count, @LockedUntil=locked_until
        FROM [dbo].[users] WHERE username=@Username;

        IF @UserId IS NULL
        BEGIN
            INSERT INTO [dbo].[login_history](username,ip_address,user_agent,login_status,failure_reason)
            VALUES(@Username,@IPAddress,@UserAgent,'FAILED','USER_NOT_FOUND');
            SELECT 0 AS Success, 'Invalid username or password' AS Message;
            RETURN;
        END

        IF @IsDeleted = 1 OR @IsActive = 0
        BEGIN
            INSERT INTO [dbo].[login_history](user_id,username,ip_address,user_agent,login_status,failure_reason)
            VALUES(@UserId,@Username,@IPAddress,@UserAgent,'FAILED','ACCOUNT_INACTIVE');
            SELECT 0 AS Success, 'Account is inactive' AS Message;
            RETURN;
        END

        IF @LockedUntil IS NOT NULL AND @LockedUntil > SYSDATETIME()
        BEGIN
            INSERT INTO [dbo].[login_history](user_id,username,ip_address,user_agent,login_status,failure_reason)
            VALUES(@UserId,@Username,@IPAddress,@UserAgent,'LOCKED','ACCOUNT_LOCKED');
            SELECT 0 AS Success, 'Account is locked' AS Message;
            RETURN;
        END

        -- Return user data for Django to verify password
        SELECT 1 AS Success, 'OK' AS Message, u.id, u.username, u.password_hash,
               u.full_name, u.email, u.must_change_password, u.employee_id
        FROM [dbo].[users] u WHERE u.id = @UserId;
    END TRY
    BEGIN CATCH
        SELECT 0 AS Success, ERROR_MESSAGE() AS Message;
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_RecordLoginSuccess
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_RecordLoginSuccess]
    @UserId INT, @IPAddress NVARCHAR(45)=NULL, @UserAgent NVARCHAR(500)=NULL, @SessionKey NVARCHAR(200)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE [dbo].[users] SET last_login=SYSDATETIME(), failed_login_count=0, locked_until=NULL WHERE id=@UserId;
        INSERT INTO [dbo].[login_history](user_id,username,ip_address,user_agent,login_status)
        SELECT @UserId, username, @IPAddress, @UserAgent, 'SUCCESS' FROM [dbo].[users] WHERE id=@UserId;
        IF @SessionKey IS NOT NULL
            INSERT INTO [dbo].[user_sessions](user_id,session_key,ip_address,user_agent)
            VALUES(@UserId,@SessionKey,@IPAddress,@UserAgent);
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_RecordLoginFailure
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_RecordLoginFailure]
    @Username NVARCHAR(150), @IPAddress NVARCHAR(45)=NULL, @Reason NVARCHAR(200)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @UserId INT, @MaxAttempts INT=5, @LockoutMin INT=30;
    SELECT @UserId=id FROM [dbo].[users] WHERE username=@Username;
    SELECT @MaxAttempts=CAST(setting_value AS INT) FROM system_settings WHERE setting_key='MAX_LOGIN_ATTEMPTS';
    SELECT @LockoutMin=CAST(setting_value AS INT) FROM system_settings WHERE setting_key='ACCOUNT_LOCKOUT_MINUTES';
    IF @UserId IS NOT NULL
    BEGIN
        UPDATE [dbo].[users] SET failed_login_count=failed_login_count+1,
            locked_until=CASE WHEN failed_login_count+1>=@MaxAttempts THEN DATEADD(MINUTE,@LockoutMin,SYSDATETIME()) ELSE locked_until END
        WHERE id=@UserId;
    END
    INSERT INTO [dbo].[login_history](user_id,username,ip_address,login_status,failure_reason)
    VALUES(@UserId,@Username,@IPAddress,'FAILED',ISNULL(@Reason,'INVALID_PASSWORD'));
END;
GO

-- ============================================================
-- SP: usp_ChangePassword
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_ChangePassword]
    @UserId INT, @NewPasswordHash NVARCHAR(256), @ChangedBy INT, @Reason NVARCHAR(100)='SELF_CHANGE', @IPAddress NVARCHAR(45)=NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO [dbo].[password_history](user_id,password_hash,changed_by,change_reason,ip_address)
        SELECT @UserId, password_hash, @ChangedBy, @Reason, @IPAddress FROM [dbo].[users] WHERE id=@UserId;
        UPDATE [dbo].[users] SET password_hash=@NewPasswordHash, password_changed_at=SYSDATETIME(),
            must_change_password=0, updated_by=@ChangedBy, updated_at=SYSDATETIME() WHERE id=@UserId;
        INSERT INTO [dbo].[audit_logs](user_id,action,table_name,record_id,module,description)
        VALUES(@ChangedBy,'PASSWORD_CHANGE','users',@UserId,'Security','Password changed');
        COMMIT TRANSACTION;
        SELECT 1 AS Success, 'Password changed successfully' AS Message;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT 0 AS Success, ERROR_MESSAGE() AS Message;
    END CATCH
END;
GO

-- ============================================================
-- SP: usp_AllocateBalance
-- ============================================================
CREATE OR ALTER PROCEDURE [dbo].[usp_AllocateBalance]
    @EmployeeId INT, @Amount DECIMAL(18,2), @AllocationType NVARCHAR(50), @Remarks NVARCHAR(500)=NULL, @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @BalanceBefore DECIMAL(18,2), @BalanceAfter DECIMAL(18,2);
        SELECT @BalanceBefore=advance_balance FROM [dbo].[employee_balances] WHERE employee_id=@EmployeeId;
        IF @BalanceBefore IS NULL
        BEGIN
            INSERT INTO [dbo].[employee_balances](employee_id,advance_balance) VALUES(@EmployeeId,0);
            SET @BalanceBefore=0;
        END
        SET @BalanceAfter=@BalanceBefore+@Amount;
        UPDATE [dbo].[employee_balances] SET advance_balance=@BalanceAfter, total_allocated=total_allocated+@Amount,
            last_transaction_at=SYSDATETIME(), updated_at=SYSDATETIME() WHERE employee_id=@EmployeeId;
        INSERT INTO [dbo].[balance_allocations](employee_id,allocation_type,amount,balance_before,balance_after,remarks,created_by)
        VALUES(@EmployeeId,@AllocationType,@Amount,@BalanceBefore,@BalanceAfter,@Remarks,@CreatedBy);
        INSERT INTO [dbo].[card_transactions](transaction_number,employee_id,transaction_type,amount,
            advance_balance_before,advance_balance_after,created_by)
        VALUES(CONCAT('TXN-',FORMAT(SYSDATETIME(),'yyyyMMdd'),'-',FORMAT(NEXT VALUE FOR dbo.seq_transaction,'0000')),
            @EmployeeId,@AllocationType,@Amount,@BalanceBefore,@BalanceAfter,@CreatedBy);
        COMMIT TRANSACTION;
        SELECT 1 AS Success, 'Balance allocated' AS Message, @BalanceAfter AS NewBalance;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
        SELECT 0 AS Success, ERROR_MESSAGE() AS Message;
    END CATCH
END;
GO

-- ============================================================
-- SEQUENCE for transaction numbers
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.sequences WHERE name='seq_transaction')
    CREATE SEQUENCE [dbo].[seq_transaction] AS INT START WITH 1 INCREMENT BY 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.sequences WHERE name='seq_order')
    CREATE SEQUENCE [dbo].[seq_order] AS INT START WITH 1 INCREMENT BY 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.sequences WHERE name='seq_payment')
    CREATE SEQUENCE [dbo].[seq_payment] AS INT START WITH 1 INCREMENT BY 1;
GO
IF NOT EXISTS (SELECT 1 FROM sys.sequences WHERE name='seq_purchase')
    CREATE SEQUENCE [dbo].[seq_purchase] AS INT START WITH 1 INCREMENT BY 1;
GO

PRINT 'Stored Procedures Part 1 created successfully.';
GO
