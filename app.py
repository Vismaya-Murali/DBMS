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
    username = request.form['username']
    password = request.form['password']
    
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Login (LoginID, Password) VALUES (%s, %s)", 
                       (username, password))
        db.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error during registration"
    finally:
        cursor.close()

    return redirect('/login')

@app.route('/back_to_home')
def back_to_home():
    return render_template('/home.html')

@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Login WHERE LoginID = %s AND Password = %s", 
                   (username, password))
    user = cursor.fetchone()
    
    cursor.close()

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


@app.route('/select_station', methods=['POST'])
def select_station():
    train_id = request.form.get('train_id')

    cursor = db.cursor()
    
    # Query to fetch all stops for the selected train
    query = """
        SELECT s.Station_id, st.Sname 
        FROM stops s 
        JOIN Station st ON s.Station_id = st.StationID
        WHERE s.Train_id = %s
    """
    cursor.execute(query, (train_id,))
    stops = cursor.fetchall()  # Fetch all stops for the train
    
    cursor.close()
    
    # Pass the stops and train_id to the template for rendering
    return render_template('stops.html', train_id=train_id, stops=stops)


# Route to show list of stations for selection
@app.route('/select_train', methods=['POST'])
def select_train():
    #src = request.form['src']
    #dest = request.form['dest']

    # Logic to fetch available trains or stations between src and dest (not implemented here)
    
    # Assuming it will render a template that lists stations to choose for food delivery
    stations = ['Bangalore', 'Chennai', 'Hyderabad']  # Example station list
    return render_template('select_train.html', stations=stations)


@app.route('/select_stops', methods=['POST'])
def select_stops():
    cursor = db.cursor()
    
    # Query to select all trains from the Train table
    query = "SELECT TrainID, TrainName FROM train"
    cursor.execute(query)
    trains = cursor.fetchall()  # Fetch all train data
    
    cursor.close()
    
    # Render the template with the train data
    return render_template('train_stops.html', trains=trains)


@app.route('/restaurants_at_station', methods=['POST'])
def restaurants_at_station():
    # Get the selected station ID from the form
    selected_station_id = request.form['station_id']

    cursor = db.cursor()

    # Query to fetch restaurants at the selected station based on station ID
    query = """
        SELECT Rname, Location, Phno 
        FROM Restaurant 
        WHERE Station_id = %s
    """
    cursor.execute(query, (selected_station_id,))
    restaurants = cursor.fetchall()

    cursor.close()

    # Render the restaurants template with the station name and list of restaurants
    return render_template('restaurants.html', station_id=selected_station_id, restaurants=restaurants)


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)