from flask import Blueprint
from .admin import admin_bp
from .staff import staff_bp
from .patient import patient_bp

def init_routes(app):
    """Initialize all route blueprints"""
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(patient_bp)
