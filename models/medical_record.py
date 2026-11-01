from database import db
from datetime import datetime

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records181'
    record_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients181.patient_id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('medical_staff181.staff_id'), nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)
    treatment = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    record_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', back_populates='medical_records')
    staff = db.relationship('MedicalStaff', back_populates='medical_records')

    def __repr__(self):
        return f'<MedicalRecord {self.record_id} - Patient: {self.patient_id}>'
