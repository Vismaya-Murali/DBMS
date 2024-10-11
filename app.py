from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="treatsontracks"
)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
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
    return redirect(url_for('login'))

@app.route('/select_train', methods=['POST'])
def select_train():
    src = request.form['src']
    dest = request.form['dest']
    
    cursor = db.cursor()
    cursor.execute("SELECT TrainName FROM Train WHERE TrainID IN (SELECT TrainID FROM Stops WHERE StationID IN (%s, %s))", (src, dest))
    trains = cursor.fetchall()
    
    if trains:
        session['src'] = src
        session['dest'] = dest
        return render_template('select_train.html', trains=[train[0] for train in trains])
    return "No trains found between the selected stations."

@app.route('/select_station', methods=['POST'])
def select_station():
    train_name = request.form['train']
    
    cursor = db.cursor()
    cursor.execute("SELECT StationID FROM Stops WHERE TrainID = (SELECT TrainID FROM Train WHERE TrainName = %s)", (train_name,))
    stations = cursor.fetchall()
    
    return render_template('select_station.html', stations=[station[0] for station in stations], train_name=train_name)

@app.route('/restaurants', methods=['POST'])
def restaurants():
    station_name = request.form['station']
    
    cursor = db.cursor()
    cursor.execute("SELECT RName FROM Restaurant WHERE RID IN (SELECT RID FROM Order WHERE SID = %s)", (station_name,))
    restaurants = cursor.fetchall()
    
    return render_template('restaurants.html', restaurants=[restaurant[0] for restaurant in restaurants], station_name=station_name)

if __name__ == '__main__':
    app.run(debug=True)
