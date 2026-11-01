"""
Simple test script to check for import errors in app.py
"""

try:
    # Try importing from app.py
    print("Importing app module...")
    import app
    print("Successfully imported app module!")
except Exception as e:
    print(f"Error importing app module: {str(e)}")
    import traceback
    traceback.print_exc()

print("Test script completed.") 