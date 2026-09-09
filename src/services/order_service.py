from src.models.Order import Order
from src.models.OrderItem import OrderItem
from src.models.Product import Product
from src.config.database import db
from src.config.constants import ROLES, ORDER_STATUS
from src.utils.logger import logger
from src.utils.validators import required_list, one_of


def list_orders_for_user(user_id, role):
    """Local (orders-specific). Admin/Manager see all orders; customers get []
    here (their own orders come from list_own_orders instead)."""
    if role == ROLES['ADMIN'] or role == ROLES['MANAGER']:
        orders = Order.query.order_by(Order.createdAt.desc()).all()
        return [o.to_dict(include_user=True, include_products=True) for o in orders]

    return []


def list_own_orders(user_id):
    """Local (orders-specific). Logged-in user's own orders."""
    orders = Order.query.filter_by(UserId=user_id).order_by(Order.createdAt.desc()).all()
    return [o.to_dict(include_products=True) for o in orders]


def get_order_by_id(order_id, user_id, role):
    """Local (orders-specific). Returns (result, error)."""
    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return None, {'status': 404, 'message': 'Order not found'}

    if role != ROLES['ADMIN'] and role != ROLES['MANAGER'] and order.UserId != user_id:
        return None, {'status': 403, 'message': 'Access denied'}

    return order.to_dict(include_user=True, include_products=True), None


def create_order(user_id, items, address):
    """Checkout. Local (orders-specific). Returns (result, error).

    Validate-then-mutate: every item is checked (existence + stock) before
    any DB write happens, so a bad item later in the list never leaves an
    earlier item's stock partially decremented. Do not merge the two phases.
    """
    error = required_list(items, 'items', message='Order must contain at least one item')
    if error:
        return None, {'status': 400, 'message': error['msg']}

    totalAmount = 0
    orderItems = []
    productsToUpdate = []

    # Phase 1: validate every item and compute total — no DB writes yet
    for item in items:
        product = Product.query.filter_by(id=item.get('productId')).first()

        if not product:
            return None, {
                'status': 404,
                'message': f"Product with ID {item.get('productId')} not found"
            }

        if product.stock < item.get('quantity', 0):
            return None, {
                'status': 400,
                'message': f"Insufficient stock for {product.name}. Available: {product.stock}"
            }

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

    # Phase 2: all items validated — now write
    order = Order(
        UserId=user_id,
        totalAmount=totalAmount,
        address=address,
        status=ORDER_STATUS['PENDING']
    )

    db.session.add(order)
    db.session.flush()

    for item in orderItems:
        orderItem = OrderItem(
            OrderId=order.id,
            ProductId=item['ProductId'],
            quantity=item['quantity'],
            priceAtPurchase=item['priceAtPurchase']
        )
        db.session.add(orderItem)

    for item in productsToUpdate:
        item['product'].stock = item['newStock']

    db.session.commit()

    logger.info('Order created', {'orderId': order.id, 'userId': user_id, 'total': totalAmount})

    completeOrder = Order.query.filter_by(id=order.id).first()

    return {
        'message': 'Order created successfully',
        'order': completeOrder.to_dict(include_products=True)
    }, None


def update_order_status(order_id, status):
    """Local (orders-specific). Returns (result, error)."""
    error = one_of(status, 'status', ORDER_STATUS.values(), message='Invalid order status')
    if error:
        return None, {'status': 400, 'message': error['msg']}

    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return None, {'status': 404, 'message': 'Order not found'}

    order.status = status
    db.session.commit()

    updatedOrder = Order.query.filter_by(id=order.id).first()

    return {
        'message': 'Order status updated successfully',
        'order': updatedOrder.to_dict(include_user=True, include_products=True)
    }, None


def delete_order(order_id):
    """Local (orders-specific). Returns (result, error)."""
    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return None, {'status': 404, 'message': 'Order not found'}

    OrderItem.query.filter_by(OrderId=order.id).delete()
    db.session.delete(order)
    db.session.commit()

    return {'message': 'Order deleted successfully'}, None
