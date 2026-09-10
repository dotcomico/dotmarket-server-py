from flask import Blueprint, request, jsonify
from src.middleware.auth import auth
from src.middleware.checkRole import checkRole
from src.config.constants import ROLES
from src.services import product_service
from src.utils.error_handler import handle_errors

products_bp = Blueprint('products', __name__)


def _error_response(error):
    body = {'message': error['message']}
    if 'errors' in error:
        body['errors'] = error['errors']
    return jsonify(body), error['status']


def _parse_body():
    """multipart/form-data (file uploads) or plain JSON — same contract as before."""
    if request.content_type and 'multipart/form-data' in request.content_type:
        return request.form.to_dict()
    return request.get_json() or {}


# Public
@products_bp.route('/', methods=['GET'])
@handle_errors
def get_all_products_route():
    result = product_service.list_products(
        page=int(request.args.get('page', 1)),
        limit=min(int(request.args.get('limit', 10)), 100),
        search=request.args.get('search'),
        categoryId=request.args.get('categoryId'),
        minPrice=request.args.get('minPrice'),
        maxPrice=request.args.get('maxPrice'),
    )
    return jsonify(result)

# Protected - Admin / Manager
# Declared before the '/<int:id>' rule so a literal path segment is never
# swallowed by the id rule (the int converter would not match 'stats' anyway,
# but the ordering keeps that guarantee explicit).
@products_bp.route('/stats', methods=['GET'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def get_product_stats_route():
    return jsonify(product_service.get_product_stats())

@products_bp.route('/<int:id>', methods=['GET'])
@handle_errors
def get_product_by_id_route(id):
    result, error = product_service.get_product_by_id(id)
    if error:
        return _error_response(error)
    return jsonify(result)

# Protected - Admin / Manager
@products_bp.route('/', methods=['POST'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def create_product_route():
    data = _parse_body()
    result, error = product_service.create_product(
        data,
        image_file=request.files.get('image'),
        image360_file=request.files.get('image360'),
    )
    if error:
        return _error_response(error)
    return jsonify(result), 201

@products_bp.route('/<int:id>', methods=['PUT'])
@auth
@checkRole(ROLES['ADMIN'], ROLES['MANAGER'])
@handle_errors
def update_product_route(id):
    data = _parse_body()
    result, error = product_service.update_product(
        id,
        data,
        image_file=request.files.get('image'),
        image360_file=request.files.get('image360'),
        removeImage=data.get('removeImage'),
        removeImage360=data.get('removeImage360'),
    )
    if error:
        return _error_response(error)
    return jsonify(result)

@products_bp.route('/<int:id>', methods=['DELETE'])
@auth
@checkRole(ROLES['ADMIN'])
@handle_errors
def delete_product_route(id):
    result, error = product_service.delete_product(id)
    if error:
        return _error_response(error)
    return jsonify(result)
