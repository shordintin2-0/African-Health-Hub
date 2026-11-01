from database import db
from datetime import datetime

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

    # Relationships
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<SecurityAudit {self.audit_id} - User: {self.user_id} - Action: {self.action}>'
