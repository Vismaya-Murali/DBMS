import random
import string
from flask import Flask, flash, render_template, request, redirect, session, url_for
import mysql.connector
import base64
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Function to establish a database connection
def get_db_connection():
    return mysql.connector.connect(
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

def generate_passenger_id(length=10):
    """Generates a random PassengerID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/handle_register', methods=['POST'])
def handle_register():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['fname']
    last_name = request.form['lname']
    phone_number = request.form['phone']
    email = request.form['email']
    role = request.form['role']  # Capturing the role ('user' or 'admin')
    
    passenger_id = generate_passenger_id()

    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Insert passenger details into passenger table
        cursor.execute(
            "INSERT INTO passenger(PassengerID, Fname, Lname, Phone, email) VALUES (%s, %s, %s, %s, %s)", 
            (passenger_id, first_name, last_name, phone_number, email)
        )

        # Insert login credentials and role into the Login table
        cursor.execute(
            "INSERT INTO Login (LoginID, Password, user_id, is_admin) VALUES (%s, %s, %s, %s)", 
            (username, password, passenger_id, 1 if role == 'admin' else 0)  # 1 for admin, 0 for user
        )
        db.commit()
        
        # Store PassengerID and Role in the session
        session['passenger_id'] = passenger_id
        session['role'] = role  # Store the role in the session

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error during registration"
    finally:
        cursor.close()
        db.close()

    return redirect('/login')

@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    # Fetch user details including PassengerID and is_admin field
    cursor.execute("SELECT user_id, is_admin FROM Login WHERE LoginID = %s AND Password = %s", 
                   (username, password))
    user = cursor.fetchone()
    
    cursor.close()
    db.close()

    if user:
        # Store username and PassengerID in the session
        session['username'] = username
        session['passenger_id'] = user[0]  # Store PassengerID in the session
        session['role'] = 'admin' if user[1] == 1 else 'user'
        
        # Check if the user is an admin or a regular user
        if user[1] == 1:  # Admin
            return redirect('/admin_dashboard')  # Redirect to admin dashboard
        else:  # Regular user
            return redirect('/home')  # Redirect to user home page
    else:
        return "Invalid credentials, try again."

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' in session and session.get('role') == 'admin':
        db = get_db_connection()
        cursor = db.cursor()

        # Fetch restaurant details
        cursor.execute("SELECT Rname, Location, Phno,RID FROM restaurant")
        restaurants = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template('admin_dashboard.html', restaurants=restaurants)
    else:
        return redirect('/login')

@app.route('/update_restaurant', methods=['GET', 'POST'])
def update_restaurant():
    if 'username' in session and session.get('role') == 'admin':
        # Fetch all restaurant data from the database
        db = get_db_connection()
        cursor = db.cursor()

        # Query to get all restaurant details
        cursor.execute("SELECT Rname,Location,Phno,RID FROM restaurant")
        restaurants = cursor.fetchall()
        cursor.close()
        db.close()

        # Render only the update restaurant HTML content (with restaurant data)
        return render_template('admin_dashboard.html', restaurants=restaurants)
    else:
        return redirect('/login')

@app.route('/edit_rest', methods=['POST'])
def edit_rest():
    if 'username' in session and session.get('role') == 'admin':
        restaurant_id = request.form.get('restaurant_id')
        restaurant_name = request.form.get('restaurant_name')
        location = request.form.get('location')
        phone = request.form.get('phone')
        
        db = get_db_connection()
        cursor = db.cursor()

        try:
            cursor.execute("""
                UPDATE restaurant
                SET Rname = %s, Location = %s, Phno = %s
                WHERE RID = %s
            """, (restaurant_name, location, phone, restaurant_id))

            db.commit()
            flash("Restaurant details updated successfully.", "success")
        
        except Exception as e:
            db.rollback()
            flash("An error occurred: " + str(e), "error")

        finally:
            cursor.close()
            db.close()

        return redirect(url_for('admin_dashboard',section='updateRestaurant'))
    else:
        return redirect('/login')

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html')
    return redirect('/login')

@app.route('/profile')
def profile():
    # Fetch PassengerID from session
    passenger_id = session.get('passenger_id')

    if not passenger_id:
        return redirect('/login')  # Redirect if no user is logged in

    db = get_db_connection()
    cursor = db.cursor()

    # Query to fetch passenger details
    cursor.execute("""
        SELECT PassengerID, Fname, Lname, Phone, email
        FROM passenger
        WHERE PassengerID = %s
    """, (passenger_id,))
    passenger = cursor.fetchone()

    cursor.close()
    db.close()

    if not passenger:
        return "Passenger details not found.", 404

    return render_template('profile.html', passenger=passenger)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # Get the updated data from the form
    passenger_id = session.get('passenger_id')
    updated_fname = request.form['fname']
    updated_lname = request.form['lname']
    updated_phone = request.form['phone']
    updated_email = request.form['email']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("""
        UPDATE passenger
        SET Fname = %s, Lname = %s, Phone = %s, email = %s
        WHERE PassengerID = %s
    """, (updated_fname, updated_lname, updated_phone, updated_email, passenger_id))
    
    db.commit()
    cursor.close()
    db.close()

    return redirect('/profile')

@app.route('/select_station', methods=['POST'])
def select_station():
    train_id = request.form.get('train_id')

    db = get_db_connection()
    cursor = db.cursor()
    
    query = """
        SELECT s.Station_id, st.Sname 
        FROM stops s 
        JOIN Station st ON s.Station_id = st.StationID
        WHERE s.Train_id = %s
    """
    cursor.execute(query, (train_id,))
    stops = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('stops.html', train_id=train_id, stops=stops)

@app.route('/select_train', methods=['POST'])
def select_train():
    stations = ['Bangalore', 'Chennai', 'Hyderabad']
    return render_template('select_train.html', stations=stations)

@app.route('/select_stops', methods=['POST'])
def select_stops():
    db = get_db_connection()
    cursor = db.cursor()
    
    query = "SELECT TrainID, TrainName FROM train"
    cursor.execute(query)
    trains = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('train_stops.html', trains=trains)

@app.route('/restaurants_at_station', methods=['POST'])
def restaurants_at_station():
    selected_station_id = request.form['station_id']

    db = get_db_connection()
    cursor = db.cursor()

    query = """
        SELECT Rname, RID, Phno 
        FROM restaurant 
        WHERE Station_id = %s
    """
    cursor.execute(query, (selected_station_id,))
    restaurants = cursor.fetchall()

    if restaurants:
        session['StationID'] = selected_station_id

    cursor.close()
    db.close()

    return render_template('restaurants.html', station_id=selected_station_id, restaurants=restaurants)

@app.route('/select_restaurant', methods=['POST'])
def select_restaurant():
    restaurant_id = request.form.get('restaurant_id')
    if not restaurant_id:
        return "Error: No restaurant selected.", 400
    
    session['RID'] = restaurant_id
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)
