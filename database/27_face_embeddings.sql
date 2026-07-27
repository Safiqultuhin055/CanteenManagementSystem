-- Face recognition embeddings — one registered face per employee.
-- The 128-d descriptor is produced client-side by face-api.js and stored as a
-- JSON array of floats. Recognition compares live descriptors against these
-- server-side (euclidean distance). Safe to re-run.
USE [CanteenManagementDB];
GO

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'face_embeddings')
BEGIN
    CREATE TABLE [dbo].[face_embeddings] (
        [id]            INT IDENTITY(1,1) PRIMARY KEY,
        [employee_id]   INT NOT NULL,
        [embedding]     NVARCHAR(MAX) NOT NULL,   -- JSON array of 128 floats (averaged over samples)
        [model]         NVARCHAR(50)  NOT NULL DEFAULT 'face-api-128',
        [sample_count]  INT NOT NULL DEFAULT 1,   -- how many frames were averaged
        [is_active]     BIT NOT NULL DEFAULT 1,
        [is_deleted]    BIT NOT NULL DEFAULT 0,
        [created_by]    INT NULL,
        [created_at]    DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        [updated_by]    INT NULL,
        [updated_at]    DATETIME2 NULL,
        CONSTRAINT [FK_face_embeddings_employee] FOREIGN KEY ([employee_id])
            REFERENCES [dbo].[employees] ([id]) ON DELETE CASCADE
    );
    PRINT 'Created table face_embeddings';
END
ELSE
    PRINT 'face_embeddings already exists';
GO

-- One row per employee (update overwrites the existing registration).
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_face_embeddings_employee')
    CREATE UNIQUE INDEX [UQ_face_embeddings_employee]
        ON [dbo].[face_embeddings] ([employee_id]);
GO
