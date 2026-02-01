from functools import wraps
from flask import jsonify, g

def checkRole(*allowedRoles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user') or not g.user:
                return jsonify({'message': 'Unauthorized: No user found'}), 401
            
            if g.user['role'] not in allowedRoles:
                return jsonify({
                    'message': f"Access Denied: {g.user['role']} role does not have permission."
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
