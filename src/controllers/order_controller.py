from flask import request, jsonify, g
from src.models.Order import Order
from src.models.OrderItem import OrderItem
from src.models.Product import Product
from src.models.User import User
from src.config.database import db
from src.config.constants import ROLES, ORDER_STATUS
from src.utils.logger import logger
from src.utils.error_handler import handle_errors

@handle_errors
def getAllOrders():
    # Admin sees all, Customers see only their own
    if g.user['role'] == ROLES['ADMIN'] or g.user['role'] == ROLES['MANAGER']:
        orders = Order.query.order_by(Order.createdAt.desc()).all()
        return jsonify([o.to_dict(include_user=True, include_products=True) for o in orders])

    # For customers
    return jsonify([])

# loged in users - only there own
@handle_errors
def getAllUserOrders():
    orders = Order.query.filter_by(UserId=g.user['id']).order_by(Order.createdAt.desc()).all()
    return jsonify([o.to_dict(include_products=True) for o in orders])

@handle_errors
def getOrderById(id):
    order = Order.query.filter_by(id=id).first()

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    # Check permissions
    if (g.user['role'] != ROLES['ADMIN'] and
        g.user['role'] != ROLES['MANAGER'] and
        order.UserId != g.user['id']):
        return jsonify({'message': 'Access denied'}), 403

    return jsonify(order.to_dict(include_user=True, include_products=True))

@handle_errors
def createOrder():
     # use for Checkout
    data = request.get_json()
    items = data.get('items', [])
    address = data.get('address')

    if not items or len(items) == 0:
        return jsonify({'message': 'Order must contain at least one item'}), 400

    totalAmount = 0
    orderItems = []
    productsToUpdate = []

    # Validate products and calculate total price
    for item in items:
        product = Product.query.filter_by(id=item.get('productId')).first()

        if not product:
            return jsonify({
                'message': f"Product with ID {item.get('productId')} not found"
            }), 404

        if product.stock < item.get('quantity', 0):
            return jsonify({
                'message': f"Insufficient stock for {product.name}. Available: {product.stock}"
            }), 400

        totalAmount += product.price * item.get('quantity')

        orderItems.append({
            'ProductId': item.get('productId'),
            'quantity': item.get('quantity'),
            'priceAtPurchase': product.price
        })

        productsToUpdate.append({
            'product': product,
            'newStock': product.stock - item.get('quantity')
        })

    order = Order(
        UserId=g.user['id'],
        totalAmount=totalAmount,
        address=address,
        status=ORDER_STATUS['PENDING']
    )

    db.session.add(order)
    db.session.flush()

    # order items with OrderId
    for item in orderItems:
        orderItem = OrderItem(
            OrderId=order.id,
            ProductId=item['ProductId'],
            quantity=item['quantity'],
            priceAtPurchase=item['priceAtPurchase']
        )
        db.session.add(orderItem)

    # Update product stock
    for item in productsToUpdate:
        item['product'].stock = item['newStock']

    db.session.commit()

    logger.info('Order created', {'orderId': order.id, 'userId': g.user['id'], 'total': totalAmount})

    # Fetch complete order with products
    completeOrder = Order.query.filter_by(id=order.id).first()

    return jsonify({
        'message': 'Order created successfully',
        'order': completeOrder.to_dict(include_products=True)
    }), 201

@handle_errors
def updateOrderStatus(id):
   # Protected - Admin/Manager
    data = request.get_json()
    status = data.get('status')

    if status not in ORDER_STATUS.values():
        return jsonify({'message': 'Invalid order status'}), 400

    order = Order.query.filter_by(id=id).first()

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    order.status = status
    db.session.commit()

    updatedOrder = Order.query.filter_by(id=order.id).first()

    return jsonify({
        'message': 'Order status updated successfully',
        'order': updatedOrder.to_dict(include_user=True, include_products=True)
    })

@handle_errors
def deleteOrder(id):
    # Protected - Admin only
    order = Order.query.filter_by(id=id).first()

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    # Delete order items first
    OrderItem.query.filter_by(OrderId=order.id).delete()
    db.session.delete(order)
    db.session.commit()

    return jsonify({'message': 'Order deleted successfully'})
