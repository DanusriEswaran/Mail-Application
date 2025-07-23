# routes/encrypted_service_routes.py - Corrected version
from flask import Blueprint, request, jsonify
from models.user import load_users, register_user, authenticate_user
from models.company import get_company_by_domain
from utils.encryption import EncryptionService
from services.mail_service import MailService
from config import API_KEY
from datetime import datetime
import json
import re

encrypted_service_bp = Blueprint('encrypted_service', __name__, url_prefix='/api/v1/encrypted')

# Initialize encryption service
encryption_service = EncryptionService()

# API Key validation
def validate_api_key():
    """Validate API key from request headers"""
    api_key = request.headers.get('X-API-KEY')
    
    if not api_key or api_key != API_KEY:
        return False, "Invalid or missing API key"
    
    return True, None

def get_client_password():
    """Get client-specific password from headers"""
    return request.headers.get('X-CLIENT-SECRET')

# ========== ENCRYPTED EMAIL OPERATIONS ==========

@encrypted_service_bp.route('/send_email', methods=['POST'])
def send_encrypted_email():
    """
    Send email with encrypted payload
    
    Expected encrypted payload structure:
    {
        "from": "sender@domain.com",
        "to": "recipient@domain.com", 
        "subject": "Email subject",
        "body": "Email body content",
        "attachment": null (optional)
    }
    """
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        # Get client password for decryption
        client_password = get_client_password()
        
        # Get encrypted payload
        data = request.get_json()
        encrypted_payload = data.get('encrypted_data')
        
        if not encrypted_payload:
            return jsonify({'error': 'Encrypted data is required'}), 400
        
        # Decrypt the payload
        try:
            decrypted_data = encryption_service.process_api_request(encrypted_payload, client_password)
        except Exception as e:
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        
        # Extract email data
        sender = decrypted_data.get('from')
        recipient = decrypted_data.get('to')
        subject = decrypted_data.get('subject', '')
        body = decrypted_data.get('body', '')
        attachment = decrypted_data.get('attachment')
        
        if not all([sender, recipient]):
            return jsonify({'error': 'Sender and recipient are required'}), 400
        
        # Send email using existing service
        success, error = MailService.send_mail(sender, recipient, subject, body, attachment)
        
        if not success:
            return jsonify({'error': error}), 400
        
        # Prepare encrypted response
        response_data = {
            'success': True,
            'message': 'Email sent successfully',
            'timestamp': datetime.now().isoformat()
        }
        
        encrypted_response = encryption_service.prepare_api_response(response_data, client_password)
        
        return jsonify({
            'encrypted_response': encrypted_response
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Email sending failed: {str(e)}'}), 500

@encrypted_service_bp.route('/get_inbox', methods=['POST'])
def get_encrypted_inbox():
    """
    Get user's inbox with encrypted response
    
    Expected encrypted payload:
    {
        "email": "user@domain.com"
    }
    """
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        client_password = get_client_password()
        
        # Get encrypted payload
        data = request.get_json()
        encrypted_payload = data.get('encrypted_data')
        
        if not encrypted_payload:
            return jsonify({'error': 'Encrypted data is required'}), 400
        
        # Decrypt the payload
        try:
            decrypted_data = encryption_service.process_api_request(encrypted_payload, client_password)
        except Exception as e:
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        
        email = decrypted_data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Get inbox
        inbox, error = MailService.get_inbox(email)
        
        if error:
            return jsonify({'error': error}), 404
        
        # Prepare encrypted response
        response_data = {
            'inbox': inbox,
            'count': len(inbox),
            'email': email
        }
        
        encrypted_response = encryption_service.prepare_api_response(response_data, client_password)
        
        return jsonify({
            'encrypted_response': encrypted_response
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Inbox retrieval failed: {str(e)}'}), 500

@encrypted_service_bp.route('/register_user', methods=['POST'])
def register_encrypted_user():
    """
    Register user with encrypted payload
    
    Expected encrypted payload:
    {
        "username": "John Doe",
        "email": "john@domain.com",
        "password": "securepassword"
    }
    """
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        client_password = get_client_password()
        
        # Get encrypted payload
        data = request.get_json()
        encrypted_payload = data.get('encrypted_data')
        
        if not encrypted_payload:
            return jsonify({'error': 'Encrypted data is required'}), 400
        
        # Decrypt the payload
        try:
            decrypted_data = encryption_service.process_api_request(encrypted_payload, client_password)
        except Exception as e:
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        
        username = decrypted_data.get('username')
        email = decrypted_data.get('email')
        password = decrypted_data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Register user
        user, error = register_user(username, email, password)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Prepare encrypted response
        response_data = {
            'success': True,
            'message': 'User registered successfully',
            'user': user
        }
        
        encrypted_response = encryption_service.prepare_api_response(response_data, client_password)
        
        return jsonify({
            'encrypted_response': encrypted_response
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'User registration failed: {str(e)}'}), 500

@encrypted_service_bp.route('/bulk_send', methods=['POST'])
def bulk_send_encrypted():
    """
    Send multiple emails with encrypted payload
    
    Expected encrypted payload:
    {
        "emails": [
            {
                "from": "sender@domain.com",
                "to": "recipient1@domain.com",
                "subject": "Subject 1",
                "body": "Body 1"
            },
            {
                "from": "sender@domain.com", 
                "to": "recipient2@domain.com",
                "subject": "Subject 2", 
                "body": "Body 2"
            }
        ]
    }
    """
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        client_password = get_client_password()
        
        # Get encrypted payload
        data = request.get_json()
        encrypted_payload = data.get('encrypted_data')
        
        if not encrypted_payload:
            return jsonify({'error': 'Encrypted data is required'}), 400
        
        # Decrypt the payload
        try:
            decrypted_data = encryption_service.process_api_request(encrypted_payload, client_password)
        except Exception as e:
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        
        emails = decrypted_data.get('emails', [])
        
        if not emails:
            return jsonify({'error': 'Email list is required'}), 400
        
        results = []
        successful = 0
        failed = 0
        
        for email_data in emails:
            try:
                sender = email_data.get('from')
                recipient = email_data.get('to')
                subject = email_data.get('subject', '')
                body = email_data.get('body', '')
                attachment = email_data.get('attachment')
                
                if not all([sender, recipient]):
                    results.append({
                        'to': recipient,
                        'success': False,
                        'error': 'Sender and recipient are required'
                    })
                    failed += 1
                    continue
                
                success, error = MailService.send_mail(sender, recipient, subject, body, attachment)
                
                if success:
                    results.append({
                        'to': recipient,
                        'success': True,
                        'message': 'Email sent successfully'
                    })
                    successful += 1
                else:
                    results.append({
                        'to': recipient,
                        'success': False,
                        'error': error
                    })
                    failed += 1
                    
            except Exception as e:
                results.append({
                    'to': email_data.get('to', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
                failed += 1
        
        # Prepare encrypted response
        response_data = {
            'total': len(emails),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
        encrypted_response = encryption_service.prepare_api_response(response_data, client_password)
        
        return jsonify({
            'encrypted_response': encrypted_response
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Bulk email sending failed: {str(e)}'}), 500

# ========== ENCRYPTION UTILITY ENDPOINTS ==========

@encrypted_service_bp.route('/test_encryption', methods=['POST'])
def test_encryption():
    """Test endpoint for encryption/decryption"""
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        data = request.get_json()
        test_data = data.get('test_data', 'Hello, World!')
        client_password = get_client_password()
        
        # Encrypt test data
        encrypted = encryption_service.encryption.encrypt_for_api(test_data, client_password)
        
        # Decrypt it back
        decrypted = encryption_service.encryption.decrypt_from_api(encrypted, client_password)
        
        return jsonify({
            'original': test_data,
            'encrypted': encrypted,
            'decrypted': decrypted,
            'success': test_data == decrypted
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Encryption test failed: {str(e)}'}), 500

@encrypted_service_bp.route('/encryption_info', methods=['GET'])
def get_encryption_info():
    """Get information about the encryption algorithm"""
    try:
        # Validate API key
        valid, error = validate_api_key()
        if not valid:
            return jsonify({'error': error}), 401
        
        info = {
            'algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2-HMAC-SHA256',
            'iterations': 100000,
            'key_length': 256,
            'nonce_length': 96,
            'salt_length': 128,
            'encoding': 'Base64',
            'data_format': 'JSON',
            'required_fields': ['ciphertext', 'nonce', 'tag', 'algorithm'],
            'optional_fields': ['salt', 'iterations'],
            'example_usage': {
                'headers': {
                    'X-API-KEY': 'your-api-key',
                    'X-CLIENT-SECRET': 'optional-client-password',
                    'Content-Type': 'application/json'
                },
                'body': {
                    'encrypted_data': 'base64-encoded-json-string'
                }
            }
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get encryption info: {str(e)}'}), 500

# ========== ERROR HANDLERS ==========

@encrypted_service_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@encrypted_service_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Invalid API key'}), 401

@encrypted_service_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500