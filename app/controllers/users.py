from flask import request, current_app, jsonify
from app.models.users import find_user_by_username, create_user
from app.models.user_images import delete_user_images
import jwt
import datetime

def get_bcrypt():
    return current_app.extensions['bcrypt']

def create_users():
    data = request.json
    response, status = handle_create_user(data)
    return jsonify(response), status

def login():
    data = request.json
    response, status = handle_login(data)
    return jsonify(response), status

def create_google_user():
    data = request.json
    response, status = handle_google_user(data)
    
    if status == 201:
        # Create JWT token
        token = jwt.encode({
            'sub': data['username'],
            'role': 'user'
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        response['token'] = token  # Add token to response
        return jsonify(response), status

    return jsonify(response), status

def handle_create_user(data):
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default to 'user' if not provided

    if not username or not password:
        return {"error": "Missing username or password"}, 400

    # Check if the username already exists
    existing_user = find_user_by_username(username)
    if existing_user:
        return {"error": "Username already exists"}, 409  # Conflict status code

    result = create_user(username, password, role)
    return {"username": username}, 201

def handle_login(data):
    bcrypt = get_bcrypt()  # Get bcrypt inside the function
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Missing username or password"}, 400

    user = find_user_by_username(username)
    if user and bcrypt.check_password_hash(user['password'], password):
        token = jwt.encode({
            'sub': username,
            'role': user.get('role', 'user'),  # Include user role in the token
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return {"token": token, "role": user.get('role', 'user')}, 200
    else:
        return {"error": "Invalid username or password"}, 401
    
def handle_google_user(data):
    username = data.get('username')
    password = data.get('password')
    role = 'user'

    # Check if the username already exists
    existing_user = find_user_by_username(username)
    if existing_user:
        return {"error": "Username already exists"}, 409  # Conflict status code

    # Create the user with a default password or use a unique identifier
    result = create_user(username, password, role)
    return {"username": username}, 201

def get_user_data():
    from flask import g
    username = getattr(g, 'username', None)  # Retrieve username from g
    if not username:
        return jsonify({'error': 'User not found in request'}), 400

    user_data = {
        'username': username
    }

    return jsonify({'user_data': user_data}), 200

def admin_dashboard():
    from flask import g
    username = getattr(g, 'username', None)  # Retrieve username from g
    if not username or g.get('role') != 'admin':  # Check if the user is an admin
        return jsonify({'error': 'Access denied'}), 403

    # Fetch admin-specific data or render the admin dashboard
    return jsonify({
        
        'message': f'Welcome, {g.get('role')}!',  # Personalized message
        'username': username  # Include username in the response
    }), 200

def logout():
    from flask import g
    username = getattr(g, 'username', None)  # Retrieve username from g

    deleted_count = delete_user_images(username)

    if deleted_count > 0:
        # If images were deleted, return a success message
        return jsonify({'message': 'Logged out and images cleared successfully.'}), 200
    else:
        # If no images were found or deleted, just log the user out
        return jsonify({'message': 'Logged out successfully, but no images found for deletion.'}), 200
