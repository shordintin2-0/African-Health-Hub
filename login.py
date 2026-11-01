from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for session management
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://@localhost/AfricanHealthHub181?driver=ODBC+Driver+17+for+SQL+Server'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Prevents unnecessary warnings

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Test database connection
try:
    with app.app_context():
        with db.engine.connect() as connection:
            print("✅ Successfully connected to SQL Server!")
            # Print the list of tables in the database
            print("Tables in the database:", db.engine.dialect.get_table_names(db.engine.connect()))
except Exception as e:
    print(f"❌ Database connection failed: {e}")


# Mock user database (replace with actual database queries)
users = {
    'admin': {'password': 'adminpass', 'role': 'admin'},
    'manager': {'password': 'managerpass', 'role': 'manager'},
    'staff': {'password': 'staffpass', 'role': 'staff'},
    'customer': {'password': 'customerpass', 'role': 'customer'},
    'guest': {'password': 'guestpass', 'role': 'guest'}
}

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    role = session['role']
    if role == 'admin':
        return render_template('admin_dashboard.html')
    elif role == 'manager':
        return render_template('manager_dashboard.html')
    elif role == 'staff':
        return render_template('staff_dashboard.html')
    elif role == 'customer':
        return render_template('customer_dashboard.html')
    elif role == 'guest':
        return render_template('guest_dashboard.html')
    else:
        return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)