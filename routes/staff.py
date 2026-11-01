from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db
from models.patient import Patient
from models.appointment import Appointment
from models.medical_record import MedicalRecord

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            flash('You must be a medical staff member to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    # Get today's appointments
    today = datetime.now().date()
    today_appointments = Appointment.query.filter(
        db.func.cast(Appointment.appointment_date, db.Date) == today
    ).all()
    
    # Get recent patient updates
    recent_updates = MedicalRecord.query.order_by(MedicalRecord.update_date.desc()).limit(10).all()
    
    return render_template('dashboard/staff.html', 
                         today_appointments=today_appointments,
                         recent_updates=recent_updates)

@staff_bp.route('/patients')
@login_required
@staff_required
def manage_patients():
    patients = Patient.query.all()
    return render_template('staff/patients.html', patients=patients)

@staff_bp.route('/appointments')
@login_required
@staff_required
def appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_date).all()
    return render_template('staff/appointments.html', appointments=appointments)

@staff_bp.route('/medical-records')
@login_required
@staff_required
def medical_records():
    records = MedicalRecord.query.order_by(MedicalRecord.update_date.desc()).all()
    return render_template('staff/medical_records.html', records=records)
