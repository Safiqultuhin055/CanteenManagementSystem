-- Third-party API integrations (Claude, OpenAI, TTS, etc.) — safe to re-run.
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'api_integrations')
BEGIN
    CREATE TABLE [dbo].[api_integrations] (
        [id]              INT IDENTITY(1,1) PRIMARY KEY,
        [provider]        NVARCHAR(50)  NOT NULL,   -- anthropic | openai | azure_tts | google | other
        [label]           NVARCHAR(150) NOT NULL,   -- human name, e.g. "Claude (POS voice)"
        [api_key]         NVARCHAR(500) NULL,
        [api_model]       NVARCHAR(150) NULL,       -- e.g. claude-sonnet-5
        [base_url]        NVARCHAR(300) NULL,       -- override endpoint if needed
        [extra_config]    NVARCHAR(MAX) NULL,       -- optional JSON for extra params
        [is_default]      BIT NOT NULL DEFAULT 0,   -- preferred row for its provider
        [is_active]       BIT NOT NULL DEFAULT 1,
        [is_deleted]      BIT NOT NULL DEFAULT 0,
        [created_by]      INT NULL,
        [created_at]      DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_by]      INT NULL,
        [updated_at]      DATETIME2 NULL
    );
    PRINT 'Created table api_integrations';
END
ELSE
    PRINT 'api_integrations already exists';
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_api_integrations_provider')
    CREATE INDEX [IX_api_integrations_provider]
        ON [dbo].[api_integrations] ([provider], [is_active], [is_default]);
GO
