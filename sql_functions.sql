-- SQL script to create all functions, triggers, and stored procedures
-- Run this directly in SQL Server Management Studio

-- First: Create the CalculatePatientAge function
IF OBJECT_ID('CalculatePatientAge', 'FN') IS NOT NULL
    DROP FUNCTION CalculatePatientAge;
GO

CREATE FUNCTION CalculatePatientAge
    (@BirthDate DATE)
RETURNS INT
AS
BEGIN
    RETURN DATEDIFF(YEAR, @BirthDate, GETDATE()) - 
            CASE WHEN DATEADD(YEAR, DATEDIFF(YEAR, @BirthDate, GETDATE()), @BirthDate) > GETDATE() 
                THEN 1 ELSE 0 END;
END;
GO

-- Second: Create the UpdateLastModified trigger
IF OBJECT_ID('UpdateLastModified', 'TR') IS NOT NULL
    DROP TRIGGER UpdateLastModified;
GO

CREATE TRIGGER UpdateLastModified
ON medical_records181
AFTER UPDATE
AS
BEGIN
    UPDATE medical_records181
    SET updated_at = GETDATE()
    FROM medical_records181 m
    INNER JOIN inserted i ON m.id = i.id;
END;
GO

-- Third: Create the AuditMedicalRecordsChanges trigger
IF OBJECT_ID('AuditMedicalRecordsChanges', 'TR') IS NOT NULL
    DROP TRIGGER AuditMedicalRecordsChanges;
GO

CREATE TRIGGER AuditMedicalRecordsChanges
ON medical_records181
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    DECLARE @action_type VARCHAR(50);
    
    IF EXISTS(SELECT * FROM inserted) AND EXISTS(SELECT * FROM deleted)
        SET @action_type = 'UPDATE';
    ELSE IF EXISTS(SELECT * FROM inserted)
        SET @action_type = 'INSERT';
    ELSE
        SET @action_type = 'DELETE';
    
    INSERT INTO security_audit181 (user_id, action, action_details, action_date, status)
    SELECT 1, @action_type, 'medical_records181', GETDATE(), 'Success'
    FROM inserted i
    FULL OUTER JOIN deleted d ON i.id = d.id;
END;
GO

-- Fourth: Create the GetPatientAppointments stored procedure
IF OBJECT_ID('GetPatientAppointments', 'P') IS NOT NULL
    DROP PROCEDURE GetPatientAppointments;
GO

CREATE PROCEDURE GetPatientAppointments
    @PatientID INT
AS
BEGIN
    SELECT * FROM appointments181
    WHERE patient_id = @PatientID
    ORDER BY appointment_date;
END;
GO

-- Fifth: Create the ClassifyPatientRisk stored procedure
IF OBJECT_ID('ClassifyPatientRisk', 'P') IS NOT NULL
    DROP PROCEDURE ClassifyPatientRisk;
GO

CREATE PROCEDURE ClassifyPatientRisk
    @PatientID INT
AS
BEGIN
    DECLARE @ChronicConditions INT;
    
    SELECT @ChronicConditions = COUNT(*) 
    FROM medical_records181
    WHERE patient_id = @PatientID;
    
    IF @ChronicConditions > 2
        UPDATE patients181 SET medical_history = CONCAT(ISNULL(medical_history, ''), ' [HIGH RISK]') WHERE id = @PatientID;
    ELSE IF @ChronicConditions > 0
        UPDATE patients181 SET medical_history = CONCAT(ISNULL(medical_history, ''), ' [MEDIUM RISK]') WHERE id = @PatientID;
    ELSE
        UPDATE patients181 SET medical_history = CONCAT(ISNULL(medical_history, ''), ' [LOW RISK]') WHERE id = @PatientID;
END;
GO

-- Test the function
SELECT dbo.CalculatePatientAge('1990-01-01') AS Age;
GO 