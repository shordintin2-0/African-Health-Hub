from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db
from models.patient import Patient
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from models.security_audit import SecurityAudit

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'patient':
            flash('You must be a patient to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.patient.id,
        Appointment.appointment_date >= datetime.now()
    ).order_by(Appointment.appointment_date).all()
    
    # Get recent medical updates
    recent_updates = MedicalRecord.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(MedicalRecord.update_date.desc()).limit(10).all()
    
    return render_template('dashboard/patient.html',
                         upcoming_appointments=upcoming_appointments,
                         recent_updates=recent_updates)

@patient_bp.route('/appointments')
@login_required
@patient_required
def appointments():
    appointments = Appointment.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(Appointment.appointment_date).all()
    return render_template('patient/appointments.html', appointments=appointments)

@patient_bp.route('/medical-history')
@login_required
@patient_required
def medical_history():
    records = MedicalRecord.query.filter_by(
        patient_id=current_user.patient.id
    ).order_by(MedicalRecord.update_date.desc()).all()
    return render_template('patient/medical_history.html', records=records)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def profile():
    if request.method == 'POST':
        try:
            patient = current_user.patient
            patient.contact_number = request.form['contact_number']
            patient.email = request.form['email']
            patient.address = request.form['address']
            
            audit = SecurityAudit(
                action_type='UPDATE',
                table_affected='patients181',
                user_name=current_user.username,
                affected_record_id=patient.patient_id
            )
            
            db.session.add(audit)
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'danger')
            
    return render_template('patient/profile.html', patient=current_user.patient)

@patient_bp.route('/appointment/<int:id>/cancel')
@login_required
@patient_required
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    if appointment.patient_id != current_user.patient.id:
        flash('You can only cancel your own appointments.', 'danger')
        return redirect(url_for('patient.appointments'))
        
    try:
        db.session.delete(appointment)
        
        audit = SecurityAudit(
            action_type='DELETE',
            table_affected='appointments181',
            user_name=current_user.username,
            affected_record_id=id
        )
        
        db.session.add(audit)
        db.session.commit()
        
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling appointment.', 'danger')
        
    return redirect(url_for('patient.appointments'))

@patient_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        try:
            new_patient = Patient(
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date(),
                gender=request.form['gender'],
                contact_number=request.form['contact_number'],
                email=request.form['email'],
                address=request.form['address'],
                medical_history=request.form['medical_history'],
                risk_level=request.form['risk_level']
            )
            
            db.session.add(new_patient)
            
            # Log the action
            audit = SecurityAudit(
                user_id=current_user.id,
                action='create',
                resource='patient',
                ip_address=request.remote_addr,
                details=f'Created new patient: {new_patient.first_name} {new_patient.last_name}'
            )
            db.session.add(audit)
            
            db.session.commit()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('patient.view_patients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding patient: {str(e)}', 'error')
            
    return render_template('add_patient.html')

@patient_bp.route('/list')
@login_required
def view_patients():
    patients = Patient.query.all()
    
    # Log the access
    audit = SecurityAudit(
        user_id=current_user.id,
        action='view',
        resource='patient',
        ip_address=request.remote_addr,
        details='Viewed patient list'
    )
    db.session.add(audit)
    db.session.commit()
    
    return render_template('patients.html', patients=patients)

@patient_bp.route('/<int:patient_id>')
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Log the access
    audit = SecurityAudit(
        user_id=current_user.id,
        action='view',
        resource='patient',
        ip_address=request.remote_addr,
        details=f'Viewed patient details: {patient.first_name} {patient.last_name}'
    )
    db.session.add(audit)
    db.session.commit()
    
    return render_template('patient_details.html', patient=patient)
