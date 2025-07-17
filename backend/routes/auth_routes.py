# Update your auth_routes.py to include proper token generation

from flask import Blueprint, request, jsonify
from models.user import register_user, authenticate_user, update_user_last_login
from utils.auth import generate_token, verify_token
import json

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

# Additional endpoint to logout (optional)
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In a stateless JWT system, logout is typically handled client-side
        # by removing the token from storage
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

# Update your company_routes.py to have better error handling

from flask import Blueprint, request, jsonify
from models.company import (
    register_company, 
    is_domain_available, 
    get_company_by_domain,
    get_all_companies,
    get_company_stats,
    update_company_status,
    delete_company
)
from models.user import get_users_by_domain
from utils.auth import verify_token, admin_required, is_domain_admin

company_bp = Blueprint('company', __name__)

@company_bp.route('/check_domain', methods=['POST'])
def check_domain_availability():
    """Check if a domain is available for registration"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        
        # Clean and validate domain
        domain = domain.strip().lower()
        
        # Basic domain validation
        if '.' not in domain or len(domain.split('.')) < 2:
            return jsonify({'error': 'Invalid domain format'}), 400
        
        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$', domain):
            return jsonify({'error': 'Invalid domain format'}), 400
        
        available = is_domain_available(domain)
        
        return jsonify({
            'available': available,
            'domain': domain
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error checking domain: {str(e)}'}), 500

@company_bp.route('/register_company', methods=['POST'])
def register_new_company():
    """Register a new company"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        domain = data.get('domain', '').strip().lower()
        admin_name = data.get('admin_name', '').strip()
        
        # Validation
        if not all([company_name, domain, admin_name]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Additional validation
        if len(company_name) < 2:
            return jsonify({'error': 'Company name must be at least 2 characters'}), 400
        
        if len(admin_name) < 2:
            return jsonify({'error': 'Admin name must be at least 2 characters'}), 400
        
        # Register the company
        company, error = register_company(company_name, domain, admin_name)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Company registered successfully',
            'company': company
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@company_bp.route('/companies', methods=['GET'])
def get_companies():
    """Get all registered companies"""
    try:
        companies = get_all_companies()
        
        return jsonify({
            'companies': companies,
            'count': len(companies)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching companies: {str(e)}'}), 500

@company_bp.route('/companies/<domain>', methods=['GET'])
def get_company_details(domain):
    """Get details for a specific company"""
    try:
        company = get_company_by_domain(domain)
        
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        return jsonify({'company': company}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching company: {str(e)}'}), 500

@company_bp.route('/domain_users/<domain>', methods=['GET'])
def get_domain_users(domain):
    """Get all users for a specific domain (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Admin authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if user is admin for this domain
        user_email = user_data.get('email')
        if not user_email or not is_domain_admin(user_email, domain):
            return jsonify({'error': 'Access denied. Admin privileges required for this domain.'}), 403
        
        # Get users for this domain
        users = get_users_by_domain(domain)
        
        return jsonify({
            'users': users,
            'domain': domain,
            'count': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching domain users: {str(e)}'}), 500

@company_bp.route('/domain_stats/<domain>', methods=['GET'])
def get_domain_statistics(domain):
    """Get statistics for a domain (admin only)"""
    try:
        # Verify admin token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Admin authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = verify_token(token)
        
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if user is admin for this domain
        user_email = user_data.get('email')
        if not user_email or not is_domain_admin(user_email, domain):
            return jsonify({'error': 'Access denied. Admin privileges required for this domain.'}), 403
        
        # Get domain statistics
        stats, error = get_company_stats(domain)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'stats': stats,
            'domain': domain
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching domain stats: {str(e)}'}), 500

# Add this function to your models/user.py to get users by domain
def get_users_by_domain(domain):
    """Get all users for a specific domain"""
    try:
        users = load_users()
        domain_users = []
        
        for user_email, user_data in users.items():
            if user_email.endswith(f'@{domain}'):
                domain_users.append({
                    'user_id': user_data.get('user_id', generate_user_id(user_email, 'dummy')),
                    'username': user_data.get('username'),
                    'email': user_email,
                    'status': user_data.get('status', 'active'),
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login')
                })
        
        return domain_users
        
    except Exception as e:
        print(f"Error getting users by domain: {str(e)}")
        return []

# Update your models/company.py to improve stats calculation
def get_company_stats(domain):
    """Get statistics for a company domain"""
    try:
        from models.user import get_users_by_domain
        
        # Get users for this domain
        users = get_users_by_domain(domain)
        
        # Calculate user stats
        total_users = len(users)
        active_users = len([u for u in users if u.get('status') == 'active'])
        
        # Get email stats (basic implementation - can be enhanced)
        total_emails = 0
        try:
            # Count emails for all users in this domain
            from utils.file_helpers import read_mail_file
            for user in users:
                user_email = user.get('email')
                if user_email:
                    inbox = read_mail_file(user_email, 'inbox')
                    sent = read_mail_file(user_email, 'sent')
                    total_emails += len(inbox) + len(sent)
        except Exception as e:
            print(f"Error calculating email stats: {e}")
            total_emails = 0
        
        # Storage stats (basic implementation)
        total_storage_mb = 0
        try:
            from utils.storage import show_storage_status
            for user in users:
                user_email = user.get('email')
                if user_email:
                    storage = show_storage_status(user_email)
                    total_storage_mb += storage.get('used_mb', 0)
        except Exception as e:
            print(f"Error calculating storage stats: {e}")
            total_storage_mb = 0
        
        storage_used = {
            'used_mb': round(total_storage_mb, 2),
            'total_mb': total_users * 8,  # 8 MB per user
            'percentage': round((total_storage_mb / max(total_users * 8, 1)) * 100, 2)
        }
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_emails': total_emails,
            'storage_used': storage_used
        }, None
        
    except Exception as e:
        return None, f"Error getting company stats: {str(e)}"