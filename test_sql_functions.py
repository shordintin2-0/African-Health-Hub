"""
Test SQL functions, triggers and stored procedures.
This script can be run independently to create and test database functions.
"""
import os
import sys
from datetime import datetime
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import app and database directly
# Since we're running this from the project root
from african_health_hub_flask.app import app, db, Patient

def create_age_calculation_function():
    """Create the CalculatePatientAge function in SQL Server"""
    sql = """
    IF OBJECT_ID('CalculatePatientAge', 'FN') IS NOT NULL
        DROP FUNCTION CalculatePatientAge;
    
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
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("✅ CalculatePatientAge function created")
            print("✅ CalculatePatientAge function created")
        except Exception as e:
            logger.error(f"❌ Error creating CalculatePatientAge function: {str(e)}")
            print(f"❌ Error creating CalculatePatientAge function: {str(e)}")
            raise

def create_update_last_modified_trigger():
    """Create the UpdateLastModified trigger"""
    sql = """
    IF OBJECT_ID('UpdateLastModified', 'TR') IS NOT NULL
        DROP TRIGGER UpdateLastModified;
    
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
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("✅ UpdateLastModified trigger created")
            print("✅ UpdateLastModified trigger created")
        except Exception as e:
            logger.error(f"❌ Error creating UpdateLastModified trigger: {str(e)}")
            print(f"❌ Error creating UpdateLastModified trigger: {str(e)}")
            raise

def create_audit_medical_records_trigger():
    """Create the AuditMedicalRecordsChanges trigger"""
    sql = """
    IF OBJECT_ID('AuditMedicalRecordsChanges', 'TR') IS NOT NULL
        DROP TRIGGER AuditMedicalRecordsChanges;
    
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
        
        INSERT INTO security_audit181 (action, action_details, action_date, status)
        SELECT @action_type, 'medical_records181', GETDATE(), 'Success'
        FROM inserted i
        FULL OUTER JOIN deleted d ON i.id = d.id;
    END
    """
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("✅ AuditMedicalRecordsChanges trigger created")
            print("✅ AuditMedicalRecordsChanges trigger created")
        except Exception as e:
            logger.error(f"❌ Error creating AuditMedicalRecordsChanges trigger: {str(e)}")
            print(f"❌ Error creating AuditMedicalRecordsChanges trigger: {str(e)}")
            raise

def create_get_patient_appointments_procedure():
    """Create the GetPatientAppointments stored procedure"""
    sql = """
    IF OBJECT_ID('GetPatientAppointments', 'P') IS NOT NULL
        DROP PROCEDURE GetPatientAppointments;
    
    CREATE PROCEDURE GetPatientAppointments
        @PatientID INT
    AS
    BEGIN
        SELECT * FROM appointments181
        WHERE patient_id = @PatientID
        ORDER BY appointment_date;
    END
    """
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("✅ GetPatientAppointments procedure created")
            print("✅ GetPatientAppointments procedure created")
        except Exception as e:
            logger.error(f"❌ Error creating GetPatientAppointments procedure: {str(e)}")
            print(f"❌ Error creating GetPatientAppointments procedure: {str(e)}")
            raise

def create_classify_patient_risk_procedure():
    """Create the ClassifyPatientRisk stored procedure"""
    sql = """
    IF OBJECT_ID('ClassifyPatientRisk', 'P') IS NOT NULL
        DROP PROCEDURE ClassifyPatientRisk;
    
    CREATE PROCEDURE ClassifyPatientRisk
        @PatientID INT
    AS
    BEGIN
        DECLARE @ChronicConditions INT;
        
        SELECT @ChronicConditions = COUNT(*) 
        FROM medical_records181
        WHERE patient_id = @PatientID;
        
        IF @ChronicConditions > 2
            UPDATE patients181 SET medical_history = CONCAT(medical_history, ' [HIGH RISK]') WHERE id = @PatientID;
        ELSE IF @ChronicConditions > 0
            UPDATE patients181 SET medical_history = CONCAT(medical_history, ' [MEDIUM RISK]') WHERE id = @PatientID;
        ELSE
            UPDATE patients181 SET medical_history = CONCAT(medical_history, ' [LOW RISK]') WHERE id = @PatientID;
    END
    """
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("✅ ClassifyPatientRisk procedure created")
            print("✅ ClassifyPatientRisk procedure created")
        except Exception as e:
            logger.error(f"❌ Error creating ClassifyPatientRisk procedure: {str(e)}")
            print(f"❌ Error creating ClassifyPatientRisk procedure: {str(e)}")
            raise

def test_age_calculation():
    """Test the CalculatePatientAge function"""
    with app.app_context():
        patient = Patient.query.filter(Patient.date_of_birth.isnot(None)).first()
        if patient and patient.date_of_birth:
            try:
                age = db.session.execute(
                    text("SELECT dbo.CalculatePatientAge(:birth_date) AS age"), 
                    {"birth_date": patient.date_of_birth}
                ).fetchone()
                logger.info(f"✅ Age calculation test: Patient #{patient.id} is {age[0]} years old")
                print(f"✅ Age calculation test: Patient #{patient.id} is {age[0]} years old")
                return age[0]
            except Exception as e:
                logger.error(f"❌ Age calculation test failed: {str(e)}")
                print(f"❌ Age calculation test failed: {str(e)}")
                return None
        else:
            logger.error("❌ No patients with date of birth found")
            print("❌ No patients with date of birth found")
            return None

if __name__ == "__main__":
    try:
        # Create all functions and procedures
        create_age_calculation_function()
        create_update_last_modified_trigger()
        create_audit_medical_records_trigger()
        create_get_patient_appointments_procedure()
        create_classify_patient_risk_procedure()
        
        # Test functions
        age = test_age_calculation()
        
        print("\nAll SQL functions, triggers, and procedures have been created successfully.")
        print("\nYou can now access these in your application.")
        print("\nTo test the Patient Risk Assessment feature, log in as an admin or staff user")
        print("and view a patient's profile, then click the 'Risk Assessment' button.")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("\nSome SQL functions, triggers, or procedures may not have been created correctly.")
        print("Please check the error message and try again.") 