from flask import Blueprint, request, jsonify, g
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.models.User import User
from src.config.database import db

users_bp = Blueprint('users', __name__)

# Protected - logged in user
@users_bp.route('/profile', methods=['GET'])
@auth
def get_profile():
    user = User.query.filter_by(id=g.user['id']).first()
    return jsonify(user.to_dict(exclude_password=True))

# Protected - Admin
@users_bp.route('/', methods=['GET'])
@auth
@checkRole(ROLES['ADMIN'])
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict(exclude_password=True) for u in users])

@users_bp.route('/<int:id>/role', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'])
def update_user_role(id):
    data = request.get_json()
    role = data.get('role')
    
    if role not in ROLES.values():
        return jsonify({'message': 'Invalid role'}), 400
    
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    user.role = role
    db.session.commit()
    
    return jsonify({'message': 'User role updated successfully'})
