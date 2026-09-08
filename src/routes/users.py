from flask import Blueprint, request, jsonify, g
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.services import user_service

users_bp = Blueprint('users', __name__)

# Protected - logged in user
@users_bp.route('/profile', methods=['GET'])
@auth
def get_profile():
    profile = user_service.get_profile(g.user['id'])
    return jsonify(profile)

# Protected - Admin
@users_bp.route('/', methods=['GET'])
@auth
@checkRole(ROLES['ADMIN'])
def get_all_users():
    return jsonify(user_service.get_all_users())

@users_bp.route('/<int:id>/role', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'])
def update_user_role(id):
    data = request.get_json()
    role = data.get('role')

    result, error = user_service.update_user_role(id, role)
    if error:
        return jsonify({'message': error['message']}), error['status']

    return jsonify(result)
