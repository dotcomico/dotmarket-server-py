import bcrypt
from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from src.models.User import User
from src.config.database import db
from src.config.constants import ROLES
from src.utils.logger import logger
from src.utils.jwt_identity import resolve_user_id
from src.utils.error_handler import handle_errors
from src.utils.validators import required_string, valid_email, strong_password, one_of

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
        required_string(data.get('password'), 'password'),
    ]
    return [e for e in errors if e]

@handle_errors
def register():
    data = request.get_json()
    # errors
    errors = validateRegister(data)
    if errors:
        return jsonify({
            'message': 'Validation failed',
            'errors': errors
        }), 400
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    role = data.get('role')

    # Check if exists
    existingUser = User.query.filter_by(email=email).first()
    if existingUser:
        return jsonify({'message': 'User already exists with this email'}), 400

    # Check if uniq
    existingUsername = User.query.filter_by(username=username).first()
    if existingUsername:
        return jsonify({'message': 'Username already taken'}), 400

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

    return jsonify({
        'message': 'User registered successfully',
        'token': token,
        'user': {
            'id': newUser.id,
            'username': newUser.username,
            'email': newUser.email,
            'role': newUser.role
        }
    }), 201

@handle_errors
def login():
    data = request.get_json()

    #  errors
    errors = validateLogin(data)
    if errors:
        return jsonify({
            'message': 'Validation failed',
            'errors': errors
        }), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user:
        logger.warn('Login failed', {'email': email, 'reason': 'wrong password'})
        return jsonify({'message': 'Invalid email or password'}), 401

    isMatch = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
    if not isMatch:
        logger.warn('Login failed', {'email': email, 'reason': 'wrong password'})
        return jsonify({'message': 'Invalid email or password'}), 401

    logger.info('User logged in', {'userId': user.id})
    token = create_access_token(identity={'id': user.id, 'role': user.role})

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@handle_errors
def getMe():
    user_id = resolve_user_id(get_jwt_identity())

    # search with integer/ID
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user.to_dict(exclude_password=True))
