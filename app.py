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
<<<<<<< HEAD
    print("Register route accessed")  # Debugging statement
    username = request.form['username']
    password = request.form['password']
    
    # Insert the user into the database without PassengerID (MySQL handles it)
=======
    username = request.form['username']
    password = request.form['password']
    
>>>>>>> 49d5f1a (Initial commit with project files)
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Login (LoginID, Password) VALUES (%s, %s)", 
                       (username, password))
        db.commit()
<<<<<<< HEAD
        print("User registered successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error during registration"  # Return an appropriate message or redirect
=======
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error during registration"
>>>>>>> 49d5f1a (Initial commit with project files)
    finally:
        cursor.close()

    return redirect('/login')

<<<<<<< HEAD
=======
@app.route('/back_to_home')
def back_to_home():
    return render_template('/home.html')

>>>>>>> 49d5f1a (Initial commit with project files)
@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    cursor = db.cursor()
<<<<<<< HEAD
    cursor.execute("SELECT * FROM Login WHERE LoginID = %s AND Password = %s", (username, password))
    user = cursor.fetchone()
    
=======
    cursor.execute("SELECT * FROM Login WHERE LoginID = %s AND Password = %s", 
                   (username, password))
    user = cursor.fetchone()
    
    cursor.close()

>>>>>>> 49d5f1a (Initial commit with project files)
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

<<<<<<< HEAD
=======
# This is the /select_station route to select a station and display restaurants
@app.route('/select_station', methods=['POST'])
def select_station():
    selected_station = request.form['station']
    
    cursor = db.cursor()
    query = """
        SELECT Rname, Location, Phno 
        FROM Restaurant 
        WHERE Station_id = (
            SELECT StationID FROM Station WHERE Sname = %s
        )
    """
    cursor.execute(query, (selected_station,))
    restaurants = cursor.fetchall()
    
    cursor.close()
    
    return render_template('restaurants.html', station=selected_station, restaurants=restaurants)

# @app.route('/ordering')
# def ordering():
#     stations = ['Bangalore', 'Chennai', 'Hyderabad']  # Example station list
#     return render_template('select_train.html', stations=stations)


# Route to show list of stations for selection
@app.route('/select_train', methods=['POST'])
def select_train():
    #src = request.form['src']
    #dest = request.form['dest']

    # Logic to fetch available trains or stations between src and dest (not implemented here)
    
    # Assuming it will render a template that lists stations to choose for food delivery
    stations = ['Bangalore', 'Chennai', 'Hyderabad']  # Example station list
    return render_template('select_train.html', stations=stations)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

>>>>>>> 49d5f1a (Initial commit with project files)
if __name__ == '__main__':
    app.run(debug=True)
