from flask import Blueprint
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from controllers.order_controller import (
    getAllOrders,
    getAllUserOrders,
    getOrderById,
    createOrder,
    updateOrderStatus,
    deleteOrder
)

orders_bp = Blueprint('orders', __name__)

# Customers - only own orders
# Admin/Manager sees all
@orders_bp.route('/', methods=['GET'])
@auth
def get_all_orders_route():
    return getAllOrders()

@orders_bp.route('/privet', methods=['GET'])
@auth
def get_all_user_orders_route():
    return getAllUserOrders()

# Specific details of one order
@orders_bp.route('/<int:id>', methods=['GET'])
@auth
def get_order_by_id_route(id):
    return getOrderById(id)

# "Checkout" 
@orders_bp.route('/', methods=['POST'])
@auth
def create_order_route():
    return createOrder()

# Update status
@orders_bp.route('/<int:id>', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
def update_order_status_route(id):
    return updateOrderStatus(id)

# Delete order
@orders_bp.route('/<int:id>', methods=['DELETE'])
@auth
@checkRole(ROLES['ADMIN'])
def delete_order_route(id):
    return deleteOrder(id)
