from african_health_hub_flask.app import app, db, create_test_accounts
import sys

def init_database():
    with app.app_context():
        try:
            # Drop existing tables
            db.drop_all()
            print("Existing tables dropped")
            
            # Create tables
            db.create_all()
            print("New tables created")
            
            # Create test accounts
            create_test_accounts()
            print("Test accounts created")
            
            print("Database initialization completed successfully!")
            return True
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 