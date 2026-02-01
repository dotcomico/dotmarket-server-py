from flask import Blueprint
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from controllers.product_controller import (
    getAllProducts,
    getProductById,
    createProduct,
    updateProduct,
    deleteProduct
)

products_bp = Blueprint('products', __name__)

# Public
@products_bp.route('/', methods=['GET'])
def get_all_products_route():
    return getAllProducts()

@products_bp.route('/<int:id>', methods=['GET'])
def get_product_by_id_route(id):
    return getProductById(id)

# Protected - Admin / Manager 
@products_bp.route('/', methods=['POST'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
def create_product_route():
    return createProduct()

@products_bp.route('/<int:id>', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
def update_product_route(id):
    return updateProduct(id)

@products_bp.route('/<int:id>', methods=['DELETE'])
@auth
@checkRole(ROLES['ADMIN'])
def delete_product_route(id):
    return deleteProduct(id)
