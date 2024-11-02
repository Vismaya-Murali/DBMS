from flask import Flask, render_template, request, redirect, session, url_for
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

@app.route('/handle_register', methods=['POST'])
def handle_register():
    username = request.form['username']
    password = request.form['password']
    
    db = get_db_connection()
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
        db.close()

    return redirect('/login')

@app.route('/handle_login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Login WHERE LoginID = %s AND Password = %s", 
                   (username, password))
    user = cursor.fetchone()
    
    cursor.close()
    db.close()

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

    db = get_db_connection()
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
    db.close()
    
    # Pass the stops and train_id to the template for rendering
    return render_template('stops.html', train_id=train_id, stops=stops)

# Route to show list of stations for selection
@app.route('/select_train', methods=['POST'])
def select_train():
    # Assuming it will render a template that lists stations to choose for food delivery
    stations = ['Bangalore', 'Chennai', 'Hyderabad']  # Example station list
    return render_template('select_train.html', stations=stations)

@app.route('/select_stops', methods=['POST'])
def select_stops():
    db = get_db_connection()
    cursor = db.cursor()
    
    # Query to select all trains from the Train table
    query = "SELECT TrainID, TrainName FROM train"
    cursor.execute(query)
    trains = cursor.fetchall()  # Fetch all train data
    
    cursor.close()
    db.close()
    
    # Render the template with the train data
    return render_template('train_stops.html', trains=trains)

@app.route('/restaurants_at_station', methods=['POST'])
def restaurants_at_station():
    selected_station_id = request.form['station_id']

    db = get_db_connection()
    cursor = db.cursor()

    # Query to fetch restaurants at the selected station based on station ID
    query = """
        SELECT Rname, RID 
        FROM restaurant 
        WHERE Station_id = %s
    """
    cursor.execute(query, (selected_station_id,))
    restaurants = cursor.fetchall()

    cursor.close()
    db.close()

    # Render the restaurants template with the station name and list of restaurants
    return render_template('restaurants.html', station_id=selected_station_id, restaurants=restaurants)

@app.route('/menu/<restaurant_id>', methods=['GET', 'POST'])
def menu(restaurant_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT Item_name, Price, Image FROM menu WHERE Res_ID = %s"
    cursor.execute(query, (restaurant_id,))
    menu_items = cursor.fetchall()

    for index, item in enumerate(menu_items):
        if item[2] is not None:
            menu_items[index] = (
                item[0],
                item[1],
                base64.b64encode(item[2]).decode('utf-8')
            )
        else:
            menu_items[index] = (item[0], item[1], None)

    cursor.close()
    db.close()

    if request.method == 'POST':
        item_name = request.form.get('item_name')
        item_price = float(request.form.get('item_price'))
        if 'cart' not in session:
            session['cart'] = []
        session['cart'].append({'name': item_name, 'price': item_price})
        session.modified = True

    return render_template('menu.html', restaurant_name=restaurant_id, menu_items=menu_items)

@app.route('/place_order', methods=['POST'])
def place_order():
    db = get_db_connection()
    cursor = db.cursor()

    restaurant_id = request.form.get('RID')
    passenger_id = session.get('passenger_id')  # Get Passenger_id from session
    station_id = request.form.get('station_id')

    cursor.execute("SELECT DPID FROM deliveryperson LIMIT 1")
    dp_id = cursor.fetchone()[0]

    order_items = []
    for key, value in request.form.items():
        if key.startswith('quantity_') and int(value) > 0:
            item_name = key.split('quantity_')[1]
            quantity = int(value)
            order_items.append({'item_name': item_name, 'quantity': quantity})

    if not order_items:
        return redirect(url_for('menu', restaurant_id=restaurant_id, error="No items selected"))

    try:
        order_id = str(uuid.uuid4())[:8]
        order_date = datetime.now().date()
        total_amount = 0

        for item in order_items:
            cursor.execute("SELECT Price, ItemID FROM menu WHERE Item_name = %s", (item['item_name'],))
            price, item_id = cursor.fetchone()
            total_amount += price * item['quantity']
            item['item_id'] = item_id
            item['price'] = price

        cursor.execute(
            "INSERT INTO orders (OrderID, Order_date, Passenger_id, DP_ID, R_ID, S_ID) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_id, order_date, passenger_id, dp_id, restaurant_id, station_id)
        )

        for item in order_items:
            order_item_id = str(uuid.uuid4())[:8]
            cursor.execute(
                "INSERT INTO orderitems (OrdItemID, ItemPrice, quantity, Order_id, R_ID) VALUES (%s, %s, %s, %s, %s)",
                (order_item_id, item['price'], item['quantity'], order_id, restaurant_id)
            )

        db.commit()
    except Exception as e:
        db.rollback()
        print("Error placing order:", e)
        return "Error placing order"
    finally:
        cursor.close()
        db.close()

    return render_template('order_success.html', order_id=order_id, total_amount=total_amount, order_items=order_items)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        # Place an order
        return redirect('/place_order')  # Redirect to place order

    # Access the cart stored in the session
    cart_items = session.get('cart', [])
    total_price = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/order_success')
def order_success():
    return render_template('order_success.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
