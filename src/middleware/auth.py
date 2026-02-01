# Exact translation of src/middleware/auth.js
import os
import jwt
from functools import wraps
from flask import request, jsonify, g
from src.models.User import User

def auth(f):
    """
    Authentication Middleware
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from the header (format: Bearer <token>)
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'No token, authorization denied'}), 401
        
        try:
            # Verify token signature and decode payload
            decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            
            # Fetch FRESH user data from database (including current role)
            user = User.query.filter_by(id=decoded['id']).first()
            
            # Handle case where user was deleted after token was issued
            if not user:
                return jsonify({'message': 'User no longer exists'}), 401
            
            # Attach CURRENT database values to request (not token values)
            g.user = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is not valid'}), 401
    
    return decorated_function
