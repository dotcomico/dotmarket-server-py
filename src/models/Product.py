from src.config.database import db

class Product(db.Model):
    __tablename__ = 'Products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)
    image360 = db.Column(db.String(255), nullable=True)
    categoryId = db.Column(db.Integer, db.ForeignKey('Categories.id'), nullable=True)
    createdAt = db.Column(db.DateTime, server_default=db.func.now())
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    def to_dict(self, include_category=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'image': self.image,
            'image360': self.image360,
            'categoryId': self.categoryId,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None
        }
        if include_category and self.category:
            data['category'] = {
                'id': self.category.id,
                'name': self.category.name,
                'slug': self.category.slug,
                'icon': self.category.icon
            }
        return data
