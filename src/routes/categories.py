from flask import Blueprint
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.controllers.category_controller import (
    createCategory,
    getCategoryTree,
    getAllCategories,
    getProductsByCategory,
    getCategoryBySlug
)

categories_bp = Blueprint('categories', __name__)

# Public 
@categories_bp.route('/tree', methods=['GET'])
def get_category_tree_route():
    return getCategoryTree()

@categories_bp.route('/<slug>', methods=['GET'])
def get_category_by_slug_route(slug):
    return getCategoryBySlug(slug)

@categories_bp.route('/<slug>/products', methods=['GET'])
def get_products_by_category_route(slug):
    return getProductsByCategory(slug)

# Protected (Admin , Manager)
@categories_bp.route('/', methods=['POST'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
def create_category_route():
    return createCategory()
