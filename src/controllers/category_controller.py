import re
from flask import request, jsonify
from sqlalchemy import or_
from src.models.Category import Category
from src.models.Product import Product
from src.config.database import db
from src.utils.logger import logger
from src.middleware.multer import save_uploaded_file, delete_uploaded_file

def createCategory():
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}
        
        name = data.get('name')
        parentId = data.get('parentId')
        icon = data.get('icon')
        
        if not name or not name.strip():
            return jsonify({'message': 'Category name is required'}), 400
        
        #image path 
        image = None
        if 'image' in request.files:
            try:
                image = save_uploaded_file(request.files['image'], 'categories')
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        category = Category(
            name=name.strip(),
            parentId=int(parentId) if parentId else None,
            icon=icon.strip() if icon else None,
            image=image
        )
        
        db.session.add(category)
        db.session.commit()
        
        logger.info('Category created', {'categoryId': category.id, 'name': name})
        
        return jsonify(category.to_dict()), 201
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'error': str(error)}), 400

def getCategoryById(id): 
    try:
        category = Category.query.filter_by(id=id).first()
        
        if not category:
            return jsonify({'message': 'Category not found'}), 404
        
        return jsonify(category.to_dict(include_children=True))
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def updateCategory(id):
    try:
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
            if not name.strip():
                return jsonify({'message': 'Category name cannot be empty'}), 400
            
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
                
                def is_descendant(parent_id, target_id):
                    children = Category.query.filter_by(parentId=parent_id).all()
                    for child in children:
                        if child.id == target_id:
                            return True
                        if is_descendant(child.id, target_id):
                            return True
                    return False
                
                if is_descendant(category.id, new_parent_id):
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
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def deleteCategory(id):
    try:
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
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'message': 'Server error', 'error': str(error)}), 500
    
def getCategoryTree():
    try:
        categories = Category.query.filter_by(parentId=None).all()
        def build_tree(category, depth=0):
            # Build tree - 2 levels for max
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
        
        def getAllChildIds(cat_id):
            ids = [cat_id]
            children = Category.query.filter_by(parentId=cat_id).all()
            for child in children:
                ids.extend(getAllChildIds(child.id))
            return ids
        all_category_ids = getAllChildIds(category.id)
        
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
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
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
        result['children'] = [
            {'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon, 'image': c.image}
            for c in children
        ]
        if category.parent:
            result['parent'] = {
                'id': category.parent.id,
                'name': category.parent.name,
                'slug': category.parent.slug
            }
        result['breadcrumbs'] = breadcrumbs
        
        return jsonify(result)
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        return jsonify({'message': 'Server error', 'error': str(error)}), 500