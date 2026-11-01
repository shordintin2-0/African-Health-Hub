from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mssql+pyodbc://AMERLEY/AfricanHealthHub181?'
        'driver=ODBC+Driver+17+for+SQL+Server&'
        'trusted_connection=yes&'
        'encrypt=yes&'
        'trustservercertificate=yes'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Import and register blueprints
    from .auth import auth as auth_blueprint
    from .routes import init_routes
    
    app.register_blueprint(auth_blueprint)
    init_routes(app)
    
    return app
