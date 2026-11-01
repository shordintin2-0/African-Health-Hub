from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db
from models.user import User
from models.security_audit import SecurityAudit

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(get_dashboard_url(current_user.role))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password) and user.role == role:
            login_user(user)
            
            # Log the successful login
            audit = SecurityAudit(
                action_type='LOGIN',
                table_affected='users181',
                user_name=username,
                affected_record_id=user.id
            )
            db.session.add(audit)
            db.session.commit()
            
            return redirect(get_dashboard_url(role))
        else:
            flash('Invalid username, password, or role.', 'danger')

    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    # Log the logout
    audit = SecurityAudit(
        action_type='LOGOUT',
        table_affected='users181',
        user_name=current_user.username,
        affected_record_id=current_user.id
    )
    db.session.add(audit)
    db.session.commit()
    
    logout_user()
    return redirect(url_for('auth.login'))

def get_dashboard_url(role):
    """Return the appropriate dashboard URL based on user role"""
    if role == 'admin':
        return url_for('admin.dashboard')
    elif role == 'staff':
        return url_for('staff.dashboard')
    elif role == 'patient':
        return url_for('patient.dashboard')
    return url_for('home')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        audit = SecurityAudit(
            action_type='REGISTER',
            table_affected='users181',
            user_name=username,
            affected_record_id=user.id
        )
        db.session.add(audit)
        db.session.commit()

        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
