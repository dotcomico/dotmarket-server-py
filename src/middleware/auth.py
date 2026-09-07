from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from src.models.User import User
from src.utils.jwt_identity import resolve_user_id

def auth(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = resolve_user_id(get_jwt_identity())

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User no longer exists'}), 401
        
        g.user = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
        
        return f(*args, **kwargs)
    
    return decorated_function