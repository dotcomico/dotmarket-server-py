from sqlalchemy import case, func

from src.models.Product import Product
from src.models.Category import Category
from src.config.constants import LOW_STOCK_PREVIEW_LIMIT, LOW_STOCK_THRESHOLD
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


def get_product_stats():
    """Dataset-wide inventory aggregates for the admin dashboard.

    Local (products-specific). Returns a plain dict (no error tuple — there is
    no failure mode other than an infra error, which `@handle_errors` covers).

    Everything is computed by SQL in a **single** query with conditional
    aggregates; the products are deliberately never loaded into Python. The
    dashboard used to derive these numbers from one paginated page of products,
    which is exactly the bug this replaces.

    Definitions:
    - `lowStockCount` — `stock < LOW_STOCK_THRESHOLD`. This **includes**
      out-of-stock rows (stock 0 is < 10), matching what the dashboard has
      always shown; `outOfStockCount` is therefore a subset of it, not a
      disjoint bucket.
    - `outOfStockCount` — `stock <= 0`.
    - `inventoryValue` — `SUM(price * stock)`, rounded to 2 decimals.
      `SUM` returns NULL on an empty table in SQLite, so it is coalesced to 0.
    - `lowStockThreshold` is returned in the payload so the frontend renders
      the same threshold the backend filtered on instead of re-hardcoding it.
    - `lowStockProducts` — the worst `LOW_STOCK_PREVIEW_LIMIT` offenders for the
      dashboard's "Low Stock Alert" panel, ordered by stock ASC then name ASC
      (the name tie-break keeps the list stable across requests). It is a
      capped *preview*: `lowStockCount` stays the full count, so the panel can
      honestly render "5 of 7". Always a list, never null.

    Cost: two bounded queries — one aggregate row, plus one `LIMIT`ed select.
    Only the four fields the panel actually renders (`id`, `name`, `stock`,
    `price`) are projected, rather than reusing `Product.to_dict()`, so the
    payload doesn't carry `description` (a Text column) and the rest of the
    CRUD shape into a dashboard tile. `image` is deliberately NOT projected:
    the alert panel has no thumbnail slot, so shipping the column would be an
    unrendered field on the wire that later readers would mistake for a
    contract the UI honours.
    """
    total, low_stock, out_of_stock, inventory_value = db.session.query(
        func.count(Product.id),
        func.sum(case((Product.stock < LOW_STOCK_THRESHOLD, 1), else_=0)),
        func.sum(case((Product.stock <= 0, 1), else_=0)),
        func.coalesce(func.sum(Product.price * Product.stock), 0.0),
    ).one()

    low_stock_rows = (
        db.session.query(Product.id, Product.name, Product.stock,
                         Product.price)
        .filter(Product.stock < LOW_STOCK_THRESHOLD)
        .order_by(Product.stock.asc(), Product.name.asc())
        .limit(LOW_STOCK_PREVIEW_LIMIT)
        .all()
    )

    return {
        'totalProducts': int(total or 0),
        'lowStockCount': int(low_stock or 0),
        'outOfStockCount': int(out_of_stock or 0),
        'inventoryValue': round(float(inventory_value or 0.0), 2),
        'lowStockThreshold': LOW_STOCK_THRESHOLD,
        'lowStockProducts': [
            {
                'id': row.id,
                'name': row.name,
                'stock': row.stock,
                'price': row.price,
            }
            for row in low_stock_rows
        ],
    }


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
