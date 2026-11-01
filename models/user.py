from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users181'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # admin, staff, patient
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Foreign keys to link to specific roles
    patient_id = db.Column(db.Integer, db.ForeignKey('patients181.patient_id'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('medical_staff181.staff_id'), nullable=True)

    # Relationships
    patient_profile = db.relationship('Patient', foreign_keys=[patient_id], post_update=True)
    staff_profile = db.relationship('MedicalStaff', foreign_keys=[staff_id], post_update=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
