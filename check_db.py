from app import app, User, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    # Check Users
    logger.info("===== USERS IN DATABASE =====")
    users = User.query.all()
    for user in users:
        logger.info(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}")
        
        # Test password validation for the test users
        if user.username in ['admin', 'patient', 'staff']:
            test_password = user.username + '123'  # admin123, patient123, staff123
            is_valid = user.check_password(test_password)
            logger.info(f"Password check for {user.username} with '{test_password}': {is_valid}") 