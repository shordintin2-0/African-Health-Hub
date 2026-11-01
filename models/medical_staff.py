from database import db
from datetime import datetime

class MedicalStaff(db.Model):
    __tablename__ = 'medical_staff181'
    staff_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=True)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Active')

    # Relationships
    appointments = db.relationship('Appointment', back_populates='staff', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='staff', cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys='User.staff_id', backref=db.backref('staff', uselist=False), post_update=True)

    def __repr__(self):
        return f'<MedicalStaff {self.first_name} {self.last_name}>'
