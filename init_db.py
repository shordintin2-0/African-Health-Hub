from datetime import datetime
from app import app, db
from models.user import User
from models.patient import Patient
from models.medical_staff import MedicalStaff
from models.security_audit import SecurityAudit

def init_db():
    with app.app_context():
        # Drop all tables to handle circular dependencies
        db.drop_all()
        
        # Create tables
        db.create_all()
        
        # Create test users if they don't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@africanhealthhub.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        if not User.query.filter_by(username='staff').first():
            # Create medical staff record
            staff_member = MedicalStaff(
                first_name='John',
                last_name='Doe',
                specialization='General Practice',
                contact_number='123-456-7890',
                email='john.doe@africanhealthhub.com',
                hire_date=datetime.utcnow().date(),
                status='Active'
            )
            db.session.add(staff_member)
            db.session.flush()  # Get the staff_id
            
            staff_user = User(
                username='staff',
                email='staff@africanhealthhub.com',
                role='staff',
                staff_id=staff_member.staff_id,
                is_active=True
            )
            staff_user.set_password('staff123')
            db.session.add(staff_user)
        
        if not User.query.filter_by(username='patient').first():
            # Create patient record
            patient = Patient(
                first_name='Jane',
                last_name='Smith',
                date_of_birth=datetime(1990, 1, 1).date(),
                gender='F',
                contact_number='098-765-4321',
                email='jane.smith@example.com',
                address='123 Main St',
                medical_history='No significant medical history',
                risk_level='Low'
            )
            db.session.add(patient)
            db.session.flush()  # Get the patient_id
            
            patient_user = User(
                username='patient',
                email='patient@example.com',
                role='patient',
                patient_id=patient.patient_id,
                is_active=True
            )
            patient_user.set_password('patient123')
            db.session.add(patient_user)
        
        try:
            db.session.commit()
            print("Database initialized with test users!")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    init_db()
