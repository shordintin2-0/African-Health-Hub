# wsgi.py - WSGI entry point
from app import app as application

# This ensures the application is properly callable as a WSGI app
if __name__ == '__main__':
    application.run()
