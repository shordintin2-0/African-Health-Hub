from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
from datetime import datetime, timedelta
import logging
import urllib.parse
import traceback
import secrets
import uuid
import random
import string
from sqlalchemy import or_
from sqlalchemy import cast
from sqlalchemy import String
from sqlalchemy import func

# Initialize Flask app and logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key in production

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

# Test direct pyodbc connection first
try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.close()
    conn.close()
    logger.info("✅ Successfully connected to SQL Server via pyodbc!")
except Exception as e:
    logger.error(f"❌ Error connecting to database via pyodbc: {str(e)}")
    traceback.print_exc()
    raise

# URL encode the connection string for SQLAlchemy
params = urllib.parse.quote_plus(connection_string)

# Set up SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import after creating app and db to avoid circular imports
from database_functions import initialize_database_functions, get_patient_appointments, classify_patient_risk, calculate_patient_age

# Helper function to log security events
def log_security_event(user_id, action, action_details, status='Success'):
    """
    Helper function to create security audit logs
    
    Args:
        user_id: ID of the user performing the action
        action: Type of action performed
        action_details: Detailed description of the action
        status: Status of the action (default: 'Success')
    """
    try:
        new_audit = SecurityAudit(
            user_id=user_id,
            action=action,
            action_details=action_details,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            status=status
        )
        db.session.add(new_audit)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating security audit log: {str(e)}")
        return False

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users181'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # Increased length for password hash
    role = db.Column(db.String(20), nullable=False)  # admin, staff, patient
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    __tablename__ = 'patients181'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users181.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))

class MedicalStaff(db.Model):
    __tablename__ = 'medical_staff181'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users181.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200), nullable=True)
    years_of_experience = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('staff_profile', uselist=False))

class Appointment(db.Model):
    __tablename__ = 'appointments181'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients181.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('medical_staff181.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    patient = db.relationship('Patient', backref='appointments')
    staff = db.relationship('MedicalStaff', backref='appointments')

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records181'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients181.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('medical_staff181.id'), nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)
    treatment = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    record_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    patient = db.relationship('Patient', backref='medical_records')
    staff = db.relationship('MedicalStaff', backref='medical_records')

class SecurityAudit(db.Model):
    __tablename__ = 'security_audit181'
    audit_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users181.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    action_details = db.Column(db.Text, nullable=True)
    action_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Success')
    user = db.relationship('User', backref='audit_logs')

# Password reset token model
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens181'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users181.id'), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='reset_tokens')

class PublicHealthResource(db.Model):
    __tablename__ = 'public_health_resources181'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # Article, Video, Document
    target_audience = db.Column(db.String(50), nullable=True)  # General, Patients, Medical Staff
    is_featured = db.Column(db.Boolean, default=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class VideoConsultation(db.Model):
    __tablename__ = 'video_consultations181'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments181.id'), nullable=False)
    meeting_link = db.Column(db.String(255), nullable=False)
    meeting_id = db.Column(db.String(50), nullable=False)
    passcode = db.Column(db.String(20), nullable=True)
    scheduled_start = db.Column(db.DateTime, nullable=False)
    scheduled_end = db.Column(db.DateTime, nullable=False)
    actual_start = db.Column(db.DateTime, nullable=True)
    actual_end = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')  # Scheduled, In Progress, Completed, Cancelled
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users181.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    appointment = db.relationship('Appointment', backref='video_consultations')
    creator = db.relationship('User', foreign_keys=[created_by])

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return redirect(url_for('dashboard'))

@app.route('/patients')
@login_required
def patients():
    return redirect(url_for('staff_patients'))

@app.route('/medical_staff')
@login_required
def medical_staff():
    return redirect(url_for('admin_users'))

@app.route('/add_patient')
@login_required
def add_patient():
    return redirect(url_for('staff_patients'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Enhanced debug logging
        print(f"Login attempt for username: {username}, password: {password[:2]}***")
        logger.info(f"Login attempt for username: {username}")
        
        # Get the user first
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Log user details for debugging
            print(f"User found: ID={user.id}, Username={user.username}, Role={user.role}, Active={user.is_active}")
            logger.info(f"User found: {user.username}, role: {user.role}, active: {user.is_active}")
            
            # Check password and ensure user is active
            if user.check_password(password) and user.is_active:
                # Print the actual and expected password hashes for debugging
                print(f"Password valid for {username}. Logging in.")
                login_user(user)
                logger.info(f"User {username} successfully logged in")
                
                # Create audit log
                try:
                    audit = SecurityAudit(
                        user_id=user.id,
                        action='login',
                        action_details='User logged in successfully',
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                    db.session.add(audit)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error creating login audit: {str(e)}")
                    db.session.rollback()
                
                return redirect(url_for('dashboard'))
            else:
                # Check whether the password check or active check failed
                if not user.check_password(password):
                    print(f"❌ Password check failed for user: {username}")
                    logger.warning(f"Password check failed for user: {username}")
                if not user.is_active:
                    print(f"❌ User account not active: {username}")
                    logger.warning(f"User account not active: {username}")
                
                # If we had a password that didn't match, try with a default test password
                test_password = f"{username}123"  # e.g., admin123, patient123, staff123
                if password != test_password:
                    print(f"Attempting with default test password pattern ({username}123)...")
                    if user.check_password(test_password):
                        print(f"✅ Default test password works! User should use: {test_password}")
                        flash(f'Try the default password: {test_password}', 'info')
        else:
            print(f"❌ User not found: {username}")
            logger.warning(f"User not found: {username}")
            
            # Check if the username is one of our expected test accounts
            if username in ['admin', 'patient', 'staff']:
                print(f"This is a standard test account name. It should exist. Creating it now...")
                # Create the test account since it should exist
                create_test_accounts()
                flash(f'Test account "{username}" has been created. Try logging in with password: {username}123', 'info')
                return redirect(url_for('login'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    audit = SecurityAudit(
        user_id=current_user.id,
        action='logout',
        action_details='User logged out',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(audit)
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'staff':
        return redirect(url_for('staff_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))

    users_count = db.session.query(User).count()
    patients_count = db.session.query(Patient).count()
    staff_count = db.session.query(MedicalStaff).count()

    # Get recent audit logs
    recent_logs = (
        db.session.query(SecurityAudit)
        .order_by(SecurityAudit.action_date.desc())
        .limit(10)
        .all()
    )

    return render_template('admin_dashboard.html',
                         users_count=users_count,
                         patients_count=patients_count,
                         staff_count=staff_count,
                         recent_logs=recent_logs)

@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    """Staff dashboard route."""
    if current_user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    # Get staff's appointments for today
    today = datetime.now().date()
    today_appointments = Appointment.query.filter(
        Appointment.staff_id == current_user.id,
        func.cast(Appointment.appointment_date, db.Date) == today
    ).order_by(Appointment.appointment_date).all()
    
    # Get today's video consultations
    today_consultations = VideoConsultation.query.join(
        Appointment, VideoConsultation.appointment_id == Appointment.id
    ).filter(
        Appointment.staff_id == current_user.id,
        func.cast(VideoConsultation.scheduled_start, db.Date) == today,
        VideoConsultation.status.in_(['Scheduled', 'In Progress'])
    ).order_by(VideoConsultation.scheduled_start).all()
    
    # Add patient details to each consultation
    for consultation in today_consultations:
        appointment = Appointment.query.get(consultation.appointment_id)
        consultation.patient = Patient.query.get(appointment.patient_id)
    
    return render_template('staff_dashboard.html', 
                           staff=current_user,
                           today_appointments=today_appointments,
                           today_consultations=today_consultations)

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard route."""
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    # Get patient's appointments
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    
    # Get recent medical records
    medical_records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.record_date.desc()).limit(5).all()
    
    # Get upcoming video consultations
    upcoming_consultations = VideoConsultation.query.join(
        Appointment, VideoConsultation.appointment_id == Appointment.id
    ).filter(
        Appointment.patient_id == current_user.id,
        VideoConsultation.status.in_(['Scheduled', 'In Progress']),
        VideoConsultation.scheduled_start > datetime.now() - timedelta(hours=1)
    ).order_by(VideoConsultation.scheduled_start).limit(3).all()
    
    # Add staff details to each consultation
    for consultation in upcoming_consultations:
        appointment = Appointment.query.get(consultation.appointment_id)
        consultation.staff = MedicalStaff.query.get(appointment.staff_id)
    
    # Get all doctors (staff) for appointment scheduling
    doctors = MedicalStaff.query.all()
    
    return render_template('patient_dashboard.html', 
                           profile=current_user,
                           appointments=appointments,
                           medical_records=medical_records,
                           upcoming_consultations=upcoming_consultations,
                           doctors=doctors)

@app.route('/patient/schedule_appointment', methods=['POST'])
@login_required
def patient_schedule_appointment():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get form data
    appointment_date = request.form.get('appointment_date')
    staff_id = request.form.get('staff_id')
    appointment_type = request.form.get('appointment_type')
    notes = request.form.get('notes')
    
    # Validate form data
    if not appointment_date or not staff_id or not appointment_type:
        flash('Please fill out all required fields', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    try:
        # Get patient profile
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if not patient:
            flash('Patient profile not found', 'danger')
            return redirect(url_for('patient_dashboard'))
        
        # Create new appointment
        new_appointment = Appointment(
            patient_id=patient.id,
            staff_id=staff_id,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M'),
            appointment_type=appointment_type,
            status='Scheduled',
            notes=notes
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Log the action
        audit = SecurityAudit(
            user_id=current_user.id,
            action='create_appointment',
            action_details=f'Appointment scheduled for {appointment_date}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Appointment scheduled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling appointment: {str(e)}', 'danger')
        print(f"Error scheduling appointment: {str(e)}")
        
    return redirect(url_for('patient_dashboard'))

@app.route('/profile')
@login_required
def profile():
    if current_user.role == 'patient':
        profile_data = Patient.query.filter_by(user_id=current_user.id).first()
        return render_template('profile.html', profile=profile_data, role='patient')
    elif current_user.role == 'staff':
        profile_data = MedicalStaff.query.filter_by(user_id=current_user.id).first()
        return render_template('profile.html', profile=profile_data, role='staff')
    else:
        profile_data = current_user
        return render_template('profile.html', profile=profile_data, role='admin')

# Admin routes
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def admin_add_user():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')
    
    if not username or not email or not password or not role:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin_users'))
    
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash('User added successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    role = request.form.get('role')
    is_active = request.form.get('is_active') == 'on'
    
    if not username or not role:
        flash('Username and role are required.', 'danger')
        return redirect(url_for('admin_users'))
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user_id:
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin_users'))
    
    user.username = username
    user.role = role
    user.is_active = is_active
    db.session.commit()
    
    flash('User updated successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    if user_id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/audit_logs')
@login_required
def audit_logs():
    if current_user.role != 'admin' and current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all logs for admin, or only relevant logs for staff
    if current_user.role == 'admin':
        logs = SecurityAudit.query.order_by(SecurityAudit.action_date.desc()).all()
    else:
        # For staff, only show logs related to their patients
        staff_profile = MedicalStaff.query.filter_by(user_id=current_user.id).first()
        if not staff_profile:
            flash('Staff profile not found', 'danger')
            return redirect(url_for('dashboard'))
        
        # Get all patient IDs associated with this staff member
        patient_appointments = Appointment.query.filter_by(staff_id=staff_profile.id).all()
        patient_ids = [appt.patient_id for appt in patient_appointments]
        patient_users = Patient.query.filter(Patient.id.in_(patient_ids)).all()
        patient_user_ids = [patient.user_id for patient in patient_users]
        
        # Get logs for these patients
        logs = SecurityAudit.query.filter(
            (SecurityAudit.user_id.in_(patient_user_ids))
        ).order_by(SecurityAudit.action_date.desc()).all()
    
    return render_template('audit_logs.html', logs=logs, now=datetime.now)

# Keep the old route for backward compatibility, redirecting to the new one
@app.route('/admin/audit_logs')
@login_required
def admin_audit_logs():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    return redirect(url_for('audit_logs'))

@app.route('/admin/users/<int:user_id>/toggle_privilege', methods=['POST'])
@login_required
def admin_toggle_privilege(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    if user_id == current_user.id:
        flash('Cannot modify your own privileges.', 'danger')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    is_active = request.form.get('is_active') == 'true'
    
    # Toggle the active status
    user.is_active = is_active
    
    # Log the action in security audit
    action_details = f"{'Granted' if is_active else 'Revoked'} privileges for user {user.username} (ID: {user.id})"
    new_audit = SecurityAudit(
        user_id=current_user.id,
        action="toggle_user_privilege",
        action_details=action_details,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        status='Success'
    )
    db.session.add(new_audit)
    
    try:
        db.session.commit()
        flash(f"User privileges {'granted' if is_active else 'revoked'} successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing user privileges: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/patients')
@login_required
def admin_patients():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    patients = Patient.query.all()
    return render_template('admin/patients.html', patients=patients)

@app.route('/admin/medical_staff')
@login_required
def admin_medical_staff():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = MedicalStaff.query.all()
    return render_template('admin/medical_staff.html', staff=staff)

# Staff routes
@app.route('/staff/patients')
@login_required
def staff_patients():
    if current_user.role != 'staff':
        flash('Access denied')
        return redirect(url_for('dashboard'))
    patients = Patient.query.all()
    return render_template('staff/patients.html', patients=patients)

@app.route('/staff/appointments')
@login_required
def staff_appointments():
    if current_user.role != 'staff':
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    staff_profile = MedicalStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_profile:
        flash('Staff profile not found', 'danger')
        return redirect(url_for('dashboard'))
    
    appointments = Appointment.query.filter_by(staff_id=staff_profile.id).all()
    
    # Get video consultations for these appointments
    appointment_ids = [a.id for a in appointments]
    video_consultations = {}
    if appointment_ids:
        consultations = VideoConsultation.query.filter(VideoConsultation.appointment_id.in_(appointment_ids)).all()
        video_consultations = {c.appointment_id: c for c in consultations}
    
    return render_template('staff/appointments.html', 
                          appointments=appointments, 
                          video_consultations=video_consultations,
                          now=datetime.now())

@app.route('/staff/add_medical_record', methods=['POST'])
@login_required
def staff_add_medical_record():
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))

    # Get form data
    patient_id = request.form.get('patient_id')
    appointment_id = request.form.get('appointment_id')
    diagnosis = request.form.get('diagnosis')
    treatment = request.form.get('treatment')
    prescription = request.form.get('prescription')
    notes = request.form.get('notes')
    record_date = request.form.get('record_date')
    
    # Validate data
    if not patient_id or not diagnosis or not treatment:
        flash('Required fields are missing', 'danger')
        return redirect(url_for('staff_dashboard'))
    
    try:
        # Create new medical record
        new_record = MedicalRecord(
            patient_id=patient_id,
            staff_id=current_user.staff_profile.id,
            diagnosis=diagnosis,
            treatment=treatment,
            prescription=prescription,
            notes=notes,
            record_date=datetime.strptime(record_date, '%Y-%m-%dT%H:%M') if record_date else datetime.now()
        )
        db.session.add(new_record)
        
        # If this record is associated with an appointment, update the appointment status
        if appointment_id and appointment_id != 'None':
            appointment = Appointment.query.get(appointment_id)
            if appointment:
                appointment.status = 'Completed'
                
        db.session.commit()
        
        # Log the action
        audit = SecurityAudit(
            user_id=current_user.id,
            action='create_medical_record',
            action_details=f'Medical record created for patient ID {patient_id}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Medical record added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding medical record: {str(e)}', 'danger')
        print(f'Error adding medical record: {str(e)}')
    
    return redirect(url_for('staff_dashboard'))

@app.route('/staff/add_appointment', methods=['POST'])
@login_required
def staff_add_appointment():
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get form data
    patient_id = request.form.get('patient_id')
    appointment_date = request.form.get('appointment_date')
    appointment_type = request.form.get('appointment_type')
    notes = request.form.get('notes')
    
    # Validate form data
    if not patient_id or not appointment_date or not appointment_type:
        flash('Please fill out all required fields', 'danger')
        return redirect(url_for('staff_dashboard'))
    
    try:
        # Get staff profile
        staff_profile = MedicalStaff.query.filter_by(user_id=current_user.id).first()
        if not staff_profile:
            flash('Staff profile not found', 'danger')
            return redirect(url_for('staff_dashboard'))
        
        # Create new appointment
        new_appointment = Appointment(
            patient_id=patient_id,
            staff_id=staff_profile.id,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M'),
            appointment_type=appointment_type,
            status='Scheduled',
            notes=notes
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Log the action
        audit = SecurityAudit(
            user_id=current_user.id,
            action='create_appointment',
            action_details=f'Appointment scheduled for patient ID {patient_id}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Appointment scheduled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error scheduling appointment: {str(e)}', 'danger')
        print(f"Error scheduling appointment: {str(e)}")
        
    return redirect(url_for('staff_dashboard'))

# Patient routes
@app.route('/patient/appointments')
@login_required
def patient_appointments():
    if current_user.role != 'patient':
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    # Get patient appointments
    patient_profile = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient_profile:
        flash('Patient profile not found', 'danger')
        return redirect(url_for('dashboard'))
    
    appointments = Appointment.query.filter_by(patient_id=patient_profile.id).all()
    
    # Get video consultations for these appointments
    appointment_ids = [a.id for a in appointments]
    video_consultations = {}
    if appointment_ids:
        consultations = VideoConsultation.query.filter(VideoConsultation.appointment_id.in_(appointment_ids)).all()
        video_consultations = {c.appointment_id: c for c in consultations}
    
    # Get all doctors (staff) for appointment scheduling
    doctors = MedicalStaff.query.all()
    
    return render_template('patient/appointments.html', 
                          appointments=appointments, 
                          video_consultations=video_consultations,
                          doctors=doctors,
                          now=datetime.now())

@app.route('/patient/medical_records')
@login_required
def patient_medical_records():
    if current_user.role != 'patient':
        flash('Access denied')
        return redirect(url_for('dashboard'))
    records = MedicalRecord.query.filter_by(patient_id=current_user.patient_profile.id).all()
    return render_template('patient/medical_records.html', records=records)

@app.route('/request_appointment', methods=['POST'])
@login_required
def request_appointment():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Get form data
        staff_id = request.form.get('staff_id')
        appointment_date = request.form.get('appointment_date')
        appointment_type = request.form.get('appointment_type')
        notes = request.form.get('notes')
        
        # Validate form data
        if not staff_id or not appointment_date or not appointment_type:
            flash('Please fill out all required fields', 'danger')
            return redirect(url_for('patient_appointments'))
        
        # Create new appointment
        new_appointment = Appointment(
            patient_id=current_user.patient_profile.id,
            staff_id=staff_id,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M'),
            appointment_type=appointment_type,
            status='Scheduled',
            notes=notes
        )
        
        db.session.add(new_appointment)
        db.session.commit()
        
        # Log the action
        audit = SecurityAudit(
            user_id=current_user.id,
            action='request_appointment',
            action_details=f'Appointment requested with staff ID {staff_id}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Appointment requested successfully. You will receive a confirmation soon.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error requesting appointment: {str(e)}', 'danger')
        logger.error(f"Error requesting appointment: {str(e)}")
        
    return redirect(url_for('patient_appointments'))

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Get the appointment
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Verify that this appointment belongs to the current patient
        if appointment.patient_id != current_user.patient_profile.id:
            flash('You can only cancel your own appointments', 'danger')
            return redirect(url_for('patient_appointments'))
        
        # Check if the appointment can be cancelled (not past or already cancelled)
        if appointment.appointment_date < datetime.now():
            flash('Cannot cancel past appointments', 'danger')
            return redirect(url_for('patient_appointments'))
            
        if appointment.status == 'Cancelled':
            flash('This appointment is already cancelled', 'warning')
            return redirect(url_for('patient_appointments'))
        
        # Update appointment status
        appointment.status = 'Cancelled'
        appointment.notes = f"{appointment.notes or ''}\n\nCancelled on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Reason: {request.form.get('reason', 'Not provided')}"
        
        # Cancel associated video consultation if it exists
        video_consultation = VideoConsultation.query.filter_by(appointment_id=appointment.id).first()
        if video_consultation and video_consultation.status in ['Scheduled']:
            video_consultation.status = 'Cancelled'
        
        db.session.commit()
        
        # Log the action
        audit = SecurityAudit(
            user_id=current_user.id,
            action='cancel_appointment',
            action_details=f'Appointment ID {appointment_id} cancelled',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Appointment cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling appointment: {str(e)}', 'danger')
        logger.error(f"Error cancelling appointment: {str(e)}")
        
    return redirect(url_for('patient_appointments'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = 'patient'  # Default role for self-registration is patient

        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Create associated patient record
            new_patient = Patient(
                user_id=new_user.id,
                first_name=username,  # Initially set name same as username
                last_name='',
                email=email
            )
            db.session.add(new_patient)
            db.session.commit()
            
            # Log the registration
            audit = SecurityAudit(
                user_id=new_user.id,
                action='register',
                action_details='New patient registration',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            app.logger.error(f'Registration error: {str(e)}')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/volunteer')
def volunteer():
    return render_template('volunteer.html')

@app.route('/donate')
def donate():
    return render_template('donate.html')

@app.route('/volunteer_register', methods=['POST'])
def volunteer_register():
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            profession = request.form.get('profession')
            country = request.form.get('country')
            volunteer_type = request.form.get('volunteer_type')
            availability = request.form.get('availability')
            motivation = request.form.get('motivation')
            skills = request.form.get('skills')
            
            # Log the volunteer application
            app.logger.info(f"New volunteer application received from {first_name} {last_name}, {email}")
            
            # In a real application, you would save this to a database
            # and set up email notifications
            
            # For now, we'll just flash a success message
            flash('Thank you for your volunteer application! We will contact you soon.', 'success')
            return redirect(url_for('volunteer'))
        
        except Exception as e:
            app.logger.error(f"Error processing volunteer application: {str(e)}")
            flash('There was an error processing your application. Please try again.', 'danger')
            return redirect(url_for('volunteer'))

@app.route('/process_donation', methods=['POST'])
def process_donation():
    if request.method == 'POST':
        try:
            # Get form data
            donation_amount = request.form.get('donation_amount')
            if donation_amount == 'custom':
                donation_amount = request.form.get('custom_amount')
            
            donation_frequency = request.form.get('donation_frequency')
            donor_name = request.form.get('donor_name')
            donor_email = request.form.get('donor_email')
            initiative = request.form.get('initiative', 'General')
            
            # Process payment (this would connect to a payment gateway in production)
            # For demonstration purposes, we're just logging the donation
            
            app.logger.info(f"New donation received: ${donation_amount} ({donation_frequency}) from {donor_name} for {initiative}")
            
            # Create a security audit entry
            if current_user.is_authenticated:
                new_audit = SecurityAudit(
                    user_id=current_user.id,
                    action=f"Made a ${donation_amount} donation to {initiative}",
                    timestamp=datetime.now()
                )
                db.session.add(new_audit)
                db.session.commit()
            
            # Send receipt if requested
            if request.form.get('tax_receipt'):
                # In a real application, this would send an email
                app.logger.info(f"Tax receipt requested for donation from {donor_email}")
            
            # Subscribe to newsletter if requested
            if request.form.get('newsletter'):
                app.logger.info(f"Newsletter subscription requested for {donor_email}")
            
            flash('Thank you for your generous donation!', 'success')
            return redirect(url_for('donate'))
            
        except Exception as e:
            app.logger.error(f"Error processing donation: {str(e)}")
            flash('There was an error processing your donation. Please try again.', 'danger')
            return redirect(url_for('donate'))

def create_test_accounts():
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@africanhealthhub.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin account created')
        logger.info("Admin account created")

    # Create test patient if it doesn't exist
    patient = User.query.filter_by(username='patient').first()
    if not patient:
        patient = User(
            username='patient',
            email='patient@test.com',
            role='patient',
            is_active=True
        )
        patient.set_password('patient123')
        db.session.add(patient)
        db.session.commit()

        try:
            patient_profile = Patient(
                user_id=patient.id,
                first_name='John',
                last_name='Doe',
                email='patient@test.com',
                gender='Male',
                phone='+233 123 456 789'
            )
            db.session.add(patient_profile)
            db.session.commit()
            print('Patient account created')
            logger.info("Patient account created")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating patient profile: {str(e)}")
            logger.error(f"Error creating patient profile: {str(e)}")

    # Create test staff if it doesn't exist
    staff = User.query.filter_by(username='staff').first()
    if not staff:
        staff = User(
            username='staff',
            email='staff@test.com',
            role='staff',
            is_active=True
        )
        staff.set_password('staff123')
        db.session.add(staff)
        db.session.commit()

        try:
            staff_profile = MedicalStaff(
                user_id=staff.id,
                first_name='Jane',
                last_name='Smith',
                email='staff@test.com',
                phone='+233 987 654 321',
                specialization='General Medicine'
            )
            db.session.add(staff_profile)
            db.session.commit()
            print('Staff account created')
            logger.info("Staff account created")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating staff profile: {str(e)}")
            logger.error(f"Error creating staff profile: {str(e)}")
    
    return True

def create_sample_health_resources():
    """Create sample health resources if none exist"""
    # Check if we already have resources
    if PublicHealthResource.query.count() > 0:
        return
    
    # Create sample resources
    resources = [
        {
            'title': 'COVID-19 Prevention Guidelines',
            'description': 'Latest guidelines for COVID-19 prevention and vaccination.',
            'content': """
                <h2>COVID-19 Prevention Guidelines</h2>
                <p>This resource provides the latest information on preventing the spread of COVID-19 and vaccination recommendations.</p>
                <h3>Key Prevention Measures</h3>
                <ul>
                    <li>Get vaccinated and stay up to date with boosters</li>
                    <li>Wear a well-fitting mask in public indoor settings when transmission levels are high</li>
                    <li>Maintain good ventilation in indoor spaces</li>
                    <li>Practice regular handwashing with soap and water</li>
                    <li>Stay home when sick and get tested</li>
                </ul>
                <h3>Vaccination Information</h3>
                <p>COVID-19 vaccines are safe, effective, and free. They help protect against severe illness, hospitalization, and death.</p>
                <p>Current recommendations include staying up to date with boosters as they become available.</p>
            """,
            'resource_type': 'Article',
            'target_audience': 'General',
            'is_featured': True
        },
        {
            'title': 'Malaria Prevention Tips',
            'description': 'Essential information for preventing malaria in high-risk areas.',
            'content': """
                <h2>Malaria Prevention</h2>
                <p>Malaria is a serious and sometimes fatal disease transmitted by mosquitoes. This guide provides key prevention strategies.</p>
                <h3>Prevention Measures</h3>
                <ul>
                    <li>Sleep under insecticide-treated bed nets</li>
                    <li>Use insect repellent containing DEET, IR3535 or Icaridin</li>
                    <li>Wear long-sleeved shirts and pants when outdoors, especially at night</li>
                    <li>Take prescribed antimalarial medications if traveling to high-risk areas</li>
                    <li>Eliminate standing water where mosquitoes breed</li>
                </ul>
                <h3>Symptoms to Watch For</h3>
                <p>Early symptoms of malaria include fever, headache, chills, and vomiting. Seek medical attention immediately if you experience these symptoms, especially after visiting a malaria-endemic area.</p>
            """,
            'resource_type': 'Article',
            'target_audience': 'General',
            'is_featured': True
        },
        {
            'title': 'Healthy Eating Guidelines',
            'description': 'Nutrition guidelines for maintaining a balanced diet and healthy lifestyle.',
            'content': """
                <h2>Healthy Eating Guidelines</h2>
                <p>A balanced diet is essential for good health and well-being. This guide provides key principles for healthy eating.</p>
                <h3>Key Dietary Recommendations</h3>
                <ul>
                    <li>Eat a variety of foods from all food groups</li>
                    <li>Include plenty of fruits and vegetables</li>
                    <li>Choose whole grains over refined grains</li>
                    <li>Include lean proteins such as fish, poultry, beans, and nuts</li>
                    <li>Limit processed foods, sugars, and saturated fats</li>
                    <li>Stay hydrated by drinking plenty of water</li>
                </ul>
                <h3>Portion Control</h3>
                <p>Pay attention to portion sizes to avoid overeating. Use smaller plates and listen to your body's hunger cues.</p>
                <h3>Local Food Recommendations</h3>
                <p>Incorporate local, seasonal foods in your diet for maximum nutrition and to support local agriculture.</p>
            """,
            'resource_type': 'Article',
            'target_audience': 'General',
            'is_featured': True
        },
        {
            'title': 'Hypertension Management',
            'description': 'Guidelines for managing high blood pressure through lifestyle changes and medication.',
            'content': """
                <h2>Managing Hypertension</h2>
                <p>Hypertension, or high blood pressure, is a common condition that can lead to serious health problems if left untreated.</p>
                <h3>Lifestyle Modifications</h3>
                <ul>
                    <li>Maintain a healthy weight</li>
                    <li>Follow a low-sodium, heart-healthy diet</li>
                    <li>Exercise regularly (aim for 150 minutes of moderate activity per week)</li>
                    <li>Limit alcohol consumption</li>
                    <li>Avoid tobacco products</li>
                    <li>Manage stress through relaxation techniques</li>
                </ul>
                <h3>Medication Adherence</h3>
                <p>If prescribed medication, take it exactly as directed. Never stop taking medication without consulting your healthcare provider.</p>
                <h3>Blood Pressure Monitoring</h3>
                <p>Regular monitoring at home can help track your progress and alert you to any concerning changes.</p>
            """,
            'resource_type': 'Guide',
            'target_audience': 'Patients',
            'is_featured': False
        },
        {
            'title': 'Diabetes Care Essentials',
            'description': 'Important information for managing diabetes and preventing complications.',
            'content': """
                <h2>Diabetes Care Essentials</h2>
                <p>Effective diabetes management can help prevent complications and improve quality of life.</p>
                <h3>Key Management Strategies</h3>
                <ul>
                    <li>Monitor blood glucose levels regularly</li>
                    <li>Take medications as prescribed</li>
                    <li>Follow a balanced meal plan</li>
                    <li>Engage in regular physical activity</li>
                    <li>Attend all scheduled healthcare appointments</li>
                    <li>Check feet daily for cuts, blisters, or sores</li>
                </ul>
                <h3>Hypoglycemia Awareness</h3>
                <p>Know the signs of low blood sugar: shakiness, sweating, confusion, and irritability. Always carry a fast-acting carbohydrate source.</p>
                <h3>Complication Prevention</h3>
                <p>Regular eye exams, foot care, and kidney function tests are essential for detecting and preventing diabetes-related complications.</p>
            """,
            'resource_type': 'Guide',
            'target_audience': 'Patients',
            'is_featured': False
        },
        {
            'title': 'Antibiotic Stewardship Guidelines',
            'description': 'Best practices for proper antibiotic use to prevent resistance.',
            'content': """
                <h2>Antibiotic Stewardship Guidelines</h2>
                <p>Proper use of antibiotics is crucial to prevent antibiotic resistance, a growing global health concern.</p>
                <h3>Principles of Appropriate Antibiotic Use</h3>
                <ul>
                    <li>Prescribe antibiotics only when clinically indicated</li>
                    <li>Select the appropriate antibiotic, dose, and duration</li>
                    <li>Obtain cultures before starting antibiotics when possible</li>
                    <li>Review antibiotic therapy regularly and de-escalate when appropriate</li>
                    <li>Document indication, dose, and duration for all antibiotic prescriptions</li>
                </ul>
                <h3>Common Misuses</h3>
                <p>Antibiotics are ineffective against viral infections like the common cold, most sore throats, and flu. Educate patients about appropriate use.</p>
                <h3>Resistance Prevention</h3>
                <p>Implement infection prevention measures and antimicrobial stewardship programs to reduce the development of resistant organisms.</p>
            """,
            'resource_type': 'Guide',
            'target_audience': 'Medical Staff',
            'is_featured': False
        }
    ]
    
    for resource_data in resources:
        resource = PublicHealthResource(**resource_data)
        db.session.add(resource)
    
    try:
        db.session.commit()
        print(f"Created {len(resources)} sample health resources")
        logger.info(f"Created {len(resources)} sample health resources")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample health resources: {str(e)}")
        logger.error(f"Error creating sample health resources: {str(e)}")

# Initialize database
def init_db():
    with app.app_context():
        try:
            # Test database connection
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            connection = engine.connect()
            connection.close()
            logger.info("✅ Successfully connected to SQL Server via SQLAlchemy!")
            
            # Create all tables if they don't exist
            db.create_all()
            logger.info("✅ Database tables created")
            
            # Create test accounts
            create_test_accounts()
            
            # Create sample health resources
            create_sample_health_resources()
            
            # SQL functions are assumed to be created by running sql_functions.sql in SQL Server Management Studio
            logger.info("✅ SQL functions, triggers, and stored procedures should be created manually using sql_functions.sql")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to database: {str(e)}")
            traceback.print_exc()
            raise

@app.route('/patient/profile/<int:patient_id>')
@login_required
def patient_profile(patient_id):
    # Check permissions - admin, staff, or the patient themselves
    if current_user.role not in ['admin', 'staff'] and (not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != patient_id):
        flash('You do not have permission to view this profile.', 'danger')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Get patient's appointments
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()
    
    # Get patient's medical records
    medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.record_date.desc()).all()
    
    return render_template(
        'patient_profile.html',
        patient=patient,
        appointments=appointments,
        medical_records=medical_records,
        now=datetime.now
    )

@app.route('/staff/profile/<int:staff_id>')
@login_required
def staff_profile(staff_id):
    # Check permissions - admin, or the staff member themselves
    if current_user.role not in ['admin'] and (not hasattr(current_user, 'staff_profile') or current_user.staff_profile.id != staff_id):
        flash('You do not have permission to view this profile.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = MedicalStaff.query.get_or_404(staff_id)
    
    # Get staff's appointments
    appointments = Appointment.query.filter_by(staff_id=staff_id).order_by(Appointment.appointment_date.desc()).all()
    
    # Get staff's medical records (records they've created)
    medical_records = MedicalRecord.query.filter_by(staff_id=staff_id).order_by(MedicalRecord.record_date.desc()).all()
    
    # Calculate some statistics
    total_patients = db.session.query(Patient.id).join(Appointment, Appointment.patient_id == Patient.id)\
                    .filter(Appointment.staff_id == staff_id).distinct().count()
    
    today = datetime.now().date()
    appointments_today = Appointment.query.filter_by(staff_id=staff_id)\
                         .filter(func.cast(Appointment.appointment_date, db.Date) == today).count()
    
    upcoming_appointments = Appointment.query.filter_by(staff_id=staff_id, status='Scheduled')\
                           .filter(Appointment.appointment_date > datetime.now()).count()
    
    return render_template(
        'staff_profile.html', 
        staff=staff, 
        appointments=appointments, 
        medical_records=medical_records,
        total_patients=total_patients,
        appointments_today=appointments_today,
        upcoming_appointments=upcoming_appointments,
        now=datetime.now
    )

@app.route('/admin/staff/<int:staff_id>/edit', methods=['POST'])
@login_required
def admin_edit_staff(staff_id):
    if current_user.role != 'admin':
        flash('You do not have permission to edit staff profiles.', 'danger')
        return redirect(url_for('dashboard'))
    
    staff = MedicalStaff.query.get_or_404(staff_id)
    
    try:
        # Update staff information
        staff.first_name = request.form['first_name']
        staff.last_name = request.form['last_name']
        staff.email = request.form['email']
        staff.phone = request.form['phone']
        staff.specialization = request.form['specialization']
        staff.qualification = request.form['qualification']
        
        # Handle optional fields
        if request.form.get('years_of_experience'):
            staff.years_of_experience = int(request.form['years_of_experience'])
        
        # Log the edit in the security audit
        new_audit = SecurityAudit(
            user_id=current_user.id,
            action="Edited staff profile",
            action_details=f"Edited profile for Dr. {staff.first_name} {staff.last_name} (ID: {staff.id})",
            timestamp=datetime.now()
        )
        db.session.add(new_audit)
        
        db.session.commit()
        flash(f'Profile for Dr. {staff.first_name} {staff.last_name} has been updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating staff profile: {str(e)}")
        flash(f'An error occurred while updating the profile: {str(e)}', 'danger')
    
    return redirect(url_for('staff_profile', staff_id=staff.id))

@app.route('/debug/patients')
def debug_patients():
    """Debug route to check patients in the database"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401
        
    try:
        # Get all patients
        patients = Patient.query.all()
        patients_data = []
        
        for patient in patients:
            user = User.query.get(patient.user_id)
            patients_data.append({
                "id": patient.id,
                "user_id": patient.user_id,
                "username": user.username if user else "Unknown",
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "email": patient.email,
                "gender": patient.gender,
                "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
                "address": patient.address,
                "phone": patient.phone
            })
            
        # Also get users for comparison
        users = User.query.filter_by(role='patient').all()
        users_data = []
        
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            })
            
        return jsonify({
            "patient_count": len(patients),
            "patients": patients_data,
            "patient_user_count": len(users),
            "patient_users": users_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/create_test_patients')
def create_test_patients():
    try:
        # Create additional test patients
        test_patients = [
            {
                'username': 'patient2',
                'password': 'patient123',
                'email': 'patient2@test.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'gender': 'Female',
                'phone': '+233 111 222 333'
            },
            {
                'username': 'patient3',
                'password': 'patient123',
                'email': 'patient3@test.com',
                'first_name': 'David',
                'last_name': 'Brown',
                'gender': 'Male',
                'phone': '+233 444 555 666'
            },
            {
                'username': 'patient4',
                'password': 'patient123',
                'email': 'patient4@test.com',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'gender': 'Female',
                'phone': '+233 777 888 999'
            }
        ]
        
        created_count = 0
        for p in test_patients:
            # Check if user already exists
            existing_user = User.query.filter_by(username=p['username']).first()
            if not existing_user:
                # Create user
                user = User(
                    username=p['username'],
                    email=p['email'],
                    role='patient',
                    is_active=True
                )
                user.set_password(p['password'])
                db.session.add(user)
                db.session.commit()
                
                # Create patient profile
                patient = Patient(
                    user_id=user.id,
                    first_name=p['first_name'],
                    last_name=p['last_name'],
                    email=p['email'],
                    gender=p['gender'],
                    phone=p['phone']
                )
                db.session.add(patient)
                db.session.commit()
                created_count += 1
        
        return f"Created {created_count} new test patients. <a href='/debug/patients'>View all patients</a>"
    except Exception as e:
        db.session.rollback()
        return f"Error creating test patients: {str(e)}"

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required', 'danger')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a token
            token = secrets.token_hex(32)
            expiration = datetime.now() + timedelta(hours=24)
            
            # Save token to database
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expiration
            )
            db.session.add(reset_token)
            
            # Create a security audit
            audit = SecurityAudit(
                user_id=user.id,
                action='password_reset_request',
                action_details=f'Password reset requested for email: {email}',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            # Generate reset link (in a real application, this would be emailed)
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # For demo purposes, we'll display the link
            flash(f'If an account exists with that email, a password reset link has been created: {reset_link}', 'info')
        else:
            # For security, don't reveal if the email exists or not
            flash('If an account exists with that email, a password reset link will be sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Find the token
    reset_token = PasswordResetToken.query.filter_by(token=token, is_used=False).first()
    
    # Check if token exists and is valid
    if not reset_token or reset_token.expires_at < datetime.now():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', token=token)
        
        try:
            # Update user's password
            user = User.query.get(reset_token.user_id)
            user.set_password(password)
            
            # Mark token as used
            reset_token.is_used = True
            
            # Create a security audit
            audit = SecurityAudit(
                user_id=user.id,
                action='password_reset_complete',
                action_details='Password reset completed successfully',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            flash('Your password has been updated successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during password reset: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'danger')
    
    return render_template('reset_password.html', token=token)

# Debug route for SQL functions
@app.route('/debug/sql_functions')
@login_required
def debug_sql_functions():
    """Debug route to check SQL functions, triggers and stored procedures"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"error": "Authentication required and admin privileges required"}), 401
        
    try:
        # Try to execute functions and procedures
        result = {
            "functions": {},
            "triggers": {},
            "procedures": {}
        }
        
        # Test age calculation function
        patient = Patient.query.filter(Patient.date_of_birth.isnot(None)).first()
        if patient and patient.date_of_birth:
            try:
                age = db.session.execute(
                    text("SELECT dbo.CalculatePatientAge(:birth_date) AS age"), 
                    {"birth_date": patient.date_of_birth}
                ).fetchone()
                result["functions"]["CalculatePatientAge"] = {
                    "status": "success" if age else "error",
                    "result": age[0] if age else None,
                    "patient_id": patient.id,
                    "birth_date": patient.date_of_birth.strftime('%Y-%m-%d')
                }
            except Exception as e:
                result["functions"]["CalculatePatientAge"] = {
                    "status": "error",
                    "error": str(e)
                }
                
        # Check UpdateLastModified trigger
        try:
            triggers = db.session.execute(text(
                "SELECT name, object_id, parent_object_id FROM sys.triggers WHERE name = 'UpdateLastModified'"
            )).fetchone()
            result["triggers"]["UpdateLastModified"] = {
                "status": "exists" if triggers else "not found",
                "details": dict(zip(['name', 'object_id', 'parent_object_id'], triggers)) if triggers else None
            }
        except Exception as e:
            result["triggers"]["UpdateLastModified"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check AuditMedicalRecordsChanges trigger
        try:
            triggers = db.session.execute(text(
                "SELECT name, object_id, parent_object_id FROM sys.triggers WHERE name = 'AuditMedicalRecordsChanges'"
            )).fetchone()
            result["triggers"]["AuditMedicalRecordsChanges"] = {
                "status": "exists" if triggers else "not found",
                "details": dict(zip(['name', 'object_id', 'parent_object_id'], triggers)) if triggers else None
            }
        except Exception as e:
            result["triggers"]["AuditMedicalRecordsChanges"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check GetPatientAppointments procedure
        try:
            procedures = db.session.execute(text(
                "SELECT name, object_id FROM sys.procedures WHERE name = 'GetPatientAppointments'"
            )).fetchone()
            result["procedures"]["GetPatientAppointments"] = {
                "status": "exists" if procedures else "not found",
                "details": dict(zip(['name', 'object_id'], procedures)) if procedures else None
            }
        except Exception as e:
            result["procedures"]["GetPatientAppointments"] = {
                "status": "error",
                "error": str(e)
            }
            
        # Check ClassifyPatientRisk procedure
        try:
            procedures = db.session.execute(text(
                "SELECT name, object_id FROM sys.procedures WHERE name = 'ClassifyPatientRisk'"
            )).fetchone()
            result["procedures"]["ClassifyPatientRisk"] = {
                "status": "exists" if procedures else "not found",
                "details": dict(zip(['name', 'object_id'], procedures)) if procedures else None
            }
        except Exception as e:
            result["procedures"]["ClassifyPatientRisk"] = {
                "status": "error",
                "error": str(e)
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add route to view patient age and risk assessment
@app.route('/patient/risk-assessment/<int:patient_id>')
@login_required
def patient_risk_assessment(patient_id):
    # Check permissions - admin, staff, or the patient themselves
    if current_user.role not in ['admin', 'staff'] and (not hasattr(current_user, 'patient_profile') or current_user.patient_profile.id != patient_id):
        flash('You do not have permission to view this assessment.', 'danger')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Calculate patient age using the SQL function
    patient_age = None
    if patient.date_of_birth:
        try:
            patient_age = calculate_patient_age(patient.date_of_birth)
        except Exception as e:
            logger.error(f"Error calculating patient age: {str(e)}")
            # Calculate age in Python as fallback
            today = datetime.now().date()
            patient_age = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
    
    # Get appointments using the stored procedure
    try:
        appointments = get_patient_appointments(patient_id)
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        # Fallback to regular query
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date).all()
        appointments = [{"id": a.id, "appointment_date": a.appointment_date, "appointment_type": a.appointment_type, "status": a.status} for a in appointments]
    
    # Run risk classification procedure
    try:
        classify_patient_risk(patient_id)
    except Exception as e:
        logger.error(f"Error classifying patient risk: {str(e)}")
        # No fallback for this, but continue with the page
    
    # Get updated patient data after risk classification
    patient = Patient.query.get_or_404(patient_id)
    
    # Get patient's medical records
    medical_records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.record_date.desc()).all()
    
    # Extract risk level from medical history
    risk_level = "Unknown"
    if patient.medical_history:
        if "[HIGH RISK]" in patient.medical_history:
            risk_level = "High"
        elif "[MEDIUM RISK]" in patient.medical_history:
            risk_level = "Medium"
        elif "[LOW RISK]" in patient.medical_history:
            risk_level = "Low"
    
    return render_template(
        'patient_risk_assessment.html',
        patient=patient,
        patient_age=patient_age,
        appointments=appointments,
        medical_records=medical_records,
        risk_level=risk_level,
        now=datetime.now
    )

@app.route('/debug/check_patients')
def check_patients():
    """Debug route to check patients in the database without authentication"""
    try:
        # Get all patients
        patients = Patient.query.all()
        patients_data = []
        
        for patient in patients:
            try:
                user = User.query.get(patient.user_id)
                patients_data.append({
                    "id": patient.id,
                    "user_id": patient.user_id,
                    "username": user.username if user else "Unknown",
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "email": patient.email
                })
            except Exception as e:
                patients_data.append({
                    "id": patient.id,
                    "error": str(e)
                })
            
        return jsonify({
            "patient_count": len(patients),
            "patients": patients_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/staff/records')
@login_required
def staff_medical_records():
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    staff_profile = MedicalStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_profile:
        flash('Staff profile not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all medical records created by this staff member
    records = MedicalRecord.query.filter_by(staff_id=staff_profile.id).order_by(MedicalRecord.record_date.desc()).all()
    
    return render_template('staff/medical_records.html', records=records)

@app.route('/staff/records/<int:record_id>/delete', methods=['POST'])
@login_required
def staff_delete_record(record_id):
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    staff_profile = MedicalStaff.query.filter_by(user_id=current_user.id).first()
    if not staff_profile:
        flash('Staff profile not found', 'danger')
        return redirect(url_for('dashboard'))
    
    record = MedicalRecord.query.get_or_404(record_id)
    
    # Check if the record belongs to this staff member
    if record.staff_id != staff_profile.id:
        flash('You do not have permission to delete this record', 'danger')
        return redirect(url_for('staff_medical_records'))
    
    try:
        # Store record details for audit log
        patient_id = record.patient_id
        diagnosis = record.diagnosis
        record_date = record.record_date
        
        # Delete the record
        db.session.delete(record)
        
        # Create audit log
        audit = SecurityAudit(
            user_id=current_user.id,
            action='delete_medical_record',
            action_details=f'Deleted medical record (ID: {record_id}, Patient ID: {patient_id}, Diagnosis: {diagnosis}, Date: {record_date})',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            status='Success'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Medical record deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting medical record: {str(e)}")
        
        # Create audit log for failed deletion
        audit = SecurityAudit(
            user_id=current_user.id,
            action='delete_medical_record',
            action_details=f'Failed to delete medical record (ID: {record_id}). Error: {str(e)}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            status='Failed'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Error deleting medical record: {str(e)}', 'danger')
    
    return redirect(url_for('staff_medical_records'))

@app.route('/health-resources')
def health_resources():
    featured_resources = PublicHealthResource.query.filter_by(is_featured=True).limit(3).all()
    resources = PublicHealthResource.query.order_by(PublicHealthResource.created_at.desc()).all()
    
    # Group resources by type
    resources_by_type = {}
    for resource in resources:
        if resource.resource_type not in resources_by_type:
            resources_by_type[resource.resource_type] = []
        resources_by_type[resource.resource_type].append(resource)
    
    return render_template('health_resources.html', 
                          featured_resources=featured_resources, 
                          resources_by_type=resources_by_type)

@app.route('/health-resources/<int:resource_id>')
def view_health_resource(resource_id):
    resource = PublicHealthResource.query.get_or_404(resource_id)
    related_resources = PublicHealthResource.query.filter(
        PublicHealthResource.resource_type == resource.resource_type,
        PublicHealthResource.id != resource.id
    ).limit(3).all()
    
    return render_template('health_resource_detail.html', 
                          resource=resource, 
                          related_resources=related_resources)

# Helper function to check if a datetime is within 15 minutes of now
def is_within_15_minutes(dt):
    now = datetime.now()
    diff = dt - now
    minutes = diff.total_seconds() / 60
    return -15 <= minutes <= 15  # Allow joining 15 minutes before or after start time

# Add the helper function to the Jinja environment
app.jinja_env.globals.update(is_within_15_minutes=is_within_15_minutes)

# Telemedicine routes
@app.route('/telemedicine')
@login_required
def telemedicine_dashboard():
    """Route to the telemedicine dashboard based on user role."""
    if current_user.role == 'patient':
        # Get patient's upcoming video consultations
        upcoming_consultations = VideoConsultation.query.join(
            Appointment, VideoConsultation.appointment_id == Appointment.id
        ).join(
            MedicalStaff, Appointment.staff_id == MedicalStaff.id
        ).filter(
            Appointment.patient_id == current_user.id,
            VideoConsultation.status.in_(['Scheduled', 'In Progress']),
            VideoConsultation.scheduled_start > datetime.now() - timedelta(hours=1)
        ).order_by(VideoConsultation.scheduled_start).all()
        
        # Get patient's past video consultations
        past_consultations = VideoConsultation.query.join(
            Appointment, VideoConsultation.appointment_id == Appointment.id
        ).join(
            MedicalStaff, Appointment.staff_id == MedicalStaff.id
        ).filter(
            Appointment.patient_id == current_user.id,
            VideoConsultation.status.in_(['Completed', 'Cancelled']),
        ).order_by(VideoConsultation.scheduled_start.desc()).all()
        
        return render_template('telemedicine_dashboard.html', 
                               upcoming_consultations=upcoming_consultations,
                               past_consultations=past_consultations)
    
    elif current_user.role == 'staff':
        # Get staff's upcoming video consultations
        upcoming_consultations = VideoConsultation.query.join(
            Appointment, VideoConsultation.appointment_id == Appointment.id
        ).join(
            Patient, Appointment.patient_id == Patient.id
        ).filter(
            Appointment.staff_id == current_user.id,
            VideoConsultation.status.in_(['Scheduled', 'In Progress']),
            VideoConsultation.scheduled_start > datetime.now() - timedelta(hours=1)
        ).order_by(VideoConsultation.scheduled_start).all()
        
        # Get staff's past video consultations
        past_consultations = VideoConsultation.query.join(
            Appointment, VideoConsultation.appointment_id == Appointment.id
        ).join(
            Patient, Appointment.patient_id == Patient.id
        ).filter(
            Appointment.staff_id == current_user.id,
            VideoConsultation.status.in_(['Completed', 'Cancelled']),
        ).order_by(VideoConsultation.scheduled_start.desc()).all()
        
        return render_template('telemedicine_dashboard.html', 
                               upcoming_consultations=upcoming_consultations,
                               past_consultations=past_consultations)
    
    return redirect(url_for('home'))

@app.route('/create_video_consultation', methods=['GET', 'POST'])
@login_required
def create_video_consultation():
    """Route to create a new video consultation."""
    if current_user.role != 'staff':
        flash('Access denied. Only staff can create video consultations.', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        scheduled_start = datetime.fromisoformat(request.form.get('scheduled_start'))
        duration = int(request.form.get('duration'))
        notes = request.form.get('notes')
        
        # Calculate scheduled end time
        scheduled_end = scheduled_start + timedelta(minutes=duration)
        
        # Generate a unique meeting ID
        meeting_id = f"AHH-{uuid.uuid4().hex[:8]}"
        
        # Generate a passcode
        passcode = ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))
        
        # Create a mock meeting link (in a real app, this would be generated by the video API)
        meeting_link = f"https://meeting.africanhealthhub.com/j/{meeting_id}"
        
        # Create the video consultation
        try:
            new_consultation = VideoConsultation(
                appointment_id=appointment_id,
                meeting_link=meeting_link,
                meeting_id=meeting_id,
                passcode=passcode,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                status='Scheduled',
                notes=notes,
                created_by=current_user.id,
                created_at=datetime.now()
            )
            
            db.session.add(new_consultation)
            db.session.commit()
            
            # Log the action
            log_security_event(
                current_user.id,
                'Video Consultation Created',
                f"Created video consultation for appointment ID {appointment_id}"
            )
            
            flash('Video consultation scheduled successfully!', 'success')
            return redirect(url_for('telemedicine_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating video consultation: {str(e)}', 'danger')
            return redirect(url_for('create_video_consultation'))
    
    # Handle GET request - show form
    # Get patient search from query params
    patient_search = request.args.get('patient_search', '')
    date_filter = request.args.get('date_filter', 'upcoming')
    
    # Query to filter appointments
    appointments_query = Appointment.query.join(
        Patient, Appointment.patient_id == Patient.id
    ).filter(
        Appointment.staff_id == current_user.id,
        Appointment.status == 'Scheduled'  # Only show scheduled appointments
    )
    
    # Apply patient search if provided
    if patient_search:
        appointments_query = appointments_query.filter(
            or_(
                Patient.first_name.ilike(f'%{patient_search}%'),
                Patient.last_name.ilike(f'%{patient_search}%'),
                cast(Patient.id, String).like(f'%{patient_search}%')
            )
        )
    
    # Apply date filter
    now = datetime.now()
    if date_filter == 'today':
        appointments_query = appointments_query.filter(
            func.cast(Appointment.appointment_date, db.Date) == func.cast(now, db.Date)
        )
    elif date_filter == 'tomorrow':
        tomorrow = now + timedelta(days=1)
        appointments_query = appointments_query.filter(
            func.cast(Appointment.appointment_date, db.Date) == func.cast(tomorrow, db.Date)
        )
    elif date_filter == 'week':
        week_later = now + timedelta(days=7)
        appointments_query = appointments_query.filter(
            Appointment.appointment_date >= now,
            Appointment.appointment_date <= week_later
        )
    elif date_filter == 'upcoming':
        appointments_query = appointments_query.filter(
            Appointment.appointment_date >= now
        )
    
    # Order by date
    appointments = appointments_query.order_by(Appointment.appointment_date).all()
    
    # Filter out appointments that already have a video consultation
    existing_consultation_appointments = db.session.query(VideoConsultation.appointment_id).all()
    existing_appointment_ids = [item[0] for item in existing_consultation_appointments]
    
    appointments = [a for a in appointments if a.id not in existing_appointment_ids]
    
    return render_template('create_consultation.html', appointments=appointments)

@app.route('/join_consultation/<int:consultation_id>')
@login_required
def join_consultation(consultation_id):
    """Route to join a video consultation."""
    consultation = VideoConsultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get_or_404(consultation.appointment_id)
    
    # Check if the user is either the patient or the staff for this consultation
    if current_user.role == 'patient':
        if appointment.patient_id != current_user.id:
            flash('Access denied. This is not your consultation.', 'danger')
            return redirect(url_for('telemedicine_dashboard'))
        
        # Get the staff details
        staff = MedicalStaff.query.get_or_404(appointment.staff_id)
        patient = current_user
    
    elif current_user.role == 'staff':
        if appointment.staff_id != current_user.id:
            flash('Access denied. This is not your consultation.', 'danger')
            return redirect(url_for('telemedicine_dashboard'))
        
        # Get the patient details
        patient = Patient.query.get_or_404(appointment.patient_id)
        staff = current_user
    
    else:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    # Update consultation status to In Progress if it's currently Scheduled
    if consultation.status == 'Scheduled':
        # If this is the first time joining, mark actual start time
        if not consultation.actual_start:
            consultation.actual_start = datetime.now()
        
        consultation.status = 'In Progress'
        db.session.commit()
    
    # Log the action
    log_security_event(
        current_user.id,
        'Joined Video Consultation',
        f"Joined video consultation ID {consultation_id}"
    )
    
    return render_template('consultation_room.html', 
                          consultation=consultation,
                          appointment=appointment,
                          patient=patient,
                          staff=staff)

@app.route('/end_consultation/<int:consultation_id>', methods=['POST'])
@login_required
def end_consultation(consultation_id):
    """Route to end a video consultation (staff only)."""
    if current_user.role != 'staff':
        flash('Access denied. Only staff can end consultations.', 'danger')
        return redirect(url_for('telemedicine_dashboard'))
    
    consultation = VideoConsultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get_or_404(consultation.appointment_id)
    
    # Check if the staff is assigned to this consultation
    if appointment.staff_id != current_user.id:
        flash('Access denied. This is not your consultation.', 'danger')
        return redirect(url_for('telemedicine_dashboard'))
    
    # Update consultation status to Completed
    consultation.status = 'Completed'
    consultation.actual_end = datetime.now()
    consultation.notes = request.form.get('consultation_notes', consultation.notes)
    consultation.updated_at = datetime.now()
    
    db.session.commit()
    
    # Log the action
    log_security_event(
        current_user.id,
        'Ended Video Consultation',
        f"Ended video consultation ID {consultation_id}"
    )
    
    flash('Consultation ended successfully.', 'success')
    return redirect(url_for('telemedicine_dashboard'))

@app.route('/cancel_consultation/<int:consultation_id>', methods=['POST'])
@login_required
def cancel_consultation(consultation_id):
    """Route to cancel a video consultation (staff only)."""
    if current_user.role != 'staff':
        flash('Access denied. Only staff can cancel consultations.', 'danger')
        return redirect(url_for('telemedicine_dashboard'))
    
    consultation = VideoConsultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get_or_404(consultation.appointment_id)
    
    # Check if the staff is assigned to this consultation
    if appointment.staff_id != current_user.id:
        flash('Access denied. This is not your consultation.', 'danger')
        return redirect(url_for('telemedicine_dashboard'))
    
    # Update consultation status to Cancelled
    consultation.status = 'Cancelled'
    consultation.notes = request.form.get('cancellation_reason', '')
    consultation.updated_at = datetime.now()
    
    db.session.commit()
    
    # Log the action
    log_security_event(
        current_user.id,
        'Cancelled Video Consultation',
        f"Cancelled video consultation ID {consultation_id}. Reason: {consultation.notes}"
    )
    
    flash('Consultation cancelled successfully.', 'success')
    return redirect(url_for('telemedicine_dashboard'))

@app.route('/consultation_details/<int:consultation_id>')
@login_required
def consultation_details(consultation_id):
    """Route to get consultation details for the modal."""
    consultation = VideoConsultation.query.get_or_404(consultation_id)
    appointment = Appointment.query.get_or_404(consultation.appointment_id)
    
    # Check if the user is either the patient or the staff for this consultation
    if current_user.role == 'patient':
        if appointment.patient_id != current_user.id:
            return "Access denied", 403
    
    elif current_user.role == 'staff':
        if appointment.staff_id != current_user.id:
            return "Access denied", 403
    
    else:
        return "Access denied", 403
    
    # Add related objects to the consultation
    consultation.appointment = appointment
    consultation.patient = Patient.query.get(appointment.patient_id)
    consultation.staff = MedicalStaff.query.get(appointment.staff_id)
    
    return render_template('consultation_details.html', consultation=consultation)

# Note: The staff dashboard route at line 370 already includes telemedicine functionality

if __name__ == '__main__':
    with app.app_context():
        try:
            # Test database connection
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            connection = engine.connect()
            connection.close()
            logger.info("✅ Successfully connected to SQL Server via SQLAlchemy!")
            
            # Initialize database
            init_db()
            
            # SQL functions are assumed to be created by running sql_functions.sql in SQL Server Management Studio
            logger.info("✅ SQL functions, triggers, and stored procedures should be created manually using sql_functions.sql")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to database: {str(e)}")
            traceback.print_exc()
            raise
    
    app.run(debug=True)
