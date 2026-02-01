from src.config.database import db
from src.config.constants import ORDER_STATUS

class Order(db.Model):
    __tablename__ = 'Orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    totalAmount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum('pending', 'paid', 'shipped', 'cancelled', name='order_status'),
                       default='pending')
    address = db.Column(db.String(255), nullable=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now())
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    #Order - many OrderItems
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_user=False, include_products=False):
        data = {
            'id': self.id,
            'totalAmount': self.totalAmount,
            'status': self.status,
            'address': self.address,
            'UserId': self.UserId,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None
        }
        if include_user and self.User:
            data['User'] = {
                'id': self.User.id,
                'username': self.User.username,
                'email': self.User.email
            }
        if include_products:
            data['Products'] = []
            for item in self.order_items:
                product_data = item.product.to_dict() if item.product else {}
                product_data['OrderItem'] = {
                    'quantity': item.quantity,
                    'priceAtPurchase': item.priceAtPurchase
                }
                data['Products'].append(product_data)
        return data
