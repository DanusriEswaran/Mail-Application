# routes/service_routes.py - Enhanced with Encrypted API Support

from flask import Blueprint, request, jsonify
from models.user import load_users, is_supported_email, authenticate_user
from models.company import get_company_by_domain
from utils.auth import verify_token, generate_token
from services.mail_service import MailService
from utils.encryption import EncryptionService
from config import API_KEY
from datetime import datetime
import re
import json

service_bp = Blueprint('service', __name__)

# Initialize encryption service
encryption_service = EncryptionService()

# API Key validation
def validate_api_key():
    """Validate API key from request headers"""
    api_key = request.headers.get('X-API-KEY')
    
    if not api_key or api_key != API_KEY:
        return False, "Invalid or missing API key"
    
    return True, None

def get_client_secret():
    """Get client-specific secret from headers"""
    return request.headers.get('X-CLIENT-SECRET')

def is_encrypted_request():
    """Check if request contains encrypted data"""
    data = request.get_json()
    return data and 'encrypted_data' in data

# ========== ENHANCED VERIFY EMAIL API ==========

@service_bp.route('/verify_email', methods=['POST'])
def verify_email_enhanced():
    """
    Enhanced verify email endpoint supporting both plain and encrypted payloads
    
    Plain Text Request:
    {
        "email": "user@domain.com"
    }
    
    Encrypted Request:
    {
        "encrypted_data": "base64-encoded-encrypted-json",
        "encryption_type": "aes256gcm"  // optional
    }
    """
    try:
        data = request.get_json()
        
        # Check if this is an encrypted request
        if is_encrypted_request():
            # Validate API key for encrypted requests
            valid, error = validate_api_key()
            if not valid:
                return jsonify({'error': error}), 401
            
            client_secret = get_client_secret()
            encrypted_payload = data.get('encrypted_data')
            
            if not encrypted_payload:
                return jsonify({'error': 'Encrypted data is required'}), 400
            
            try:
                # Decrypt the payload
                decrypted_data = encryption_service.process_api_request(encrypted_payload, client_secret)
                email = decrypted_data.get('email', '').strip().lower()
            except Exception as e:
                return jsonify({
                    'error': f'Decryption failed: {str(e)}',
                    'verified': False
                }), 400
            
        else:
            # Handle plain text request (backward compatibility)
            email = data.get('email', '').strip().lower() if data else ''
            
            # Also check query parameter for plain requests
            if not email:
                email = request.args.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email parameter is required'}), 400
        
        # Load users and check if email exists
        users = load_users()
        
        if email in users:
            # Email exists - prepare response
            user_data = users[email]
            response_data = {
                'email': email,
                'exists': True,
                'username': user_data.get('username'),
                'status': user_data.get('status', 'active'),
                'verified': True
            }
            
            # If encrypted request, encrypt the response
            if is_encrypted_request():
                client_secret = get_client_secret()
                encrypted_response = encryption_service.prepare_api_response(response_data, client_secret)
                return jsonify({
                    'encrypted_response': encrypted_response
                }), 200
            else:
                return jsonify(response_data), 200
        else:
            # Email doesn't exist - prepare error response
            error_response = {
                'email': email,
                'exists': False,
                'verified': False,
                'error': 'Email not found'
            }
            
            # If encrypted request, encrypt the error response
            if is_encrypted_request():
                client_secret = get_client_secret()
                encrypted_response = encryption_service.prepare_api_response(error_response, client_secret)
                return jsonify({
                    'encrypted_response': encrypted_response
                }), 404
            else:
                return jsonify(error_response), 404
        
    except Exception as e:
        error_response = {
            'error': f'Verification failed: {str(e)}',
            'verified': False
        }
        
        # If encrypted request, encrypt the error response
        if is_encrypted_request():
            try:
                client_secret = get_client_secret()
                encrypted_response = encryption_service.prepare_api_response(error_response, client_secret)
                return jsonify({
                    'encrypted_response': encrypted_response
                }), 500
            except:
                pass
        
        return jsonify(error_response), 500

# ========== ENHANCED SEND EMAIL API ==========

@service_bp.route('/send_email', methods=['POST'])
def send_email_enhanced():
    """
    Enhanced send email endpoint supporting both plain and encrypted payloads
    
    Plain Text Request:
    {
        "from": "sender@domain.com",
        "to": "recipient@domain.com",
        "subject": "Email Subject",
        "body": "Email content",
        "attachment": null
    }
    
    Encrypted Request:
    {
        "encrypted_data": "base64-encoded-encrypted-json",
        "encryption_type": "aes256gcm"  // optional
    }
    """
    try:
        # Validate API key (required for all send_email requests)
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        data = request.get_json()
        
        # Check if this is an encrypted request
        if is_encrypted_request():
            client_secret = get_client_secret()
            encrypted_payload = data.get('encrypted_data')
            
            if not encrypted_payload:
                return jsonify({'error': 'Encrypted data is required'}), 400
            
            try:
                # Decrypt the payload
                decrypted_data = encryption_service.process_api_request(encrypted_payload, client_secret)
            except Exception as e:
                return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
            
            # Extract email data from decrypted payload
            sender = decrypted_data.get('from')
            recipient = decrypted_data.get('to')
            subject = decrypted_data.get('subject', '')
            body = decrypted_data.get('body', '')
            attachment = decrypted_data.get('attachment')
        else:
            # Handle plain text request (backward compatibility)
            sender = data.get('from')
            recipient = data.get('to')
            subject = data.get('subject', '')
            body = data.get('body', '')
            attachment = data.get('attachment')
        
        if not all([sender, recipient]):
            return jsonify({'error': 'Sender and recipient are required'}), 400
        
        # Send email using existing service
        success, error = MailService.send_mail(sender, recipient, subject, body, attachment)
        
        if not success:
            error_response = {'error': error}
            
            # If encrypted request, encrypt the error response
            if is_encrypted_request():
                client_secret = get_client_secret()
                encrypted_response = encryption_service.prepare_api_response(error_response, client_secret)
                return jsonify({
                    'encrypted_response': encrypted_response
                }), 400
            else:
                return jsonify(error_response), 400
        
        # Prepare success response
        success_response = {
            'success': True,
            'message': 'Email sent successfully',
            'timestamp': datetime.now().isoformat()
        }
        
        # If encrypted request, encrypt the response
        if is_encrypted_request():
            client_secret = get_client_secret()
            encrypted_response = encryption_service.prepare_api_response(success_response, client_secret)
            return jsonify({
                'encrypted_response': encrypted_response
            }), 200
        else:
            return jsonify(success_response), 200
        
    except Exception as e:
        error_response = {'error': f'Email sending failed: {str(e)}'}
        
        # If encrypted request, encrypt the error response
        if is_encrypted_request():
            try:
                client_secret = get_client_secret()
                encrypted_response = encryption_service.prepare_api_response(error_response, client_secret)
                return jsonify({
                    'encrypted_response': encrypted_response
                }), 500
            except:
                pass
        
        return jsonify(error_response), 500

# ========== NEW: ENCRYPTION INFO API ==========

@service_bp.route('/encryption_info', methods=['GET'])
def get_encryption_info():
    """
    Get encryption algorithm information for external applications
    """
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        info = {
            'service': 'Mail Service Encryption API',
            'version': '1.0.0',
            'encryption': {
                'algorithm': 'AES-256-GCM',
                'key_derivation': 'PBKDF2-HMAC-SHA256',
                'iterations': 100000,
                'key_length_bits': 256,
                'nonce_length_bits': 96,
                'salt_length_bits': 128,
                'encoding': 'Base64',
                'data_format': 'JSON'
            },
            'encrypted_request_format': {
                'description': 'Send encrypted data in request body',
                'required_fields': ['encrypted_data'],
                'optional_fields': ['encryption_type'],
                'headers': {
                    'X-API-KEY': 'Required for all encrypted requests',
                    'X-CLIENT-SECRET': 'Optional client-specific password for enhanced security',
                    'Content-Type': 'application/json'
                },
                'example_request': {
                    'encrypted_data': 'eyJjaXBoZXJ0ZXh0IjoiLi4uIiwibm9uY2UiOiIuLi4iLCJ0YWciOiIuLi4ifQ==',
                    'encryption_type': 'aes256gcm'
                }
            },
            'encrypted_response_format': {
                'description': 'Receive encrypted data in response body',
                'format': {
                    'encrypted_response': 'base64-encoded-encrypted-json'
                }
            },
            'supported_endpoints': {
                'verify_email': {
                    'url': '/service/verify_email',
                    'method': 'POST',
                    'supports_encryption': True,
                    'backward_compatible': True,
                    'encrypted_payload_example': {
                        'email': 'user@domain.com'
                    }
                },
                'send_email': {
                    'url': '/service/send_email',
                    'method': 'POST',
                    'supports_encryption': True,
                    'backward_compatible': True,
                    'encrypted_payload_example': {
                        'from': 'sender@domain.com',
                        'to': 'recipient@domain.com',
                        'subject': 'Email Subject',
                        'body': 'Email content',
                        'attachment': None
                    }
                }
            },
            'implementation_examples': {
                'javascript': {
                    'encrypt_request': '''
// Example: Encrypting request data
const payload = { email: "user@domain.com" };
const encryptedData = encryptWithAES256GCM(JSON.stringify(payload), clientSecret);
const request = {
    encrypted_data: btoa(JSON.stringify(encryptedData))
};
''',
                    'decrypt_response': '''
// Example: Decrypting response data
const encryptedResponse = response.encrypted_response;
const decryptedData = JSON.parse(atob(encryptedResponse));
const result = decryptWithAES256GCM(decryptedData, clientSecret);
'''
                },
                'python': {
                    'encrypt_request': '''
# Example: Encrypting request data
import json, base64
from your_encryption_lib import encrypt_aes256gcm

payload = {"email": "user@domain.com"}
encrypted_data = encrypt_aes256gcm(json.dumps(payload), client_secret)
request_data = {"encrypted_data": base64.b64encode(json.dumps(encrypted_data).encode()).decode()}
''',
                    'decrypt_response': '''
# Example: Decrypting response data
import json, base64
from your_encryption_lib import decrypt_aes256gcm

encrypted_response = response_json["encrypted_response"]
decrypted_data = json.loads(base64.b64decode(encrypted_response).decode())
result = decrypt_aes256gcm(decrypted_data, client_secret)
'''
                }
            }
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get encryption info: {str(e)}'}), 500

# ========== EXISTING APIS (Keep unchanged) ==========

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

# Keep all other existing endpoints unchanged...

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
            'encryption': 'enabled',
            'timestamp': datetime.now().isoformat()
        }
        
        all_healthy = all(status in ['running', 'connected', 'available', 'enabled'] 
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

@service_bp.route('/api/docs', methods=['GET'])
def api_documentation():
    """API documentation for Mail as a Service"""
    docs = {
        'service': 'Mail as a Service API',
        'version': '1.0.0',
        'encryption_support': 'AES-256-GCM',
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
            'Mail Operations (Enhanced with Encryption)': {
                'POST /send_email': 'Send email (supports encryption, requires API key)',
                'POST /verify_email': 'Verify email exists (supports encryption)',
                'GET /inbox/<email>': 'Get user inbox',
                'GET /sent/<email>': 'Get sent emails',
                'POST /search': 'Search emails'
            },
            'Encryption': {
                'GET /encryption_info': 'Get encryption algorithm details (requires API key)'
            },
            'Service': {
                'GET /health': 'Service health check',
                'GET /api/docs': 'This documentation'
            }
        },
        'authentication': {
            'user_endpoints': 'Bearer token in Authorization header',
            'service_endpoints': 'API key in X-API-KEY header',
            'encrypted_endpoints': 'API key + optional client secret'
        },
        'encryption_note': 'Enhanced APIs support both plain and encrypted payloads for backward compatibility'
    }
    
    return jsonify(docs), 200