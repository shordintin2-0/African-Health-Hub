from database import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments181'
    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients181.patient_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('medical_staff181.staff_id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')  
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    staff = db.relationship('MedicalStaff', back_populates='appointments')

    def __repr__(self):
        return f'<Appointment {self.appointment_id} - Patient: {self.patient_id} - Staff: {self.staff_id}>'
