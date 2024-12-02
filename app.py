from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = 'your_secret_key'
SENDGRID_API_KEY = 'your_sendgrid_api_key'

def create_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='glen',
            database='user_auth'
        )
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def send_notification_email(to_email, subject, content):
    message = Mail(
        from_email='glenbryan23@gmail.com',
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and check_password_hash(user[6], password):  # Adjust index for hashed password
                session['user_id'] = user[0]
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('index', error="Invalid email or password"))
    return render_template('login.html', error=request.args.get('error'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        phone_number = request.form['phone_number']
        blood_group = request.form['blood_group']
        age = request.form['age']
        gender = request.form['gender']
        password = request.form['password']
        re_password = request.form['re_password']

        if password != re_password:
            return "Passwords do not match"

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (email, phone_number, blood_group, age, gender, password) VALUES (%s, %s, %s, %s, %s, %s)",
                    (email, phone_number, blood_group, age, gender, hashed_password)
                )
                connection.commit()
                cursor.close()
                connection.close()

                send_notification_email(
                    email,
                    "Welcome to Our Service",
                    "Thank you for signing up. We're glad to have you!"
                )

                return redirect(url_for('index'))
            except Error as e:
                print(f"Error: {e}")  # Print error details
                return "Error: Could not create user. Check the console for details."
        else:
            return "Error: Database connection failed"
    return render_template('signup.html')



@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/test_db')
def test_db():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        cursor.close()
        connection.close()
        return f"Connected to database: {db_name[0]}"
    else:
        return "Failed to connect to database"
