from flask import Blueprint
from src.controllers.authController import register, login, getMe
from src.middleware.auth import auth

auth_bp = Blueprint('auth', __name__)

# Public 
@auth_bp.route('/register', methods=['POST'])
def register_route():
    return register()

@auth_bp.route('/login', methods=['POST'])
def login_route():
    return login()

# Protected
@auth_bp.route('/me', methods=['GET'])
@auth
def get_me_route():
    return getMe()
