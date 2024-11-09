import random
import string
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

def generate_passenger_id(length=10):
    """Generates a random PassengerID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/handle_register', methods=['POST'])
def handle_register():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['fname']
    last_name = request.form['lname']
    coach_number = request.form['coach_no']
    phone_number = request.form['phone']
    email = request.form['email']
    role = request.form['role']  # Capturing the role ('user' or 'admin')
    
    passenger_id = generate_passenger_id()

    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Insert passenger details into passenger table
        cursor.execute(
            "INSERT INTO passenger(PassengerID, coach_no, Fname, Lname, Phone, email) VALUES (%s, %s, %s, %s, %s, %s)", 
            (passenger_id, coach_number, first_name, last_name, phone_number, email)
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
        cursor.execute("SELECT Rname, Location, Phno FROM restaurant")
        restaurants = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template('admin_dashboard.html', restaurants=restaurants)
    else:
        return redirect('/login')


@app.route('/update_restaurant', methods=['POST'])
def update_restaurant():
    if 'username' in session and session.get('role') == 'admin':
        # Fetch all restaurant data from the database
        db = get_db_connection()
        cursor = db.cursor()

        # Query to get all restaurant details
        cursor.execute("SELECT Rname,Location,Phno FROM restaurant")
        restaurants = cursor.fetchall()
        print("Fetched restaurants:", restaurants)
        cursor.close()
        db.close()

        # Render only the update restaurant HTML content (with restaurant data)
        return render_template('admin_dashboard.html', restaurants=restaurants)
    else:
        return redirect('/login')


# @app.route('/update_menu')
# def update_menu():
#     if 'username' in session and session.get('role') == 'admin':
#         return render_template('update_menu.html')  # Render the update menu page
#     else:
#         return redirect('/login')

# @app.route('/update_menu_item/<item_id>')
# def update_menu_item(item_id):
#     if 'username' in session and session.get('role') == 'admin':
#         # Fetch item details from database (item_id) and pass it to the template
#         return render_template('update_menu_item.html', item_id=item_id)
#     else:
#         return redirect('/login')

# Route to handle updating the menu item details@app.route('/save_menu_item/<item_id>', methods=['POST'])
def save_menu_item(item_id):
    if 'username' in session and session.get('role') == 'admin':
        # Process the form data and update the menu item in the database
        new_name = request.form['name']  # The new name of the menu item
        new_price = request.form['price']  # The new price of the menu item

        # Assuming you want to update the menu based on Res_ID (restaurant ID) and ItemID (menu item ID)
        res_id = request.form['res_id']  # This should be part of the form to specify the restaurant

        # Update in the database (example query)
        db = get_db_connection()
        cursor = db.cursor()

        # Assuming you're updating the menu item by the combination of Res_ID and ItemID
        cursor.execute("""
            UPDATE menu 
            SET Item_name = %s, Price = %s 
            WHERE Res_ID = %s AND ItemID = %s
        """, (new_name, new_price, res_id, item_id))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/update_menu')  # Redirect back to update menu page
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
        SELECT PassengerID, coach_no, Fname, Lname, Phone, email
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
    
    # Get a database connection
    db = get_db_connection()
    
    # Use the cursor from the connection object
    cursor = db.cursor()
    
    # Update the database with new values
    cursor.execute("""
        UPDATE passenger
        SET Fname = %s, Lname = %s, Phone = %s, email = %s
        WHERE PassengerID = %s
    """, (updated_fname, updated_lname, updated_phone, updated_email, passenger_id))
    
    # Commit the changes and close the cursor
    db.commit()
    cursor.close()

    # Redirect to the profile page after updating
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
    return redirect(url_for('menu', restaurant_id=restaurant_id))

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

    passenger_id = session.get('passenger_id')  # Retrieve PassengerID from session
    restaurant_id = session.get('RID')
    station_id = session.get('StationID')

    if not passenger_id or not restaurant_id or not station_id:
        return "Error: Missing required information.", 400

    # Find an available delivery person
    cursor.execute("SELECT DPID FROM deliveryperson LIMIT 1")
    dp_id = cursor.fetchone()
    if dp_id is None:
        return "Error: No delivery person available.", 400
    dp_id = dp_id[0]

    # Get order items from form data
    order_items = []
    for key, value in request.form.items():
        if key.startswith('quantity_') and int(value) > 0:
            item_name = key.split('quantity_')[1]
            order_items.append({'item_name': item_name, 'quantity': int(value)})

    if not order_items:
        return redirect(url_for('menu', restaurant_id=restaurant_id, error="No items selected"))

    try:
        order_id = str(uuid.uuid4())[:8]
        order_date = datetime.now().date()
        total_amount = 0

        # Calculate total price and gather item details
        for item in order_items:
            cursor.execute("SELECT Price, ItemID FROM menu WHERE Item_name = %s", (item['item_name'],))
            item_data = cursor.fetchone()
            if item_data is None:
                return f"Error: Item {item['item_name']} not found in menu.", 404
            
            price, item_id = item_data
            total_amount += price * item['quantity']
            item['item_id'] = item_id
            item['price'] = price

        # Insert the order with the correct Passenger_id
        cursor.execute(
            "INSERT INTO orders (OrderID, Order_date, DP_ID, R_ID, S_ID, Passenger_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_id, order_date, dp_id, restaurant_id, station_id, passenger_id)  # Use Passenger_id here
        )

        # Insert each item in the order
        for item in order_items:
            order_item_id = str(uuid.uuid4())[:8]
            cursor.execute(
                "INSERT INTO orderitems (OrdItemID, ItemPrice, quantity, Order_id, R_ID) VALUES (%s, %s, %s, %s, %s)",
                (order_item_id, item['price'], item['quantity'], order_id, restaurant_id)
            )

        db.commit()

        # Redirect to payment selection
        return redirect(url_for('payment_selection', order_id=order_id, total_amount=total_amount))

    except Exception as e:
        db.rollback()
        print("Error placing order:", e)
        return "Error placing order", 500
    finally:
        cursor.close()
        db.close()

@app.route('/payment_selection/<order_id>/<float:total_amount>', methods=['GET'])
def payment_selection(order_id, total_amount):
    return render_template('payment_selection.html', order_id=order_id, total_amount=total_amount)

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    order_id = request.form.get('order_id')
    payment_method = request.form.get('payment_method')
    
    if not order_id or not payment_method:
        return "Error: Missing order ID or payment method.", 400

    db = get_db_connection()
    cursor = db.cursor()
    
    payment_id = str(uuid.uuid4())[:8]  # Generate a unique payment ID
    payment_date = datetime.now().date()

    try:
        cursor.execute(
            "INSERT INTO payment (order_id, paymentID, payment_method, date) VALUES (%s, %s, %s, %s)",
            (order_id, payment_id, payment_method, payment_date)
        )
        db.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db.rollback()
        return "Error processing payment", 500
    finally:
        cursor.close()
        db.close()

    return render_template('payment_success.html', order_id=order_id, payment_method=payment_method)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_amount = sum(item['price'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
