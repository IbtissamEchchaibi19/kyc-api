from flask import request ,current_app ,jsonify ,g
from app.models.clients import  *
from  app.models.users import *
from  app.models.tokens import *
from  app.utils.send_emails import *
import jwt


def add_client():
    if g.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    company = data.get('company')
    email = data.get('email')

    if not company or not email:
        return jsonify({'error': 'Company and email are required'}), 400

    if client_exists(email):
        return jsonify({'error': 'Client already exists'}), 400

    result = create_client(company, email)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result), 201

def get_clients():
    if g.role != 'admin':  # Check if the user is an admin
        return jsonify({'error': 'Access denied'}), 403

    clients = get_all_clients()
    return jsonify({"clients": clients}), 200
def auto_login():
    data = request.json
    email = data.get('email')
    token = data.get('token')
    password = 'temporary_password'  # or some default value

    if not token or not email:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    try:
        # Decode the token
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

        # Check if the token has been used
        if is_token_used(token):
            return jsonify({"status": "error", "message": "Token has already been used"}), 400

        # Mark the token as used
        mark_token_as_used(token)

        # Create user or perform login action
        create_user(email, password, role='user')

        return jsonify({"status": "success"})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": "error", "message": "Token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"status": "error", "message": "Invalid token"}), 400
    except Exception as e:
        print(f"Error during auto-login: {e}")
        return jsonify({"status": "error", "message": "Failed to process login"}), 500
    
def send_client_emails():
    try:
        notify_all_clients()
        return jsonify({"success": "Emails sent to all clients"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def notify_all_clients():
    client_emails = get_all_client_emails()
    if not client_emails:
        print("No clients to notify")
        return
    
    for email in client_emails:
        try:
            login_link = generate_login_link(email)
            send_signup_email(email, login_link)
            print(f"Sent email to {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")
