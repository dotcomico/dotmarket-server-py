import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def connectDB(app):
    db_storage = os.getenv('DB_STORAGE', './database.sqlite')
    # Resolve to an absolute path: Flask-SQLAlchemy resolves relative
    # sqlite:/// paths against app.instance_path, not the process cwd,
    # which silently breaks DB_STORAGE values set relative to the repo root.
    db_path = os.path.abspath(db_storage)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            db.engine.connect()
            print('✅ SQLite Database connected successfully.')
        except Exception as error:
            print(f'❌ Unable to connect to the database: {error}')
            exit(1)
    
    return db
