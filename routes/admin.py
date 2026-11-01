from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.user import User
from models.medical_staff import MedicalStaff
from models.security_audit import SecurityAudit

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You must be an administrator to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get recent audit logs
    audit_logs = SecurityAudit.query.order_by(SecurityAudit.action_date.desc()).limit(10).all()
    return render_template('dashboard/admin.html', audit_logs=audit_logs)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/staff')
@login_required
@admin_required
def manage_staff():
    staff = MedicalStaff.query.all()
    return render_template('admin/staff.html', staff=staff)

@admin_bp.route('/audit')
@login_required
@admin_required
def audit_logs():
    logs = SecurityAudit.query.order_by(SecurityAudit.action_date.desc()).all()
    return render_template('admin/audit.html', logs=logs)
