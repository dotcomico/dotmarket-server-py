from flask import Blueprint, request, jsonify
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.services import category_service
from src.utils.error_handler import handle_errors

categories_bp = Blueprint('categories', __name__)


def _error_response(error):
    # category_service errors carry either 'message' or 'error' as the body
    # key, matching the pre-refactor controller exactly (not unified here).
    body = {k: v for k, v in error.items() if k != 'status'}
    return jsonify(body), error['status']


def _parse_body():
    """multipart/form-data (file uploads) or plain JSON — same contract as before."""
    if request.content_type and 'multipart/form-data' in request.content_type:
        return request.form.to_dict()
    return request.get_json() or {}


# Public Routes
@categories_bp.route('/tree', methods=['GET'])
@handle_errors
def get_category_tree_route():
    return jsonify(category_service.get_category_tree())

@categories_bp.route('/', methods=['GET'])
@handle_errors
def get_all_categories_route():
    return jsonify(category_service.get_all_categories())

@categories_bp.route('/<slug>', methods=['GET'])
@handle_errors
def get_category_by_slug_route(slug):
    result, error = category_service.get_category_by_slug(slug)
    if error:
        return _error_response(error)
    return jsonify(result)

@categories_bp.route('/<slug>/products', methods=['GET'])
@handle_errors
def get_products_by_category_route(slug):
    result, error = category_service.get_products_by_category(
        slug,
        page=int(request.args.get('page', 1)),
        limit=min(int(request.args.get('limit', 20)), 100),
        minPrice=request.args.get('minPrice'),
        maxPrice=request.args.get('maxPrice'),
        search=request.args.get('search'),
    )
    if error:
        return _error_response(error)
    return jsonify(result)

# Protected - Admin/Manager
@categories_bp.route('/', methods=['POST'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def create_category_route():
    data = _parse_body()
    result, error = category_service.create_category(
        data,
        image_file=request.files.get('image'),
    )
    if error:
        return _error_response(error)
    return jsonify(result), 201

@categories_bp.route('/<int:id>', methods=['GET'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def get_category_by_id_route(id):
    result, error = category_service.get_category_by_id(id)
    if error:
        return _error_response(error)
    return jsonify(result)

@categories_bp.route('/<int:id>', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def update_category_route(id):
    data = _parse_body()
    result, error = category_service.update_category(
        id,
        data,
        image_file=request.files.get('image'),
    )
    if error:
        return _error_response(error)
    return jsonify(result)

@categories_bp.route('/<int:id>', methods=['DELETE'])
@auth
@checkRole(ROLES['ADMIN'])
@handle_errors
def delete_category_route(id):
    result, error = category_service.delete_category(id)
    if error:
        return _error_response(error)
    return jsonify(result)
