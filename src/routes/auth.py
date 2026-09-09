from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from src.middleware.auth import auth
from src.services import auth_service
from src.utils.error_handler import handle_errors

auth_bp = Blueprint('auth', __name__)


def _error_response(error):
    body = {'message': error['message']}
    if 'errors' in error:
        body['errors'] = error['errors']
    return jsonify(body), error['status']


# Public
@auth_bp.route('/register', methods=['POST'])
@handle_errors
def register_route():
    data = request.get_json()
    result, error = auth_service.register_user(data)
    if error:
        return _error_response(error)
    return jsonify(result), 201

@auth_bp.route('/login', methods=['POST'])
@handle_errors
def login_route():
    data = request.get_json()
    result, error = auth_service.login_user(data)
    if error:
        return _error_response(error)
    return jsonify(result)

# Protected
@auth_bp.route('/me', methods=['GET'])
@auth
@handle_errors
def get_me_route():
    result, error = auth_service.get_me(get_jwt_identity())
    if error:
        return _error_response(error)
    return jsonify(result)
