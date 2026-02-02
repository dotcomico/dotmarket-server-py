import os
import json
from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.config.database import db, connectDB
from src.models.User import User
from src.models.Product import Product
from src.models.Order import Order
from src.models.OrderItem import OrderItem
from src.models.Category import Category
from flask_cors import CORS
from src.routes.auth import auth_bp
from src.routes.users import users_bp
from src.routes.products import products_bp
from src.routes.orders import orders_bp
from src.routes.categories import categories_bp
from datetime import timedelta

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='../public')
    app.url_map.strict_slashes = False
    PORT = int(os.getenv('PORT', 3000))
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    connectDB(app)
   
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    jwt = JWTManager(app)

    # Allow complex objects (dict) as JWT identity
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Convert user dict to JSON string for JWT subject"""
        if isinstance(user, dict):
            return json.dumps(user)
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load user data from JWT - returns the identity"""
        identity = jwt_data["sub"]
        try:
            return json.loads(identity)
        except (json.JSONDecodeError, TypeError):
            return identity
    
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["1000 per 15 minutes"] if os.getenv('NODE_ENV') == 'development' else ["100 per 15 minutes"]
    )

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        return send_from_directory(os.path.join(app.root_path, '..', 'public', 'uploads'), filename)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    
    @app.route('/')
    def health_check():
        return jsonify({'message': 'Supermarket API is running!'})
    
    @app.errorhandler(Exception)
    def handle_error(error):
        print(f'Error: {error}')
        status_code = getattr(error, 'code', 500)
        response = {
            'message': str(error) if str(error) else 'Internal Server Error'
        }
        if os.getenv('NODE_ENV') == 'development':
            response['error'] = str(error)
        return jsonify(response), status_code
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Route not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'message': 'Internal Server Error'}), 500
    
    return app

def startServer():
    app = create_app()
    PORT = int(os.getenv('PORT', 3000))
    
    try:
        with app.app_context():
            db.create_all()
            print('✅ Database synchronized')
        
        print(f'🚀 Server running on http://localhost:{PORT}')
        app.run(host='0.0.0.0', port=PORT, debug=os.getenv('NODE_ENV') == 'development')
        
    except Exception as error:
        print(f'❌ Failed to start server: {error}')
        exit(1)

if __name__ == '__main__':
    startServer()