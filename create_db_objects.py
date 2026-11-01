import pyodbc
import logging
from pathlib import Path

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

def create_database_objects():
    try:
        # Connect to the database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        logger.info("✅ Connected to database")

        # Read the SQL script
        sql_file = Path(__file__).parent / 'sql_functions.sql'
        with open(sql_file, 'r') as f:
            sql_script = f.read()

        # Split the script into individual statements
        statements = sql_script.split('GO')

        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                    conn.commit()
                    logger.info(f"✅ Successfully executed:\n{statement[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Error executing statement:\n{statement[:100]}...\nError: {str(e)}")

        logger.info("✅ All database objects created successfully")
        
        # Verify the objects were created
        cursor.execute("""
            SELECT 'Functions' as type, name 
            FROM sys.objects 
            WHERE type_desc = 'SQL_SCALAR_FUNCTION'
            UNION ALL
            SELECT 'Triggers', name 
            FROM sys.triggers
            UNION ALL
            SELECT 'Procedures', name 
            FROM sys.procedures
            ORDER BY type, name
        """)
        
        results = cursor.fetchall()
        logger.info("\nCreated objects:")
        current_type = None
        for row in results:
            if current_type != row[0]:
                current_type = row[0]
                logger.info(f"\n{current_type}:")
            logger.info(f"  - {row[1]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    create_database_objects() 