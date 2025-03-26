from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import os
import psycopg2
import bcrypt
import random
from flask_mail import Mail, Message  # Import Flask-Mail   
from flask import abort

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.before_request
def restrict_direct_access():
    # List of routes that should not be accessed directly
    restricted_routes = ['/login', '/register','/forgot-password','/update-password','/verify-otp']

    # Check if the request path is in the restricted routes
    if request.path in restricted_routes:
        # Check if the request is coming from a form submission
        if not request.referrer or 'authenticate' not in request.referrer:
            abort(404)  # Trigger a 404 error if accessed directly via URL

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/some-protected-route')
def some_protected_route():
    # Check if the request is coming from a specific condition (e.g., not a form submission)
    if not request.referrer or 'authenticate' not in request.referrer:
        abort(404)  # Trigger a 404 error

    return "This is a protected route."

# Flask-Mail configuration for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'elevate.estate.india@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'vggf nlls qedt mjih'             # Your Gmail password or app-specific password
app.config['MAIL_DEFAULT_SENDER'] = 'elevate.estate.india@gmail.com'  # Default sender

# Initialize Flask-Mail
mail = Mail(app)

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="Real_Estate",
            user="postgres",
            password="root"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

# Password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Password verification
def check_password(stored_password, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_password.encode('utf-8'))

# Store OTPs temporarily (in production, use a database or cache)
otp_storage = {}


@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return render_template('index.html', popular_properties=[])

    try:
        cur = conn.cursor() 
        cur.execute("""
           SELECT 
                p.property_id,
                p.title,
                p.description,
                p.price,
                (SELECT pi.image_url 
                FROM property_images pi 
                WHERE pi.property_id = p.property_id 
                LIMIT 1) AS image_url,
                p.interests
            FROM properties p
            WHERE p.status = 'Available'
            ORDER BY p.interests DESC
            LIMIT 5;
        """)
        popular_properties = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching properties: {e}")
        popular_properties = []

    return render_template('index.html', popular_properties=popular_properties)

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if session.get('valid'):    
        return redirect(url_for('index'))

    auth_type = request.args.get('auth_type', 'login')
    return render_template('authenticate.html', auth_type=auth_type)

@app.route('/store_data_in_session', methods=['POST'])
def store_data_in_session():
    data = request.json  # Get data sent from JavaScript
    if not data:
        return jsonify({'success': False, 'message': 'No data provided.'})

    # Store data in Flask session
    session['redirect_url'] = data.get('redirect_url')
    return jsonify({'success': True, 'message': 'Data stored in session.'})

@app.route('/login', methods=['POST'])
def login():
    if not request.referrer or 'authenticate' not in request.referrer:
        abort(404)

    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed.'})

    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required.'})

    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            user_id, name, stored_password = user
            if check_password(stored_password, password):
                session['email'] = email  # Store email in session
                session['user_id'] = user_id
                session['name'] = name
                session['valid'] = True

                # Redirect to the stored URL (if any)
                redirect_url = session.pop('redirect_url', None)
                if redirect_url:
                    return jsonify({'success': True, 'redirect_url': redirect_url})
                else:
                    return jsonify({'success': True, 'redirect_url': url_for('index')})
            else:
                return jsonify({'success': False, 'message': 'Invalid Password.'})
        else:
            return jsonify({'success': False, 'message': 'Email entered is not registered.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/register', methods=['POST'])
def register():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed.'})

    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
    contact = request.json.get('contact')

    if not name or not email or not password or not contact:
        return jsonify({'success': False, 'message': 'All fields are required.'})

    hashed_password = hash_password(password)

    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered.'})

        cur.execute("INSERT INTO users (name, email, password, contact_no) VALUES (%s, %s, %s, %s) RETURNING user_id", 
                    (name, email, hashed_password, contact))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Registration successful. Redirecting to login...'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def fetch_all_properties():
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()
        # Query to fetch all properties along with their images
        cur.execute("""
            SELECT p.property_id, p.title, p.description, p.price, pi.image_url
            FROM properties p
            JOIN property_images pi ON p.property_id = pi.property_id
            WHERE p.status = 'Available'
        """)
        properties = cur.fetchall()
        cur.close()
        conn.close()
        return properties
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return []
    
@app.route('/properties', methods=['GET', 'POST'])
def properties():
    # Initialize variables
    search_query = ''
    properties = []
    no_results = False
    message = ''
    
    # Check for search query from home page (POST) or direct access (GET)
    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()
    else:
        search_query = request.args.get('search', '').strip()
    
    # Get filter options for dropdowns
    filter_options = get_filter_options()
    
    # Get filtered properties
    result = filter_properties(
        search_query=search_query,
        property_type=request.args.get('property_type'),
        state=request.args.get('state'),
        city=request.args.get('city'),
        min_price=request.args.get('min_price'),
        max_price=request.args.get('max_price'),
        page=request.args.get('page', 1, type=int)
    )
    
    # Handle results
    if result.get('success', False):
        properties = result.get('properties', [])
        no_results = len(properties) == 0
        if no_results:
            message = 'No properties found matching your criteria'
    else:
        no_results = True
        message = result.get('message', 'Error loading properties')
    
    return render_template(
        'properties.html',
        properties=properties,
        search_query=search_query,
        filter_options=filter_options,
        active_filters={
            'propertyType': request.args.get('property_type'),
            'state': request.args.get('state'),
            'city': request.args.get('city'),
            'minPrice': request.args.get('min_price'),
            'maxPrice': request.args.get('max_price')
        },
        pagination={
            'current': request.args.get('page', 1, type=int),
            'total': result.get('pages', 1)
        },
        no_results=no_results,
        message=message
    )

def filter_properties(search_query='', property_type=None, state=None, city=None, 
                    min_price=None, max_price=None, page=1, per_page=6):
    """
    Advanced property filtering with proper error handling
    """
    conn = get_db_connection()
    if conn is None:
        return {
            'success': False,
            'message': 'Database connection failed',
            'properties': [],
            'total': 0,
            'pages': 0
        }

    try:
        cur = conn.cursor()
        
        # Get min and max prices from database if not provided
        if min_price is None or max_price is None:
            cur.execute("SELECT MIN(price), MAX(price) FROM properties WHERE status = 'Available'")
            db_min_price, db_max_price = cur.fetchone()
            
            if min_price is None:
                min_price = db_min_price
            if max_price is None:
                max_price = db_max_price

        # Base query with joins
        base_query = """
            SELECT DISTINCT ON (p.property_id)
                p.property_id, p.title, p.description, p.price,
                (SELECT pi.image_url FROM property_images pi 
                 WHERE pi.property_id = p.property_id LIMIT 1) as image_url,
                pt.property_type_name, s.state_name, c.city_name
            FROM properties p
            JOIN Property_Type pt ON p.property_type_id = pt.property_type_id
            JOIN City c ON p.city_id = c.city_id
            JOIN State s ON c.state_id = s.state_id
            WHERE p.status = 'Available'
        """
        
        params = []
        filters = []
        
        # Search filter
        if search_query:
            filters.append("(p.title ILIKE %s OR p.description ILIKE %s)")
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])
        
        # Property type filter
        if property_type:
            filters.append("p.property_type_id = %s")
            params.append(property_type)
        
        # Location filters
        if city:
            filters.append("p.city_id = %s")
            params.append(city)
        elif state:
            filters.append("c.state_id = %s")
            params.append(state)
        
        # Price filters - ensure they're properly converted to float
        try:
            if min_price is not None and str(min_price).strip():
                min_price_val = float(min_price)
                filters.append("p.price >= %s")
                params.append(min_price_val)
            
            if max_price is not None and str(max_price).strip():
                max_price_val = float(max_price)
                filters.append("p.price <= %s")
                params.append(max_price_val)
        except ValueError as e:
            print(f"Error converting price values: {e}")
            return {
                'success': False,
                'message': 'Invalid price format',
                'properties': [],
                'total': 0,
                'pages': 0
            }
        
        # Apply filters
        if filters:
            base_query += " AND " + " AND ".join(filters)
        
        # Count query (for pagination)
        count_query = f"SELECT COUNT(*) FROM ({base_query}) AS count_query"
        
        # Add pagination to main query
        base_query += " ORDER BY p.property_id LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])
        
        # Execute count query (without LIMIT/OFFSET)
        cur.execute(count_query, params[:-2])
        total = cur.fetchone()[0]
        total_pages = max(1, (total + per_page - 1) // per_page)
        
        # Execute main query
        cur.execute(base_query, params)
        properties = [
            {
                'property_id': row[0],
                'title': row[1],
                'description': row[2],
                'price': float(row[3]),
                'image_url': row[4],
                'property_type': row[5],
                'state': row[6],
                'city': row[7]
            }
            for row in cur.fetchall()
        ]
        
        return {
            'success': True,
            'properties': properties,
            'total': total,
            'page': page,
            'pages': total_pages,
            'min_price': min_price,
            'max_price': max_price
        }
        
    except Exception as e:
        print(f"Error filtering properties: {e}")
        return {
            'success': False,
            'message': str(e),
            'properties': [],
            'total': 0,
            'pages': 0
        }
    finally:
        if conn:
            conn.close()

@app.route('/filter-options')
def get_filter_options():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed.'})

    try:
        cur = conn.cursor()
        
        # Get property types
        cur.execute("SELECT property_type_id, property_type_name FROM Property_Type")
        property_types = [{'property_type_id': row[0], 'property_type_name': row[1]} for row in cur.fetchall()]
        
        # Get states
        cur.execute("SELECT state_id, state_name FROM State")
        states = [{'state_id': row[0], 'state_name': row[1]} for row in cur.fetchall()]
        
        # Get cities with their state IDs
        cur.execute("SELECT city_id, city_name, state_id FROM City")
        cities = [{'city_id': row[0], 'city_name': row[1], 'state_id': row[2]} for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'propertyTypes': property_types,
            'states': states,
            'cities': cities
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/properties-data', methods=['POST'])
def properties_data():
    # Get all filter parameters from form data
    search_query = request.form.get('search', '').strip()
    property_type = request.form.get('property_type')
    state = request.form.get('state')
    city = request.form.get('city')
    min_price = request.form.get('min_price')
    max_price = request.form.get('max_price')
    page = request.form.get('page', 1, type=int)
    
    # Get filtered properties
    result = filter_properties(
        search_query=search_query,
        property_type=property_type,
        state=state,
        city=city,
        min_price=min_price,
        max_price=max_price,
        page=page
    )
    
    return jsonify(result)

@app.route('/property_details')
def property_details():
    property_id = request.args.get('property_id')
    if not property_id:
        print("Property ID Not Found")
        abort(404)  # Redirect to 404 page

    conn = get_db_connection()
    if conn is None:
        abort(404)  # Redirect to 404 page if database connection fails

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.property_id, p.title, p.description, p.price, c.city_name, 
                COALESCE(ARRAY_AGG(pi.image_url), '{}') AS images
            FROM properties p
            LEFT JOIN property_images pi ON p.property_id = pi.property_id
            LEFT JOIN city c ON p.city_id = c.city_id
            WHERE p.property_id = %s
            GROUP BY p.property_id, c.city_name
        """, (property_id,))
        property = cur.fetchone()
        cur.close()
        conn.close()

        if property:
            # Convert the property tuple to a dictionary for easier access in the template
            property_dict = {
                'property_id': property[0],
                'title': property[1],
                'description': property[2],
                'price': property[3],
                'city': property[4],
                'images': property[5]
            }
            # Debugging: Print property_dict to the console
            print("Property Dictionary:", property_dict)
            return render_template('property_details.html', property=property_dict)
        else:
            print("No property found for property_id:", property_id)
            abort(404)
    except Exception as e:
        print(f"Error fetching property details: {e}")
        abort(404)  # Redirect to 404 page if an error occurs

@app.route('/increment-interest', methods=['POST'])
def increment_interest():
    property_id = request.json.get('property_id')
    if not property_id:
        return jsonify({'success': False, 'message': 'Property ID is required'})

    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed'})

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE properties 
            SET interests = interests + 1 
            WHERE property_id = %s
            RETURNING interests
        """, (property_id,))
        
        updated_interests = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Interest count updated',
            'interests': updated_interests
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            conn.close()
            
            
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed.'})

    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({'success': False, 'message': 'Email not found.'})

        # Generate a random 6-digit OTP
        otp = str(random.randint(100000, 999999))
        otp_storage[email] = otp

        # Send OTP to email using Flask-Mail
        msg = Message(
            subject="Password Reset OTP",
            recipients=[email],
            body=f"Your OTP is: {otp}"
        )
        mail.send(msg)

        return jsonify({'success': True, 'message': 'OTP sent to your email.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email = request.json.get('email')
    otp = request.json.get('otp')
    if not otp:
        return jsonify({'success': False, 'message': 'Enter OTP'})
    if email in otp_storage and otp_storage[email] == otp:
        return jsonify({'success': True, 'message': 'OTP verified.'})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP.'})

@app.route('/update-password', methods=['POST'])
def update_password():
    email = request.json.get('email')
    new_password = request.json.get('new_password')

    conn = get_db_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed.'})

    # Check if new password is empty
    if not new_password or new_password.strip() == '':
        return jsonify({'success': False, 'message': 'Password cannot be blank.'})

    try:
        hashed_password = hash_password(new_password)
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()
        cur.close()
        conn.close()

        # Clear OTP from storage
        if email in otp_storage:
            del otp_storage[email]

        return jsonify({'success': True, 'message': 'Password updated successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == "__main__":
    app.run(debug=True)