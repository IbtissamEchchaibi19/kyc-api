from flask import Blueprint, request
from  app.controllers.users import create_users, login, logout, admin_dashboard, create_google_user, get_user_data
from  app.utils.authorization import token_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/create_user', methods=['POST'])
def create_user_route():
    return create_users()

@user_bp.route('/create_google_user', methods=['POST'])
def create_google_user_route():
    return create_google_user()

@user_bp.route('/login', methods=['POST'])
def login_route():
    return login()

@user_bp.route('/admin_dashboard', methods=['GET'])
@token_required
def admin_dashboard_route():
    return admin_dashboard()

@user_bp.route('/dashboard', methods=['GET'])
@token_required
def get_user_data_route():
    return get_user_data()


@user_bp.route('/logout', methods=['POST'])
def logout_route():
    return logout()