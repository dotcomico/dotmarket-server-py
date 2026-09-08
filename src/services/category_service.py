import re

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from src.models.Category import Category
from src.models.Product import Product
from src.config.database import db
from src.utils.logger import logger
from src.utils.validators import required_string
from src.utils.category_tree import (
    build_forest,
    collect_subtree_ids,
    ancestry_chain,
    is_descendant,
)
from src.middleware.multer import save_uploaded_file, delete_uploaded_file


def create_category(data, image_file=None):
    """Local (categories-specific). Returns (result, error).

    `image_file` is the werkzeug `FileStorage` already pulled out of
    `request.files` by the route (services stay flask.request-free).
    """
    name = data.get('name')
    parentId = data.get('parentId')
    icon = data.get('icon')

    error = required_string(name, 'name', message='Category name is required')
    if error:
        return None, {'status': 400, 'message': error['msg']}

    image = None
    if image_file is not None:
        try:
            image = save_uploaded_file(image_file, 'categories')
        except ValueError as e:
            return None, {'status': 400, 'error': str(e)}

    try:
        parentId = int(parentId) if parentId else None
    except (ValueError, TypeError):
        return None, {'status': 400, 'message': 'Invalid parent category ID'}

    category = Category(
        name=name.strip(),
        parentId=parentId,
        icon=icon.strip() if icon else None,
        image=image
    )

    try:
        db.session.add(category)
        db.session.commit()
    except IntegrityError:
        # e.g. a duplicate name -> duplicate auto-generated slug (unique constraint)
        db.session.rollback()
        return None, {'status': 400, 'message': 'A category with this name already exists'}

    logger.info('Category created', {'categoryId': category.id, 'name': name})

    return category.to_dict(), None


def get_category_by_id(id):
    """Local (categories-specific). Returns (result, error)."""
    category = Category.query.filter_by(id=id).first()
    if not category:
        return None, {'status': 404, 'message': 'Category not found'}
    return category.to_dict(include_children=True), None


def update_category(id, data, image_file=None):
    """Local (categories-specific). Returns (result, error)."""
    category = Category.query.filter_by(id=id).first()
    if not category:
        return None, {'status': 404, 'message': 'Category not found'}

    name = data.get('name')
    parentId = data.get('parentId')
    icon = data.get('icon')
    removeImage = data.get('removeImage')

    if name is not None:
        error = required_string(name, 'name', message='Category name cannot be empty')
        if error:
            return None, {'status': 400, 'message': error['msg']}

        category.name = name.strip()

        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = re.sub(r'^-+|-+$', '', slug)
        category.slug = slug

    if parentId is not None:
        if parentId == '' or parentId == 'null':
            category.parentId = None
        else:
            new_parent_id = int(parentId)

            if new_parent_id == category.id:
                return None, {'status': 400, 'message': 'Category cannot be its own parent'}

            # Walk up from the proposed parent instead of descending this
            # category's entire subtree.
            links = db.session.query(Category.id, Category.parentId).all()
            if is_descendant(links, category.id, new_parent_id):
                return None, {'status': 400, 'message': 'Cannot set a subcategory as parent'}

            parent = Category.query.filter_by(id=new_parent_id).first()
            if not parent:
                return None, {'status': 400, 'message': 'Parent category not found'}

            category.parentId = new_parent_id

    if icon is not None:
        category.icon = icon.strip() if icon else None

    if removeImage == 'true' or removeImage is True:
        if category.image:
            try:
                delete_uploaded_file(category.image)
            except Exception as e:
                logger.warning('Failed to delete old image', {'error': str(e)})
        category.image = None
    elif image_file is not None:
        if category.image:
            try:
                delete_uploaded_file(category.image)
            except Exception as e:
                logger.warning('Failed to delete old image', {'error': str(e)})

        try:
            category.image = save_uploaded_file(image_file, 'categories')
        except ValueError as e:
            return None, {'status': 400, 'error': str(e)}

    db.session.commit()

    logger.info('Category updated', {'categoryId': category.id, 'name': category.name})

    return {
        'message': 'Category updated successfully',
        'category': category.to_dict()
    }, None


def delete_category(id):
    """Local (categories-specific). Returns (result, error)."""
    category = Category.query.filter_by(id=id).first()
    if not category:
        return None, {'status': 404, 'message': 'Category not found'}

    children = Category.query.filter_by(parentId=id).first()
    if children:
        return None, {
            'status': 400,
            'message': 'Cannot delete category with subcategories. Please delete or reassign subcategories first.'
        }

    products_count = Product.query.filter_by(categoryId=id).count()

    if products_count > 0:
        Product.query.filter_by(categoryId=id).update({'categoryId': None})
        logger.info('Products uncategorized', {'count': products_count, 'categoryId': id})

    if category.image:
        try:
            delete_uploaded_file(category.image)
        except Exception as e:
            logger.warning('Failed to delete category image', {'error': str(e)})

    category_name = category.name
    db.session.delete(category)
    db.session.commit()
    logger.info('Category deleted', {'categoryId': id, 'name': category_name})

    return {
        'message': 'Category deleted successfully',
        'productsAffected': products_count
    }, None


def get_category_tree():
    """Local (categories-specific). One query for the whole table; the tree
    is assembled in memory (see utils/category_tree.py, Step 7)."""
    categories = Category.query.all()
    return build_forest(categories)


def get_all_categories():
    """Local (categories-specific)."""
    categories = Category.query.all()
    return [cat.to_dict(include_parent=True) for cat in categories]


def get_products_by_category(slug, page=1, limit=20, minPrice=None, maxPrice=None, search=None):
    """Local (categories-specific). Returns (result, error)."""
    offset = (page - 1) * limit

    category = Category.query.filter_by(slug=slug).first()
    if not category:
        return None, {'status': 404, 'message': 'Category not found'}

    # id/parentId only — the subtree walk never needs the other columns.
    links = db.session.query(Category.id, Category.parentId).all()
    all_category_ids = collect_subtree_ids(links, category.id)

    query = Product.query.filter(Product.categoryId.in_(all_category_ids))

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    if minPrice:
        query = query.filter(Product.price >= float(minPrice))
    if maxPrice:
        query = query.filter(Product.price <= float(maxPrice))

    total = query.count()
    products = query.offset(offset).limit(limit).all()

    return {
        'category': {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'icon': category.icon,
            'image': category.image
        },
        'products': [p.to_dict(include_category=True) for p in products],
        'pagination': {
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': (total + limit - 1) // limit
        }
    }, None


def get_category_by_slug(slug):
    """Local (categories-specific). Returns (result, error)."""
    category = Category.query.filter_by(slug=slug).first()
    if not category:
        return None, {'status': 404, 'message': 'Category not found'}

    children = Category.query.filter_by(parentId=category.id).all()

    # Build breadcrumb — one query up the whole ancestry instead of one per
    # level. A root has no ancestry, so skip the query entirely.
    if category.parentId is None:
        ancestry = [category]
    else:
        links = db.session.query(
            Category.id, Category.parentId, Category.name, Category.slug
        ).all()
        ancestry = ancestry_chain(links, category.id)
    breadcrumbs = [
        {'id': c.id, 'name': c.name, 'slug': c.slug}
        for c in ancestry
    ]

    result = category.to_dict()
    result['children'] = [
        {'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon, 'image': c.image}
        for c in children
    ]
    # ancestry ends with `category` itself, so its parent is the entry before it.
    if len(ancestry) > 1:
        parent = ancestry[-2]
        result['parent'] = {
            'id': parent.id,
            'name': parent.name,
            'slug': parent.slug
        }
    result['breadcrumbs'] = breadcrumbs

    return result, None
