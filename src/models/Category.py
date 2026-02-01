import re
from src.config.database import db

class Category(db.Model):
    __tablename__ = 'Categories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    parentId = db.Column(db.Integer, db.ForeignKey('Categories.id'), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(255), nullable=True)
    createdAt = db.Column(db.DateTime, server_default=db.func.now())
    updatedAt = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # relationship
    children = db.relationship('Category', 
                               backref=db.backref('parent', remote_side=[id]),
                               lazy=True)
    
    # Products
    products = db.relationship('Product', backref='category', lazy=True, foreign_keys='Product.categoryId')
    
    def __init__(self, **kwargs):
        if 'name' in kwargs and kwargs['name']:
            name = kwargs['name']
            slug = name.lower().strip()
            slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
            slug = re.sub(r'[\s_-]+', '-', slug)  #  spaces/underscores to hyphens
            slug = re.sub(r'^-+|-+$', '', slug)   # Trim hyphens
            kwargs['slug'] = slug
        super().__init__(**kwargs)
    
    def to_dict(self, include_children=False, include_parent=False):
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'parentId': self.parentId,
            'image': self.image,
            'icon': self.icon,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None
        }
        if include_children:
            data['children'] = [child.to_dict(include_children=True) for child in self.children]
        if include_parent and self.parent:
            data['parent'] = {'name': self.parent.name}
        return data
