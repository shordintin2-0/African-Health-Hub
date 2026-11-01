import pyodbc
from sqlalchemy import create_engine, text
import logging

# Set up logging
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

def test_connection():
    try:
        # Test direct pyodbc connection
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        logger.info("✅ Successfully connected to SQL Server via pyodbc!")

        # Test SQL functions
        logger.info("Testing SQL functions...")
        
        # Test CalculatePatientAge
        cursor.execute("SELECT dbo.CalculatePatientAge('1990-01-01') AS Age")
        age = cursor.fetchone()
        logger.info(f"CalculatePatientAge test result: {age[0] if age else 'Function not found'}")

        # Test if triggers exist
        cursor.execute("""
            SELECT name FROM sys.triggers 
            WHERE name IN ('UpdateLastModified', 'AuditMedicalRecordsChanges')
        """)
        triggers = cursor.fetchall()
        logger.info(f"Found triggers: {[t[0] for t in triggers]}")

        # Test if stored procedures exist
        cursor.execute("""
            SELECT name FROM sys.procedures 
            WHERE name IN ('GetPatientAppointments', 'ClassifyPatientRisk')
        """)
        procedures = cursor.fetchall()
        logger.info(f"Found procedures: {[p[0] for p in procedures]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    test_connection() 