import functools

from flask import jsonify

from src.config.database import db
from src.utils.logger import logger


def handle_errors(func):
    """Wraps a controller function with the standard error-handling boilerplate
    that used to be copy-pasted into every controller's try/except:
    - roll back the DB session, so a failed commit can't leave it dirty for
      the next request (previously only createOrder did this)
    - log the exception via the shared logger
    - return the standard {'message': 'Server error', 'error': ...}, 500 shape

    Global/shared (src/utils) — used by every controller function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            db.session.rollback()
            logger.error(f'{func.__name__} failed', {'error': str(error)})
            return jsonify({'message': 'Server error', 'error': str(error)}), 500
    return wrapper
