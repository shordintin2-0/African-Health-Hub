"""
Script to create SQL functions, triggers and stored procedures for African Health Hub
This script should be run directly using: python create_sql_functions.py
"""
import pyodbc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
server = 'AMERLEY'
database = 'AfricanHealthHub181'
driver = 'ODBC Driver 17 for SQL Server'

# Create the connection string
connection_string = (
    f'DRIVER={{{driver}}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    'Trusted_Connection=yes;'
    'ENCRYPT=yes;'
    'TrustServerCertificate=yes'
)

def execute_sql(sql, description):
    """Execute SQL command and log result"""
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        logger.info(f"✅ Successfully executed {description}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error executing {description}: {str(e)}")
        return False

def create_age_calculation_function():
    """Create the CalculatePatientAge function"""
    # First drop if exists
    drop_sql = "IF OBJECT_ID('CalculatePatientAge', 'FN') IS NOT NULL DROP FUNCTION CalculatePatientAge;"
    execute_sql(drop_sql, "drop CalculatePatientAge function if exists")
    
    # Then create
    create_sql = """
    CREATE FUNCTION CalculatePatientAge
        (@BirthDate DATE)
    RETURNS INT
    AS
    BEGIN
        RETURN DATEDIFF(YEAR, @BirthDate, GETDATE()) - 
               CASE WHEN DATEADD(YEAR, DATEDIFF(YEAR, @BirthDate, GETDATE()), @BirthDate) > GETDATE() 
                    THEN 1 ELSE 0 END;
    END
    """
    return execute_sql(create_sql, "create CalculatePatientAge function")

def create_update_last_modified_trigger():
    """Create the UpdateLastModified trigger"""
    # First drop if exists
    drop_sql = "IF OBJECT_ID('UpdateLastModified', 'TR') IS NOT NULL DROP TRIGGER UpdateLastModified;"
    execute_sql(drop_sql, "drop UpdateLastModified trigger if exists")
    
    # Then create
    create_sql = """
    CREATE TRIGGER UpdateLastModified
    ON medical_records181
    AFTER UPDATE
    AS
    BEGIN
        UPDATE medical_records181
        SET updated_at = GETDATE()
        FROM medical_records181 m
        INNER JOIN inserted i ON m.id = i.id;
    END
    """
    return execute_sql(create_sql, "create UpdateLastModified trigger")

def create_audit_medical_records_trigger():
    """Create the AuditMedicalRecordsChanges trigger"""
    # First drop if exists
    drop_sql = "IF OBJECT_ID('AuditMedicalRecordsChanges', 'TR') IS NOT NULL DROP TRIGGER AuditMedicalRecordsChanges;"
    execute_sql(drop_sql, "drop AuditMedicalRecordsChanges trigger if exists")
    
    # Then create
    create_sql = """
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
    END
    """
    return execute_sql(create_sql, "create AuditMedicalRecordsChanges trigger")

def create_get_patient_appointments_procedure():
    """Create the GetPatientAppointments procedure"""
    # First drop if exists
    drop_sql = "IF OBJECT_ID('GetPatientAppointments', 'P') IS NOT NULL DROP PROCEDURE GetPatientAppointments;"
    execute_sql(drop_sql, "drop GetPatientAppointments procedure if exists")
    
    # Then create
    create_sql = """
    CREATE PROCEDURE GetPatientAppointments
        @PatientID INT
    AS
    BEGIN
        SELECT * FROM appointments181
        WHERE patient_id = @PatientID
        ORDER BY appointment_date;
    END
    """
    return execute_sql(create_sql, "create GetPatientAppointments procedure")

def create_classify_patient_risk_procedure():
    """Create the ClassifyPatientRisk procedure"""
    # First drop if exists
    drop_sql = "IF OBJECT_ID('ClassifyPatientRisk', 'P') IS NOT NULL DROP PROCEDURE ClassifyPatientRisk;"
    execute_sql(drop_sql, "drop ClassifyPatientRisk procedure if exists")
    
    # Then create
    create_sql = """
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
    END
    """
    return execute_sql(create_sql, "create ClassifyPatientRisk procedure")

def main():
    """Execute all SQL functions"""
    print("\nCreating SQL functions for African Health Hub...\n")
    
    success = True
    
    # Create age calculation function
    if not create_age_calculation_function():
        success = False
    
    # Create UpdateLastModified trigger
    if not create_update_last_modified_trigger():
        success = False
    
    # Create AuditMedicalRecordsChanges trigger
    if not create_audit_medical_records_trigger():
        success = False
    
    # Create GetPatientAppointments procedure
    if not create_get_patient_appointments_procedure():
        success = False
    
    # Create ClassifyPatientRisk procedure
    if not create_classify_patient_risk_procedure():
        success = False
    
    print()
    if success:
        print("All SQL functions, triggers, and stored procedures have been created.")
    else:
        print("Some SQL functions, triggers, or procedures could not be created.")
        print("Check the error messages above for details.")
    
    print("\nYou can now access these in your application.")
    print("\nTo test the Patient Risk Assessment feature, log in as an admin or staff user")
    print("and view a patient's profile, then click the 'Risk Assessment' button.")

if __name__ == "__main__":
    main() 