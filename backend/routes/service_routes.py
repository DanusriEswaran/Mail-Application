from flask import Blueprint, request, jsonify
from models.user import load_users, is_supported_email, authenticate_user
from models.company import get_company_by_domain
from utils.auth import verify_token, generate_token
from services.mail_service import MailService
from datetime import datetime
import re

service_bp = Blueprint('service', __name__)

# 1. Email Validation API (without registration)
@service_bp.route('/validate_email', methods=['POST'])
def validate_email():
    """Validate if an email format is correct and domain is supported"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check email format
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({
                'valid': False,
                'error': 'Invalid email format'
            }), 200
        
        # Check if domain is supported
        domain_supported = is_supported_email(email)
        
        if not domain_supported:
            return jsonify({
                'valid': False,
                'error': 'Domain not supported'
            }), 200
        
        return jsonify({
            'valid': True,
            'email': email,
            'domain': email.split('@')[1]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

# 2. User Existence Check API
@service_bp.route('/user_exists', methods=['POST'])
def check_user_exists():
    """Check if a user exists in the system"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        users = load_users()
        exists = email in users
        
        response_data = {
            'exists': exists,
            'email': email
        }
        
        if exists:
            user_data = users[email]
            response_data.update({
                'username': user_data.get('username'),
                'status': user_data.get('status', 'active'),
                'created_at': user_data.get('created_at')
            })
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Check failed: {str(e)}'}), 500

# 3. Bulk User Registration API
@service_bp.route('/bulk_register', methods=['POST'])
def bulk_register_users():
    """Register multiple users at once"""
    try:
        data = request.get_json()
        users = data.get('users', [])
        
        if not users or not isinstance(users, list):
            return jsonify({'error': 'Users array is required'}), 400
        
        results = []
        
        for user_data in users:
            username = user_data.get('username', '').strip()
            email = user_data.get('email', '').strip().lower()
            password = user_data.get('password', '').strip()
            
            if not all([username, email, password]):
                results.append({
                    'email': email,
                    'success': False,
                    'error': 'Missing required fields'
                })
                continue
            
            # Import register_user function
            from models.user import register_user
            
            user, error = register_user(username, email, password)
            
            if error:
                results.append({
                    'email': email,
                    'success': False,
                    'error': error
                })
            else:
                results.append({
                    'email': email,
                    'success': True,
                    'user': user
                })
        
        successful = len([r for r in results if r['success']])
        failed = len(results) - successful
        
        return jsonify({
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Bulk registration failed: {str(e)}'}), 500

# 4. Domain Information API
@service_bp.route('/domain_info/<domain>', methods=['GET'])
def get_domain_info(domain):
    """Get information about a domain"""
    try:
        company = get_company_by_domain(domain)
        
        if not company:
            return jsonify({'error': 'Domain not found'}), 404
        
        return jsonify({
            'domain': domain,
            'company_name': company.get('name'),
            'status': company.get('status'),
            'created_at': company.get('created_at'),
            'supported': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Domain info failed: {str(e)}'}), 500

# 5. User Statistics API
@service_bp.route('/user_stats/<email>', methods=['GET'])
def get_user_statistics(email):
    """Get statistics for a specific user"""
    try:
        # Verify user exists
        users = load_users()
        if email not in users:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user stats
        stats, error = MailService.get_stats(email)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'email': email,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Stats retrieval failed: {str(e)}'}), 500

# 6. Send Email API (for external applications)
@service_bp.route('/send_email', methods=['POST'])
def send_email_service():
    """Send email on behalf of external applications"""
    try:
        data = request.get_json()
        
        # Verify API key or token
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # TODO: Implement API key validation - for now, accept any key
        if api_key != 'demo_key_12345':
            return jsonify({'error': 'Invalid API key'}), 401
        
        sender = data.get('from')
        recipient = data.get('to')
        subject = data.get('subject', '')
        body = data.get('body', '')
        attachment = data.get('attachment')
        
        if not all([sender, recipient]):
            return jsonify({'error': 'Sender and recipient are required'}), 400
        
        # Send email
        success, error = MailService.send_mail(sender, recipient, subject, body, attachment)
        
        if not success:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Email sent successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Email sending failed: {str(e)}'}), 500

# 7. Health Check API
@service_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        # Basic health checks
        from pathlib import Path
        from config import DATA_DIR, USERS_FILE
        
        checks = {
            'service': 'running',
            'database': 'connected' if Path(USERS_FILE).exists() else 'disconnected',
            'storage': 'available' if Path(DATA_DIR).exists() else 'unavailable',
            'timestamp': datetime.now().isoformat()
        }
        
        all_healthy = all(status in ['running', 'connected', 'available'] 
                         for status in checks.values() if status != checks['timestamp'])
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks
        }), 200 if all_healthy else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# 8. API Documentation Endpoint
@service_bp.route('/api/docs', methods=['GET'])
def api_documentation():
    """API documentation for Mail as a Service"""
    docs = {
        'service': 'Mail as a Service API',
        'version': '1.0.0',
        'endpoints': {
            'User Management': {
                'POST /register': 'Register a new user',
                'POST /login': 'Authenticate user',
                'POST /verify': 'Verify user token',
                'POST /validate_email': 'Validate email format and domain',
                'POST /user_exists': 'Check if user exists',
                'POST /bulk_register': 'Register multiple users',
                'GET /user_stats/<email>': 'Get user statistics'
            },
            'Company Management': {
                'POST /register_company': 'Register a new company domain',
                'POST /check_domain': 'Check domain availability',
                'GET /domain_info/<domain>': 'Get domain information',
                'GET /companies': 'List all companies'
            },
            'Mail Operations': {
                'POST /send_email': 'Send email (requires API key)',
                'GET /inbox/<email>': 'Get user inbox',
                'GET /sent/<email>': 'Get sent emails',
                'POST /search': 'Search emails'
            },
            'Service': {
                'GET /health': 'Service health check',
                'GET /api/docs': 'This documentation'
            }
        },
        'authentication': {
            'user_endpoints': 'Bearer token in Authorization header',
            'service_endpoints': 'API key in X-API-KEY header'
        }
    }
    
    return jsonify(docs), 200