"""
Standalone test script to create SQL functions without depending on Flask app
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
        print(f"✅ Successfully executed {description}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error executing {description}: {str(e)}")
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

def test_age_calculation():
    """Test the CalculatePatientAge function"""
    test_date = "1990-01-01"  # Example date
    sql = f"SELECT dbo.CalculatePatientAge('{test_date}') AS age"
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        age = result[0] if result else None
        print(f"✅ Testing CalculatePatientAge: A person born on {test_date} is {age} years old")
        cursor.close()
        conn.close()
        return age
    except Exception as e:
        print(f"❌ Error testing CalculatePatientAge: {str(e)}")
        return None

if __name__ == "__main__":
    print("\nStandalone SQL Function Test\n")
    
    # Create and test function
    if create_age_calculation_function():
        age = test_age_calculation()
        if age is not None:
            print(f"\nTest successful! Function is working correctly.")
        else:
            print(f"\nTest failed! Function could not be executed.")
    else:
        print(f"\nTest failed! Function could not be created.") 