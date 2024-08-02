from flask import Blueprint
from  app.controllers.clients import add_client, get_clients, auto_login, send_client_emails
from  app.utils.authorization import token_required

client_bp = Blueprint('client', __name__)

@client_bp.route('/add_client', methods=['POST'])
@token_required
def add_client_route():
    return add_client()

@client_bp.route('/clients', methods=['GET'])
@token_required
def get_clients_route():
    return get_clients()

@client_bp.route('/auto-login', methods=['POST'])
def auto_login_route():
    return auto_login()

@client_bp.route('/send-client-emails', methods=['POST'])
@token_required
def send_client_emails_route():
    return send_client_emails()
