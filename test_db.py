import mysql.connector
from flask import Flask

app = Flask(__name__)

# Configure your database credentials here
app.config['MYSQL_HOST'] = 'AMERLEY'  # Replace with your DB host
app.config['MYSQL_USER'] = 'AMERLEY\amerley'  # Replace with your DB username
app.config['MYSQL_PASSWORD'] = ''  # Replace with your DB password
app.config['MYSQL_DB'] = 'AfricanHealthHub181'  # Replace with your DB name


@app.route('/test_db')
def test_db_connection():
    try:
        # Attempt to connect to the database
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )

        if conn.is_connected():
            conn.close()  # Close the connection after testing
            return "Database connection successful!", 200
        else:
            return "Database connection failed!", 500

    except mysql.connector.Error as err:
        return f"Database connection error: {err}", 500


if __name__ == '__main__':
    app.run(debug=True)