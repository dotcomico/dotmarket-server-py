import bcrypt
from flask_jwt_extended import create_access_token

from src.config.constants import ROLES
from src.config.database import db
from src.models.User import User
from src.utils.jwt_identity import resolve_user_id
from src.utils.logger import logger
from src.utils.validators import required, required_string, valid_email, strong_password, one_of


def validateRegister(data):
    errors = []
    errors.append(required_string(data.get('username'), 'username', min_len=3, max_len=30))
    errors.append(valid_email(data.get('email'), 'email'))
    errors.append(strong_password(data.get('password'), 'password'))

    # Role (optional)
    role = data.get('role')
    if role:
        errors.append(one_of(role, 'role', ROLES.values()))

    return [e for e in errors if e]


def validateLogin(data):
    errors = [
        valid_email(data.get('email'), 'email'),
        required(data.get('password'), 'password'),
    ]
    return [e for e in errors if e]


def register_user(data):
    """Create a new user account and issue a JWT.

    Local (auth-specific). Returns (result, error): `error` carries
    {'status', 'message'} and, for validation failures, an `errors` list —
    the route maps this straight onto the old response shape.
    """
    errors = validateRegister(data)
    if errors:
        return None, {'status': 400, 'message': 'Validation failed', 'errors': errors}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    role = data.get('role')

    if User.query.filter_by(email=email).first():
        return None, {'status': 400, 'message': 'User already exists with this email'}

    if User.query.filter_by(username=username).first():
        return None, {'status': 400, 'message': 'Username already taken'}

    salt = bcrypt.gensalt(rounds=10)
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    newUser = User(
        username=username,
        email=email,
        password=hashedPassword,
        role=role if role else ROLES['CUSTOMER']
    )
    db.session.add(newUser)
    db.session.commit()

    logger.info('User registered', {'userId': newUser.id, 'email': email})

    token = create_access_token(identity={'id': newUser.id, 'role': newUser.role})

    return {
        'message': 'User registered successfully',
        'token': token,
        'user': {
            'id': newUser.id,
            'username': newUser.username,
            'email': newUser.email,
            'role': newUser.role
        }
    }, None


def login_user(data):
    """Authenticate a user and issue a JWT. Local (auth-specific)."""
    errors = validateLogin(data)
    if errors:
        return None, {'status': 400, 'message': 'Validation failed', 'errors': errors}

    email = data.get('email', '').strip().lower()
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        logger.warn('Login failed', {'email': email, 'reason': 'wrong password'})
        return None, {'status': 401, 'message': 'Invalid email or password'}

    logger.info('User logged in', {'userId': user.id})
    token = create_access_token(identity={'id': user.id, 'role': user.role})

    return {
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }, None


def get_me(jwt_identity):
    """Look up the currently-authenticated user. Local (auth-specific)."""
    user_id = resolve_user_id(jwt_identity)
    user = User.query.get(user_id)
    if not user:
        return None, {'status': 404, 'message': 'User not found'}
    return user.to_dict(exclude_password=True), None
