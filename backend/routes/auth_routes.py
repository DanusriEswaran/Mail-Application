from flask import Blueprint, request, jsonify
from models.user import register_user, authenticate_user, update_user_last_login
from utils.auth import generate_token, verify_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Register user
        user, error = register_user(username, email, password)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return token"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        user, error = authenticate_user(email, password)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Update last login
        update_user_last_login(email)
        
        # Generate token
        token = generate_token(user)
        
        if not token:
            return jsonify({'error': 'Failed to generate token'}), 500
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'email': user.get('email')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['POST'])
def verify_token_route():
    """Verify if token is valid"""
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            token = request.headers.get('MAIL-KEY')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'valid': True,
            'user': user_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Token verification failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In a stateless JWT system, logout is typically handled client-side
        # by removing the token from storage
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500