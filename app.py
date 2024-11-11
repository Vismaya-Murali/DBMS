import random
import string
from flask import Flask, flash, render_template, request, redirect, session, url_for , jsonify
import mysql.connector
import base64
import uuid
from datetime import datetime
import json

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
        # Store username, PassengerID, and role in the session
        session['username'] = username
        session['passenger_id'] = user[0]  # Store PassengerID in the session
        session['role'] = 'admin' if user[1] == 1 else 'user'  # Set role based on is_admin value
        
        # Redirect based on the role
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
        cursor.execute("SELECT Rname, Location, Phno, RID FROM restaurant")
        restaurants = cursor.fetchall()

        # Fetch menu items for each restaurant, including image data
        menu_items = {}
        for restaurant in restaurants:
            restaurant_id = restaurant[3]  # Assuming 'RID' is the 4th field (Res_ID)
            cursor.execute("SELECT Item_name, Price, Image FROM menu WHERE Res_ID = %s", (restaurant_id,))
            menu_items[restaurant_id] = []
            
            # Convert Image data to Base64 if it exists
            for item in cursor.fetchall():
                item_name, price, image_data = item
                if image_data:
                    # Convert binary image data to Base64 string
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    image_base64 = None  # Handle case where no image data is available
                menu_items[restaurant_id].append((item_name, price, image_base64))

        cursor.close()
        db.close()

        # Pass both restaurants and menu items to the template
        return render_template('admin_dashboard.html', restaurants=restaurants, menu_items=menu_items)
    else:
        return redirect('/login')

@app.route('/delete_menu_item', methods=['POST'])
def delete_menu_item():
    try:
        data = request.get_json()  # Get the JSON data sent by the client
        item_name = data['item_name']
        price = data['price']
        restaurant_id = data['restaurant_id']
        
        db = get_db_connection()
        cursor = db.cursor()

        # Delete the item from the menu table
        cursor.execute("DELETE FROM menu WHERE Res_ID = %s AND Item_name = %s AND Price = %s", 
                       (restaurant_id, item_name, price))
        
        db.commit()  # Commit the changes to the database
        
        cursor.close()
        db.close()
        
        return jsonify({'success': True})  # Return a success response
    
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)})  # Return an error response in case of failure


@app.route('/update_restaurant', methods=['GET', 'POST'])
def update_restaurant():
    if 'username' in session and session.get('role') == 'admin':
        # Fetch all restaurant data from the database
        db = get_db_connection()
        cursor = db.cursor()

        # Query to get all restaurant details
        cursor.execute("SELECT Rname,Location,Phno,RID FROM restaurant")
        restaurants = cursor.fetchall()
        print("Fetched restaurants:", restaurants)
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

@app.route('/update_menu_item', methods=['POST'])
def update_menu_item():
    if 'username' in session and session.get('role') == 'admin':
        restaurant_id = request.form.get('restaurant_id')
        item_id = request.form.get('item_id')
        item_name = request.form.get('item_name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')  # Get the quantity input
        image_file = request.files.get('image')

        db = get_db_connection()
        cursor = db.cursor()

        # Prepare the image data if an image file was uploaded
        image_data = None
        if image_file:
            image_data = image_file.read()

        try:
            # Check if the item with this ItemID exists in the menu for the specified restaurant
            cursor.execute("SELECT ItemID FROM menu WHERE Res_ID = %s AND ItemID = %s", (restaurant_id, item_id))
            existing_item = cursor.fetchone()

            if existing_item:
                # If the item exists, update the quantity and other fields
                cursor.execute("""
                    UPDATE menu
                    SET Item_name = %s, Price = %s, Image = %s, Quantity = %s
                    WHERE Res_ID = %s AND ItemID = %s
                """, (item_name, price, image_data, quantity, restaurant_id, item_id))

                db.commit()
                return jsonify({"success": True, "message": "Menu item successfully updated."})

            else:
                # Insert new item if it does not exist
                cursor.execute("""
                    INSERT INTO menu (Res_ID, ItemID, Item_name, Price, Image, Quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (restaurant_id, item_id, item_name, price, image_data, quantity))

                db.commit()
                return jsonify({"success": True, "message": "Menu item successfully added."})

        except Exception as e:
            db.rollback()
            return jsonify({"success": False, "message": f"An error occurred: {e}"})

        finally:
            cursor.close()
            db.close()
    else:
        return jsonify({"success": False, "message": "Unauthorized access."})


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

        # Insert the order with the correct Passenger_id
        cursor.execute(
            "INSERT INTO orders (OrderID, Order_date, DP_ID, R_ID, S_ID, Passenger_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (order_id, order_date, dp_id, restaurant_id, station_id, passenger_id)
        )

        # Insert each item in the order into orderitems table
        for item in order_items:
            # Find the ItemID and Price from the menu table
            cursor.execute("SELECT ItemID, Price FROM menu WHERE Item_name = %s AND Res_ID = %s", 
                           (item['item_name'], restaurant_id))
            item_data = cursor.fetchone()
            if item_data is None:
                return f"Error: Item {item['item_name']} not found in menu.", 404

            item_id, price = item_data
            order_item_id = str(uuid.uuid4())[:8]

            # Insert into orderitems table
            cursor.execute(
                "INSERT INTO orderitems (OrdItemID, ItemPrice, quantity, Order_id, R_ID, ItemID) VALUES (%s, %s, %s, %s, %s, %s)",
                (order_item_id, price, item['quantity'], order_id, restaurant_id, item_id)
            )

        db.commit()

        # Use the SQL function to calculate the total price for the order
        cursor.execute("SELECT CalculateTotalPrice(%s)", (order_id,))
        total_amount = cursor.fetchone()[0]

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
    flash("You have been logged out.", "info")
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
