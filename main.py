from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)

# Set configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)  # Secure secret key for session management and flash messages

app.permanent_session_lifetime = timedelta(minutes=30)  # Set session timeout to 30 minutes


# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Enum classes for order status, delicacies, and container sizes
class DelicacyType(PyEnum):
    SINUKMANI = "SINUKMANI"
    SAPIN_SAPIN = "SAPIN_SAPIN"
    PUTO = "PUTO"
    PUTO_ALSA = "PUTO_ALSA"
    KUTSINTA = "KUTSINTA"
    PUTO_KUTSINTA = "PUTO_KUTSINTA"
    MAJA = "MAJA"
    PICHI_PICHI = "PICHI_PICHI"
    PALITAW = "PALITAW"
    KARIOKA = "KARIOKA"
    SUMAN_MALAGKIT = "SUMAN_MALAGKIT"
    SUMAN_CASSAVA = "SUMAN_CASSAVA"
    SUMAN_LIHIA = "SUMAN_LIHIA"

class ContainerSize(PyEnum):
    BILAO_10 = "BILAO_10"
    BILAO_12 = "BILAO_12"
    BILAO_14 = "BILAO_14"
    BILAO_16 = "BILAO_16"
    BILAO_18 = "BILAO_18"
    TAB = "TAB"
    SLICE = "SLICE"

class OrderStatus(PyEnum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REMOVED = "Removed"

# User table definition
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    orders = relationship("Order", back_populates="user")

# Buyer information table
class BuyerInfo(db.Model):
    __tablename__ = 'buyer_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    orders = relationship("Order", back_populates="buyer")

# Orders table definition
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    buyer_id = db.Column(db.Integer, ForeignKey('buyer_info.id'), nullable=False)
    delicacy = db.Column(db.Enum(DelicacyType), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    container_size = db.Column(db.Enum(ContainerSize), nullable=False)
    special_request = db.Column(db.String(255))
    pickup_place = db.Column(db.String(255), nullable=False)
    pickup_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="orders")
    buyer = relationship("BuyerInfo", back_populates="orders")


# Create tables before the first request
@app.before_request
def create_tables():
    db.create_all()
    # Check if a user exists, create one if not
    if not User.query.first():
        default_user = User(
            username="admin", 
            password=bcrypt.generate_password_hash("password").decode('utf-8')
        )
        db.session.add(default_user)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']

        # Retrieve the first (and only) user from the database
        user = User.query.first()

        if user and bcrypt.check_password_hash(user.password, password) and user.username == username:
            
            return redirect(url_for('order_form'))  # Redirect to order form after login
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/order_form', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        # Retrieving form data
        name = request.form.get('customer_name')
        contact_number = request.form.get('contactNumber')
        address = request.form.get('address')
        pickup_place = request.form.get('pickupPlace')
        pickup_date = datetime.strptime(request.form.get('pickupDate'), "%Y-%m-%d")
        delicacy_display = request.form.get('delicacy')
        quantity = int(request.form.get('quantity', 1))  # Default to 1 if missing
        container_size = request.form.get('container')
        special_request = request.form.get('specialRequest', '')

        # Debugging: Print form data
        print(f"Form data before saving: {name}, {contact_number}, {address}, {pickup_place}, {pickup_date}, {delicacy_display}, {quantity}, {container_size}, {special_request}")

        # Retrieve or create buyer
        buyer = BuyerInfo.query.filter_by(
            name=name,
            contact_number=contact_number,
            address=address
        ).first()

        if not buyer:
            print(f"Creating new buyer: {name}")
            buyer = BuyerInfo(
                name=name,
                contact_number=contact_number,
                address=address
            )
            db.session.add(buyer)
            db.session.commit()

        # Sanitize and validate Enum values
        try:
            # Convert the input to uppercase and replace hyphens with underscores
            delicacy_display_cleaned = delicacy_display.strip().upper().replace("-", "_")
            container_display_cleaned = container_size.strip().upper().replace("-", "_")

            # Try to access the Enum values
            delicacy_display = DelicacyType[delicacy_display_cleaned]
            container_size = ContainerSize[container_display_cleaned]
        except KeyError as e:
            print(f"Enum value error: {e}")
            flash(f'Invalid enum value: {e}', 'error')
            return redirect(url_for('order_form'))

        # Create and add new order directly to the database
        new_order = Order(
            user_id=User.query.first().id,  # Assuming there's only one user, or use session-based user ID
            buyer_id=buyer.id,
            delicacy=delicacy_display,
            quantity=quantity,
            container_size=container_size,
            special_request=special_request,
            pickup_place=pickup_place,
            pickup_date=pickup_date,
            status=OrderStatus.PENDING
        )

        db.session.add(new_order)

        # Commit the transaction to save the order in the database
        try:
            db.session.commit()
            flash("Order submitted successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to the database: {e}")
            flash("Error submitting the order. Please try again.", 'error')

        return redirect(url_for('order_form'))  # Optionally redirect to the order form or other page

    return render_template('order_form.html')


# Comb Sort implementation
def comb_sort(orders, key_func, reverse=False):
    gap = len(orders)
    shrink_factor = 1.3
    swapped = True

    while gap > 1 or swapped:
        gap = int(gap / shrink_factor)
        if gap < 1:
            gap = 1
        
        swapped = False
        for i in range(len(orders) - gap):
            # Compare for ascending or descending order based on the reverse flag
            if (key_func(orders[i]) > key_func(orders[i + gap])) if not reverse else (key_func(orders[i]) < key_func(orders[i + gap])):
                orders[i], orders[i + gap] = orders[i + gap], orders[i]
                swapped = True

    return orders


# Flask route for order management with sorting
# Comb Sort implementation
from datetime import datetime

# Comb Sort implementation with reverse flag
def comb_sort(orders, key_func, reverse=False):
    gap = len(orders)
    shrink_factor = 1.3
    swapped = True

    while gap > 1 or swapped:
        gap = int(gap / shrink_factor)
        if gap < 1:
            gap = 1
        
        swapped = False
        for i in range(len(orders) - gap):
            # Compare for ascending or descending order based on the reverse flag
            if (key_func(orders[i]) > key_func(orders[i + gap])) if not reverse else (key_func(orders[i]) < key_func(orders[i + gap])):
                orders[i], orders[i + gap] = orders[i + gap], orders[i]
                swapped = True

    return orders


# Flask route for order management with sorting
@app.route('/order_management')
def order_management():
    sort_by = request.args.get('sort_by', default='pickup_date', type=str)
    
    # Validate the 'sort_by' parameter to ensure it is valid
    valid_sort_fields = ['pickup_date', 'delicacy', 'status']
    
    if sort_by not in valid_sort_fields:
        return "Invalid sort option!", 400  # Return error if invalid option is passed

     # Fetch orders that are NOT removed (no actual deletion from the database)
    orders = Order.query.filter(Order.status != OrderStatus.REMOVED).all()

    # Sort based on the 'pickup_date'
    if sort_by == 'pickup_date':
        # Get today's date for comparison
        today = datetime.today().date()

        # Separate orders into past and future
        past_orders = [order for order in orders if order.pickup_date <= today]
        future_orders = [order for order in orders if order.pickup_date > today]

        # Sort both lists (past orders in ascending order, future orders also in ascending order)
        past_orders = comb_sort(past_orders, lambda order: order.pickup_date)
        future_orders = comb_sort(future_orders, lambda order: order.pickup_date)

        # Combine past orders first, then future orders
        orders = past_orders + future_orders

    elif sort_by == 'delicacy':
        # Count orders for each delicacy
        delicacy_counts = {}
        for order in orders:
            delicacy_name = order.delicacy.name
            if delicacy_name not in delicacy_counts:
                delicacy_counts[delicacy_name] = 0
            delicacy_counts[delicacy_name] += 1

        # Create a frequency rank for each delicacy (numeric representation of how many orders)
        frequency_ranks = {delicacy: count for delicacy, count in delicacy_counts.items()}
        
        # Apply Comb Sort to orders based on the frequency of the delicacy (higher frequencies first)
        orders = comb_sort(orders, lambda order: frequency_ranks[order.delicacy.name], reverse=True)

    elif sort_by == 'status':
        # Apply Comb Sort to status (if numeric) or adjust if needed
        orders = comb_sort(orders, lambda order: order.status.name)

    return render_template('order_management.html', orders=orders)

@app.route('/remove_order/<int:order_id>', methods=['POST'])
def remove_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Mark the order as removed but don't delete it
    order.status = OrderStatus.REMOVED
    db.session.commit()

    return jsonify({"success": True})  # Return success response for AJAX

# Update an order (for the admin interface)
@app.route('/update_order/<int:orderId>', methods=['POST'])
def update_order(orderId):
    data = request.json  # Receive the JSON data
    order = Order.query.get(orderId)  # Get the order by ID

    if order:
        # Update each field with the received data
        order.buyer.name = data['customer_name']
        order.buyer.contact_number = data['contact_number']
        order.buyer.address = data['address']
        order.pickup_place = data['pickup_place']
        order.pickup_date = data['pickup_date']
        order.delicacy = data['delicacy']
        order.quantity = data['quantity']
        order.container_size = data['container']
        order.special_request = data['special_request']
        order.status = data['status']
        
        # Commit changes to the database
        db.session.commit()
        return jsonify(success=True, order=data)
    else:
        return jsonify(success=False, message="Order not found")

# Permanent delete the order
@app.route('/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)  # Permanently delete the order from the database
    db.session.commit()
    return '', 204  # No content, as the order is deleted

@app.route('/order_history')
def order_history():
    # Fetch all orders, including those marked as removed
    orders = Order.query.all()  # Get all orders, including removed ones

    # Debugging log to see the orders being fetched
    print(f"Orders fetched for history: {len(orders)} orders found.")
    for order in orders:
        print(f"Order ID: {order.id}, Status: {order.status.name}")

    return render_template('order_history.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)
