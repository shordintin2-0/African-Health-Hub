"""
Minimal test script to check database connection and SQL function existence
"""
import pyodbc
import sys

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

print("Minimal test script for African Health Hub SQL functions")
print(f"Connecting to: {server}, Database: {database}")

try:
    # Test connection
    conn = pyodbc.connect(connection_string)
    print("✅ Successfully connected to the database!")
    
    # Check if functions exist
    cursor = conn.cursor()
    
    # Check CalculatePatientAge function
    cursor.execute("SELECT OBJECT_ID('CalculatePatientAge', 'FN')")
    result = cursor.fetchone()
    if result and result[0]:
        print("✅ CalculatePatientAge function exists")
        
        # Test the function
        cursor.execute("SELECT dbo.CalculatePatientAge('1990-01-01') AS age")
        result = cursor.fetchone()
        if result:
            print(f"   Age calculation test: A person born on 1990-01-01 is {result[0]} years old")
    else:
        print("❌ CalculatePatientAge function does NOT exist")
    
    # Check GetPatientAppointments procedure
    cursor.execute("SELECT OBJECT_ID('GetPatientAppointments', 'P')")
    result = cursor.fetchone()
    if result and result[0]:
        print("✅ GetPatientAppointments procedure exists")
    else:
        print("❌ GetPatientAppointments procedure does NOT exist")
    
    # Check ClassifyPatientRisk procedure
    cursor.execute("SELECT OBJECT_ID('ClassifyPatientRisk', 'P')")
    result = cursor.fetchone()
    if result and result[0]:
        print("✅ ClassifyPatientRisk procedure exists")
    else:
        print("❌ ClassifyPatientRisk procedure does NOT exist")
    
    # Close resources
    cursor.close()
    conn.close()
    
    print("\nTest completed successfully!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    sys.exit(1) 