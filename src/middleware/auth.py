import json
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from src.models.User import User

def auth(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):      
        identity = get_jwt_identity()
        
        # Parse JSON string if needed (from user_identity_loader)
        if isinstance(identity, str):
            try:
                identity = json.loads(identity)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Handle both dict and simple ID formats
        user_id = identity.get('id') if isinstance(identity, dict) else identity
        
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