from src.models.Product import Product
from src.models.Category import Category
from src.config.database import db
from src.utils.logger import logger
from src.utils.validators import required_string, positive_number, max_length
from src.middleware.multer import save_uploaded_file


def validateProduct(data):
    """Local (products-specific). Returns a list of field-error dicts (empty if valid)."""
    errors = [
        required_string(data.get('name'), 'name', min_len=3, max_len=100),
        positive_number(data.get('price', 0), 'price'),
        positive_number(data.get('categoryId', 0), 'categoryId', integer=True,
                         message='Valid category ID required'),
        max_length(data.get('description', ''), 'description', 1000,
                   message='Description too long (max 1000 chars)'),
    ]

    # Stock validation (only if provided)
    if data.get('stock') is not None:
        errors.append(positive_number(data.get('stock', 0), 'stock', allow_zero=True, integer=True,
                                       message='Stock must be 0 or positive'))

    return [e for e in errors if e]


def list_products(page=1, limit=10, search=None, categoryId=None, minPrice=None, maxPrice=None):
    """Search/filter/paginate products. Local (products-specific)."""
    offset = (page - 1) * limit

    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    if categoryId:
        query = query.filter(Product.categoryId == int(categoryId))

    if minPrice:
        query = query.filter(Product.price >= float(minPrice))
    if maxPrice:
        query = query.filter(Product.price <= float(maxPrice))

    count = query.count()

    products = query.order_by(Product.createdAt.desc()).offset(offset).limit(limit).all()

    return {
        'products': [p.to_dict(include_category=True) for p in products],
        'pagination': {
            'total': count,
            'page': page,
            'limit': limit,
            'totalPages': (count + limit - 1) // limit if count > 0 else 0
        }
    }


def get_product_by_id(id):
    """Local (products-specific). Returns (result, error)."""
    product = Product.query.filter_by(id=id).first()
    if not product:
        return None, {'status': 404, 'message': 'Product not found'}
    return product.to_dict(include_category=True), None


def create_product(data, image_file=None, image360_file=None):
    """Create a product, optionally saving an image / 360 image.

    Local (products-specific). `image_file`/`image360_file` are the
    werkzeug `FileStorage` objects already pulled out of `request.files` by
    the route (services stay flask.request-free). Returns (result, error).
    """
    errors = validateProduct(data)
    if errors:
        return None, {'status': 400, 'message': 'Validation failed', 'errors': errors}

    name = data.get('name', '').strip()
    categoryId = int(data.get('categoryId'))
    description = data.get('description', '').strip() if data.get('description') else None
    price = float(data.get('price'))
    stock = int(data.get('stock', 0))

    category = Category.query.filter_by(id=categoryId).first()
    if not category:
        return None, {'status': 400, 'message': 'Invalid category ID'}

    image = None
    image360 = None

    if image_file is not None:
        try:
            image = save_uploaded_file(image_file)
        except ValueError as e:
            return None, {'status': 400, 'message': str(e)}

    if image360_file is not None:
        try:
            image360 = save_uploaded_file(image360_file)
        except ValueError as e:
            return None, {'status': 400, 'message': str(e)}

    newProduct = Product(
        name=name,
        categoryId=categoryId,
        description=description,
        price=price,
        stock=stock,
        image=image,
        image360=image360
    )

    db.session.add(newProduct)
    db.session.commit()

    logger.info('Product created', {'productId': newProduct.id, 'name': name})

    return {
        'message': 'Product created successfully',
        'product': newProduct.to_dict(include_category=True)
    }, None


def update_product(id, data, image_file=None, image360_file=None,
                    removeImage=None, removeImage360=None):
    """Local (products-specific). Returns (result, error)."""
    product = Product.query.filter_by(id=id).first()
    if not product:
        return None, {'status': 404, 'message': 'Product not found'}

    name = data.get('name')
    categoryId = data.get('categoryId')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')

    if categoryId:
        category = Category.query.filter_by(id=int(categoryId)).first()
        if not category:
            return None, {'status': 400, 'message': 'Invalid category ID'}

    if name:
        product.name = name.strip()
    if categoryId:
        product.categoryId = int(categoryId)
    if description is not None:
        product.description = description.strip() if description else product.description
    if price:
        product.price = float(price)
    if stock is not None:
        product.stock = int(stock)

    if image_file is not None:
        try:
            product.image = save_uploaded_file(image_file)
        except ValueError as e:
            return None, {'status': 400, 'message': str(e)}
    elif removeImage == 'true':
        product.image = None

    if image360_file is not None:
        try:
            product.image360 = save_uploaded_file(image360_file)
        except ValueError as e:
            return None, {'status': 400, 'message': str(e)}
    elif removeImage360 == 'true':
        product.image360 = None

    db.session.commit()

    return {
        'message': 'Product updated successfully',
        'product': product.to_dict(include_category=True)
    }, None


def delete_product(id):
    """Local (products-specific). Returns (result, error)."""
    product = Product.query.filter_by(id=id).first()
    if not product:
        return None, {'status': 404, 'message': 'Product not found'}

    productId = product.id
    db.session.delete(product)
    db.session.commit()

    logger.info('Product deleted', {'productId': productId})

    return {
        'message': 'Product deleted successfully',
        'deletedId': str(id)
    }, None
