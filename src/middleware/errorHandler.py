from functools import wraps
from flask import jsonify

def asyncHandler(f):
  # catches exceptions , passes to error handler
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # for global error handler
            raise e
    return decorated_function
