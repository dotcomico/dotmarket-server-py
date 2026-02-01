from src.config.database import db

class OrderItem(db.Model):
    __tablename__ = 'OrderItems'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrderId = db.Column(db.Integer, db.ForeignKey('Orders.id'), nullable=False)
    ProductId = db.Column(db.Integer, db.ForeignKey('Products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    priceAtPurchase = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, server_default=db.func.now())
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    product = db.relationship('Product', backref='order_items', lazy=True)
    
    #product can't appear twice in same order
    __table_args__ = (
        db.UniqueConstraint('OrderId', 'ProductId', name='unique_order_product'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'OrderId': self.OrderId,
            'ProductId': self.ProductId,
            'quantity': self.quantity,
            'priceAtPurchase': self.priceAtPurchase,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None
        }
