from database import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients181'
    patient_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    medical_history = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(10), nullable=False, default='Low')
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='patient', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='patient', cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys='User.patient_id', backref=db.backref('patient', uselist=False), post_update=True)

    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'
