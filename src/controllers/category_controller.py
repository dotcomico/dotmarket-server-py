from flask import request, jsonify
from sqlalchemy import or_
from src.models.Category import Category
from src.models.Product import Product
from src.config.database import db
from src.utils.logger import logger
from src.middleware.multer import save_uploaded_file

def createCategory():
    try:
        # Get data from form (multipart) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}
        
        name = data.get('name')
        parentId = data.get('parentId')
        icon = data.get('icon')
        
        # Get image path from multer if uploaded
        image = None
        if 'image' in request.files:
            try:
                image = save_uploaded_file(request.files['image'], 'categories')
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        category = Category(
            name=name,
            parentId=int(parentId) if parentId else None,
            icon=icon,
            image=image
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify(category.to_dict()), 201
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'error': str(error)}), 400

def getCategoryTree():
    try:
        categories = Category.query.filter_by(parentId=None).all()
        def build_tree(category, depth=0):
            # build tree - 2 levels
            data = category.to_dict()
            if depth < 2: 
                children = Category.query.filter_by(parentId=category.id).all()
                data['children'] = [build_tree(child, depth + 1) for child in children]
            else:
                data['children'] = []
            return data
        
        result = [build_tree(cat) for cat in categories]
        return jsonify(result)
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'error': str(error)}), 500

def getAllCategories():
    try:
        categories = Category.query.all()
        result = [cat.to_dict(include_parent=True) for cat in categories]
        return jsonify(result)
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'error': str(error)}), 500

def getProductsByCategory(slug):
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        minPrice = request.args.get('minPrice')
        maxPrice = request.args.get('maxPrice')
        search = request.args.get('search')
        
        offset = (page - 1) * limit

        category = Category.query.filter_by(slug=slug).first()
        
        if not category:
            return jsonify({'message': 'Category not found'}), 404
        
        # get all child IDs
        def getAllChildIds(categoryId):
            children = Category.query.filter_by(parentId=categoryId).all()
            ids = [categoryId]
            for child in children:
                childIds = getAllChildIds(child.id)
                ids.extend(childIds)
            return ids
        
        categoryIds = getAllChildIds(category.id)
        
        query = Product.query.filter(Product.categoryId.in_(categoryIds))
        
        if minPrice:
            query = query.filter(Product.price >= float(minPrice))
        if maxPrice:
            query = query.filter(Product.price <= float(maxPrice))
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        count = query.count()
        
        # Fetch products
        products = query.order_by(Product.createdAt.desc()).offset(offset).limit(limit).all()
        
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
                'total': count,
                'page': page,
                'limit': limit,
                'totalPages': (count + limit - 1) // limit if count > 0 else 0
            }
        })
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Get products by category error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def getCategoryBySlug(slug):
    try:
        category = Category.query.filter_by(slug=slug).first()
        
        if not category:
            return jsonify({'message': 'Category not found'}), 404
        
        children = Category.query.filter_by(parentId=category.id).all()
        
        # Build breadcrumb
        breadcrumbs = []
        current = category
        
        while current:
            breadcrumbs.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug
            })
            
            if current.parentId:
                current = Category.query.filter_by(id=current.parentId).first()
            else:
                current = None
        
        result = category.to_dict()
        result['children'] = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon, 'image': c.image} for c in children]
        if category.parent:
            result['parent'] = {'id': category.parent.id, 'name': category.parent.name, 'slug': category.parent.slug}
        result['breadcrumbs'] = breadcrumbs
        
        return jsonify(result)
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Get category by slug error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500
