import re
from flask import request, jsonify
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from src.models.Category import Category
from src.models.Product import Product
from src.config.database import db
from src.utils.logger import logger
from src.utils.error_handler import handle_errors
from src.utils.validators import required_string
from src.utils.category_tree import (
    build_forest,
    collect_subtree_ids,
    ancestry_chain,
    is_descendant,
)
from src.middleware.multer import save_uploaded_file, delete_uploaded_file

@handle_errors
def createCategory():
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json() or {}

    name = data.get('name')
    parentId = data.get('parentId')
    icon = data.get('icon')

    error = required_string(name, 'name', message='Category name is required')
    if error:
        return jsonify({'message': error['msg']}), 400

    #image path
    image = None
    if 'image' in request.files:
        try:
            image = save_uploaded_file(request.files['image'], 'categories')
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    try:
        parentId = int(parentId) if parentId else None
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid parent category ID'}), 400

    category = Category(
        name=name.strip(),
        parentId=parentId,
        icon=icon.strip() if icon else None,
        image=image
    )

    try:
        db.session.add(category)
        db.session.commit()
    except IntegrityError as e:
        # e.g. a duplicate name -> duplicate auto-generated slug (unique constraint)
        db.session.rollback()
        return jsonify({'message': 'A category with this name already exists'}), 400

    logger.info('Category created', {'categoryId': category.id, 'name': name})

    return jsonify(category.to_dict()), 201

@handle_errors
def getCategoryById(id):
    category = Category.query.filter_by(id=id).first()

    if not category:
        return jsonify({'message': 'Category not found'}), 404

    return jsonify(category.to_dict(include_children=True))

@handle_errors
def updateCategory(id):
    category = Category.query.filter_by(id=id).first()

    if not category:
        return jsonify({'message': 'Category not found'}), 404

    # Get data from form (multipart) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json() or {}

    name = data.get('name')
    parentId = data.get('parentId')
    icon = data.get('icon')
    removeImage = data.get('removeImage')

    if name is not None:
        error = required_string(name, 'name', message='Category name cannot be empty')
        if error:
            return jsonify({'message': error['msg']}), 400

        category.name = name.strip()

        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = re.sub(r'^-+|-+$', '', slug)
        category.slug = slug

    # Validate parentId
    if parentId is not None:
        if parentId == '' or parentId == 'null':
            category.parentId = None
        else:
            new_parent_id = int(parentId)

            # validatre parent not himself
            if new_parent_id == category.id:
                return jsonify({'message': 'Category cannot be its own parent'}), 400

            # Walk up from the proposed parent instead of descending this
            # category's entire subtree.
            links = db.session.query(Category.id, Category.parentId).all()
            if is_descendant(links, category.id, new_parent_id):
                return jsonify({'message': 'Cannot set a subcategory as parent'}), 400

            # Verify parent exists
            parent = Category.query.filter_by(id=new_parent_id).first()
            if not parent:
                return jsonify({'message': 'Parent category not found'}), 400

            category.parentId = new_parent_id

    if icon is not None:
        category.icon = icon.strip() if icon else None

    if removeImage == 'true' or removeImage == True:
        if category.image:
            try:
                delete_uploaded_file(category.image)
            except Exception as e:
                logger.warning('Failed to delete old image', {'error': str(e)})
        category.image = None
    elif 'image' in request.files:
        # Delete old image
        if category.image:
            try:
                delete_uploaded_file(category.image)
            except Exception as e:
                logger.warning('Failed to delete old image', {'error': str(e)})

        # Save new image
        try:
            category.image = save_uploaded_file(request.files['image'], 'categories')
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    db.session.commit()

    logger.info('Category updated', {'categoryId': category.id, 'name': category.name})

    return jsonify({
        'message': 'Category updated successfully',
        'category': category.to_dict()
    })

@handle_errors
def deleteCategory(id):
    category = Category.query.filter_by(id=id).first()

    if not category:
        return jsonify({'message': 'Category not found'}), 404

    children = Category.query.filter_by(parentId=id).first()
    if children:
        return jsonify({
            'message': 'Cannot delete category with subcategories. Please delete or reassign subcategories first.'
        }), 400

    products_count = Product.query.filter_by(categoryId=id).count()

    if products_count > 0:
        Product.query.filter_by(categoryId=id).update({'categoryId': None})
        logger.info('Products uncategorized', {'count': products_count, 'categoryId': id})

    # delete image
    if category.image:
        try:
            delete_uploaded_file(category.image)
        except Exception as e:
            logger.warning('Failed to delete category image', {'error': str(e)})

    category_name = category.name
    db.session.delete(category)
    db.session.commit()
    logger.info('Category deleted', {'categoryId': id, 'name': category_name})
    return jsonify({
        'message': 'Category deleted successfully',
        'productsAffected': products_count
    })

@handle_errors
def getCategoryTree():
    # One query for the whole table; the tree is assembled in memory.
    categories = Category.query.all()
    return jsonify(build_forest(categories))

@handle_errors
def getAllCategories():
    categories = Category.query.all()
    result = [cat.to_dict(include_parent=True) for cat in categories]
    return jsonify(result)

@handle_errors
def getProductsByCategory(slug):
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 20)), 100)
    minPrice = request.args.get('minPrice')
    maxPrice = request.args.get('maxPrice')
    search = request.args.get('search')

    offset = (page - 1) * limit

    category = Category.query.filter_by(slug=slug).first()

    if not category:
        return jsonify({'message': 'Category not found'}), 404

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

    return jsonify({
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
    })

@handle_errors
def getCategoryBySlug(slug):
    category = Category.query.filter_by(slug=slug).first()

    if not category:
        return jsonify({'message': 'Category not found'}), 404

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

    return jsonify(result)
