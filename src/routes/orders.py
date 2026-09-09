from flask import Blueprint, request, jsonify, g
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.services import order_service
from src.utils.error_handler import handle_errors

orders_bp = Blueprint('orders', __name__)


def _error_response(error):
    return jsonify({'message': error['message']}), error['status']


# Customers - only own orders
# Admin/Manager sees all
@orders_bp.route('/', methods=['GET'])
@auth
@handle_errors
def get_all_orders_route():
    result = order_service.list_orders_for_user(g.user['id'], g.user['role'])
    return jsonify(result)

@orders_bp.route('/privet', methods=['GET'])
@auth
@handle_errors
def get_all_user_orders_route():
    result = order_service.list_own_orders(g.user['id'])
    return jsonify(result)

# Specific details of one order
@orders_bp.route('/<int:id>', methods=['GET'])
@auth
@handle_errors
def get_order_by_id_route(id):
    result, error = order_service.get_order_by_id(id, g.user['id'], g.user['role'])
    if error:
        return _error_response(error)
    return jsonify(result)

# "Checkout"
@orders_bp.route('/', methods=['POST'])
@auth
@handle_errors
def create_order_route():
    data = request.get_json()
    result, error = order_service.create_order(
        g.user['id'],
        data.get('items', []),
        data.get('address'),
    )
    if error:
        return _error_response(error)
    return jsonify(result), 201

# Update status
@orders_bp.route('/<int:id>', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def update_order_status_route(id):
    data = request.get_json()
    result, error = order_service.update_order_status(id, data.get('status'))
    if error:
        return _error_response(error)
    return jsonify(result)

# Delete order
@orders_bp.route('/<int:id>', methods=['DELETE'])
@auth
@checkRole(ROLES['ADMIN'])
@handle_errors
def delete_order_route(id):
    result, error = order_service.delete_order(id)
    if error:
        return _error_response(error)
    return jsonify(result)
