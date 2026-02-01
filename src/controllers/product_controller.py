# Exact translation of src/controllers/productController.js
from flask import request, jsonify
from sqlalchemy import or_
from src.models.Product import Product
from src.models.Category import Category
from src.config.database import db
from src.utils.logger import logger
from src.middleware.multer import save_uploaded_file

def validateProduct(data, files=None):
    errors = []
    # Name 
    name = data.get('name', '').strip() if data.get('name') else ''
    if not name:
        errors.append({'type': 'field', 'msg': 'Name is required', 'path': 'name'})
    elif len(name) < 3 or len(name) > 100:
        errors.append({'type': 'field', 'msg': 'Name must be 3-100 characters', 'path': 'name'})
    
    # Price
    try:
        price = float(data.get('price', 0))
        if price <= 0:
            errors.append({'type': 'field', 'msg': 'Price must be greater than 0', 'path': 'price'})
    except (ValueError, TypeError):
        errors.append({'type': 'field', 'msg': 'Price must be greater than 0', 'path': 'price'})
    
    # Category ID 
    try:
        categoryId = int(data.get('categoryId', 0))
        if categoryId <= 0:
            errors.append({'type': 'field', 'msg': 'Valid category ID required', 'path': 'categoryId'})
    except (ValueError, TypeError):
        errors.append({'type': 'field', 'msg': 'Valid category ID required', 'path': 'categoryId'})
    
    # Description validation 
    description = data.get('description', '')
    if description and len(description) > 1000:
        errors.append({'type': 'field', 'msg': 'Description too long (max 1000 chars)', 'path': 'description'})
    
    # Stock validation
    if data.get('stock') is not None:
        try:
            stock = int(data.get('stock', 0))
            if stock < 0:
                errors.append({'type': 'field', 'msg': 'Stock must be 0 or positive', 'path': 'stock'})
        except (ValueError, TypeError):
            errors.append({'type': 'field', 'msg': 'Stock must be 0 or positive', 'path': 'stock'})
    
    return errors

def handleValidationErrors(errors):
    #Helper - check validation results
    if errors:
        return jsonify({
            'message': 'Validation failed',
            'errors': errors
        }), 400
    return None

def getAllProducts():
    # for search, filters, pagination
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search')
        categoryId = request.args.get('categoryId')
        minPrice = request.args.get('minPrice')
        maxPrice = request.args.get('maxPrice')
        
        offset = (page - 1) * limit
        
        query = Product.query
        
        # Search by name
        if search:
            query = query.filter(Product.name.ilike(f'%{search}%'))
        
        # Filter by category
        if categoryId:
            query = query.filter(Product.categoryId == int(categoryId))
        
        # Price range filter
        if minPrice:
            query = query.filter(Product.price >= float(minPrice))
        if maxPrice:
            query = query.filter(Product.price <= float(maxPrice))
        
        # total count
        count = query.count()
        
        # paginated results with category
        products = query.order_by(Product.createdAt.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
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
        print(f'Get all products error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def getProductById(id):
    try:
        product = Product.query.filter_by(id=id).first()
        
        if not product:
            return jsonify({'message': 'Product not found'}), 404
        
        return jsonify(product.to_dict(include_category=True))
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Get product error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def createProduct():
    try:
        # Get data from form (multipart) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}
        
        errors = validateProduct(data)
        validation_error = handleValidationErrors(errors)
        if validation_error:
            return validation_error
        
        name = data.get('name', '').strip()
        categoryId = int(data.get('categoryId'))
        description = data.get('description', '').strip() if data.get('description') else None
        price = float(data.get('price'))
        stock = int(data.get('stock', 0))
        
        # Verify category 
        category = Category.query.filter_by(id=categoryId).first()
        if not category:
            return jsonify({'message': 'Invalid category ID'}), 400
        
        #  image uploads
        image = None
        image360 = None
        
        if 'image' in request.files:
            try:
                image = save_uploaded_file(request.files['image'])
            except ValueError as e:
                return jsonify({'message': str(e)}), 400
        
        if 'image360' in request.files:
            try:
                image360 = save_uploaded_file(request.files['image360'])
            except ValueError as e:
                return jsonify({'message': str(e)}), 400
        
        # Create product
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
        
        return jsonify({
            'message': 'Product created successfully',
            'product': newProduct.to_dict(include_category=True)
        }), 201
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Create product error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def updateProduct(id):
    try:
        product = Product.query.filter_by(id=id).first()
        
        if not product:
            return jsonify({'message': 'Product not found'}), 404
        
        # Get data from form (multipart) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            data = request.get_json() or {}
        
        name = data.get('name')
        categoryId = data.get('categoryId')
        description = data.get('description')
        price = data.get('price')
        stock = data.get('stock')
        removeImage = data.get('removeImage')
        removeImage360 = data.get('removeImage360')
        
        # Verify category if being updated
        if categoryId:
            category = Category.query.filter_by(id=int(categoryId)).first()
            if not category:
                return jsonify({'message': 'Invalid category ID'}), 400
        
        # Update fields
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
        
        # Handle main image
        if 'image' in request.files:
            try:
                product.image = save_uploaded_file(request.files['image'])
            except ValueError as e:
                return jsonify({'message': str(e)}), 400
        elif removeImage == 'true':
            product.image = None
        
        # Handle 360 image
        if 'image360' in request.files:
            try:
                product.image360 = save_uploaded_file(request.files['image360'])
            except ValueError as e:
                return jsonify({'message': str(e)}), 400
        elif removeImage360 == 'true':
            product.image360 = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict(include_category=True)
        })
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Update product error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500

def deleteProduct(id):
    """Delete product"""
    try:
        product = Product.query.filter_by(id=id).first()
        
        if not product:
            return jsonify({'message': 'Product not found'}), 404
        
        productId = product.id
        db.session.delete(product)
        db.session.commit()
        
        logger.info('Product deleted', {'productId': productId})
        
        return jsonify({
            'message': 'Product deleted successfully',
            'deletedId': str(id)
        })
        
    except Exception as error:
        logger.error('Operation failed', {'error': str(error)})
        print(f'Delete product error: {error}')
        return jsonify({'message': 'Server error', 'error': str(error)}), 500
