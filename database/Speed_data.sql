-- ============================================================
-- CANTEEN MANAGEMENT SYSTEM — Speed_data.sql
-- Purpose: Insert 100 dummy employees (minimum) for testing/performance
-- Run AFTER: 09_seed_data.sql (requires departments 1-10)
-- Safe to re-run: skips if employee_code already exists
-- ============================================================

USE [CanteenManagementDB];
GO

SET NOCOUNT ON;

DECLARE @StartId INT = 13;
DECLARE @EndId INT = 112;
DECLARE @i INT = @StartId;

DECLARE @FirstNames TABLE (n NVARCHAR(50));
INSERT INTO @FirstNames VALUES
(N'Rahim'),(N'Karim'),(N'Jamal'),(N'Hasan'),(N'Ali'),(N'Ahmed'),(N'Rafiq'),(N'Salam'),
(N'Nasir'),(N'Kabir'),(N'Imran'),(N'Sohel'),(N'Rubel'),(N'Tanvir'),(N'Farhan'),(N'Arif'),
(N'Nabil'),(N'Sakib'),(N'Mehedi'),(N'Parvez'),(N'Fatema'),(N'Nasreen'),(N'Sumaiya'),(N'Ritu'),
(N'Shanta'),(N'Priya'),(N'Nusrat'),(N'Sadia'),(N'Lamia'),(N'Tasnim');

DECLARE @LastNames TABLE (n NVARCHAR(50));
INSERT INTO @LastNames VALUES
(N'Islam'),(N'Rahman'),(N'Hossain'),(N'Ahmed'),(N'Khan'),(N'Begum'),(N'Akter'),(N'Das'),
(N'Roy'),(N'Uddin'),(N'Chowdhury'),(N'Sarkar'),(N'Miah'),(N'Ali'),(N'Hasan');

WHILE @i <= @EndId
BEGIN
    DECLARE @Code NVARCHAR(50) = CONCAT(N'EMP', RIGHT(CONCAT(N'000', @i), 3));
    IF NOT EXISTS (SELECT 1 FROM [dbo].[employees] WHERE [employee_code] = @Code)
    BEGIN
        DECLARE @Fn NVARCHAR(50), @Ln NVARCHAR(50), @Full NVARCHAR(300);
        DECLARE @Dept INT = ((@i - 1) % 10) + 1;
        SELECT TOP 1 @Fn = n FROM @FirstNames ORDER BY NEWID();
        SELECT TOP 1 @Ln = n FROM @LastNames ORDER BY NEWID();
        SET @Full = CONCAT(@Fn, N' ', @Ln);

        INSERT INTO [dbo].[employees] (
            [employee_code],[first_name],[last_name],[full_name],[email],[phone],
            [department_id],[designation],[employee_type],[is_active],[is_deleted]
        )
        VALUES (
            @Code, @Fn, @Ln, @Full,
            CONCAT(LOWER(@Fn), N'.', LOWER(@Ln), @i, N'@company.com'),
            CONCAT(N'+88017', RIGHT(CONCAT(N'00000000', @i + 1000), 8)),
            @Dept,
            CASE (@i % 5)
                WHEN 0 THEN N'Officer'
                WHEN 1 THEN N'Executive'
                WHEN 2 THEN N'Analyst'
                WHEN 3 THEN N'Engineer'
                ELSE N'Staff'
            END,
            CASE (@i % 4) WHEN 0 THEN N'CONTRACT' WHEN 1 THEN N'INTERN' ELSE N'PERMANENT' END,
            1, 0
        );

        DECLARE @EmpId INT = SCOPE_IDENTITY();

        IF NOT EXISTS (SELECT 1 FROM [dbo].[employee_cards] WHERE [card_number] = CONCAT(N'RFID-SPD-', @Code))
        BEGIN
            INSERT INTO [dbo].[employee_cards] ([employee_id],[card_number],[card_type],[card_status],[is_active])
            VALUES (@EmpId, CONCAT(N'RFID-SPD-', @Code), N'RFID', N'ACTIVE', 1);
        END

        IF NOT EXISTS (SELECT 1 FROM [dbo].[employee_balances] WHERE [employee_id] = @EmpId)
        BEGIN
            INSERT INTO [dbo].[employee_balances] ([employee_id],[advance_balance],[credit_limit],[credit_used])
            VALUES (
                @EmpId,
                CAST(1500 + (@i * 17) % 4500 AS DECIMAL(18,2)),
                CAST(500 + (@i * 13) % 2000 AS DECIMAL(18,2)),
                0.00
            );
        END
    END
    SET @i = @i + 1;
END
GO

PRINT CONCAT(N'Speed_data: employee count = ', (SELECT COUNT(*) FROM [dbo].[employees] WHERE [is_deleted] = 0));
GO
