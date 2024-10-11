from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="treatsontracks"
)

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/handle_register', methods=['POST'])
def handle_register():
    print("Register route accessed")  # Debugging statement
    username = request.form['username']
    password = request.form['password']
    
    # Insert the user into the database without PassengerID (MySQL handles it)
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Login (LoginID, Password) VALUES (%s, %s)", 
                       (username, password))
        db.commit()
        print("User registered successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error during registration"  # Return an appropriate message or redirect
    finally:
        cursor.close()

    return redirect('/login')

@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Login WHERE LoginID = %s AND Password = %s", (username, password))
    user = cursor.fetchone()
    
    if user:
        session['username'] = username
        return redirect('/home')
    else:
        return "Invalid credentials, try again."

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html')
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
