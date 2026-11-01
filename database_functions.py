"""
Database functions for African Health Hub
These functions interface with SQL functions and stored procedures in the database
Please run sql_functions.sql directly in SQL Server Management Studio first
"""
import logging
import pyodbc
from datetime import datetime

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

def initialize_database_functions(db=None):
    """Dummy function that assumes SQL functions are already created"""
    logger.info("✅ SQL functions are assumed to be already created")
    return True

# Helper functions to call the stored procedures
def get_patient_appointments(patient_id):
    """Call the GetPatientAppointments stored procedure"""
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        query = f"EXEC GetPatientAppointments @PatientID = {patient_id}"
        cursor.execute(query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows and convert to list of dictionaries
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error calling GetPatientAppointments: {str(e)}")
        return []

def classify_patient_risk(patient_id):
    """Call the ClassifyPatientRisk stored procedure"""
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        query = f"EXEC ClassifyPatientRisk @PatientID = {patient_id}"
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error calling ClassifyPatientRisk: {str(e)}")
        return False

def calculate_patient_age(birth_date):
    """Call the CalculatePatientAge function"""
    if not birth_date:
        return None
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Convert birth_date to string if it's a date object
        if isinstance(birth_date, datetime):
            birth_date_str = birth_date.strftime('%Y-%m-%d')
        else:
            birth_date_str = str(birth_date)
            
        query = f"SELECT dbo.CalculatePatientAge('{birth_date_str}') AS age"
        cursor.execute(query)
        result = cursor.fetchone()
        age = result[0] if result else None
        cursor.close()
        conn.close()
        return age
    except Exception as e:
        logger.error(f"Error calling CalculatePatientAge: {str(e)}")
        return None 