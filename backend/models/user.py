import json
import hashlib
from config import USERS_FILE, SUPPORTED_SERVICES
from utils.encryption import Encryption
from datetime import datetime
def generate_user_id(username, password):
    """Generate a user ID based on username and password"""
    return hashlib.sha256((username + password).encode()).hexdigest()[:16]

def get_user_id(username, password):
    """Get a user ID (for backward compatibility)"""
    return generate_user_id(username, password)

def load_users():
    """Load users from the users file"""
    try:
        if not USERS_FILE.exists():
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    """Save users to the users file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False

def is_supported_email(email):
    """Check if an email domain is supported"""
    # Check if it's one of the default supported services
    if any(email.endswith("@" + service["domain"]) for service in SUPPORTED_SERVICES.values()):
        return True
    
    # Check if it's a registered custom domain
    try:
        domain = email.split('@')[1]
        from models.company import get_company_by_domain
        company = get_company_by_domain(domain)
        return company is not None
    except:
        return False

def register_user(username, email, password):
    """Register a new user"""
    # Check if email is supported
    if not is_supported_email(email):
        return None, "Unsupported email domain"
    
    # Load existing users
    users = load_users()
    
    # Check if user already exists
    if email in users:
        return None, "User already exists"
    
    # Encrypt password
    encryption = Encryption()
    encrypted_password = encryption.encrypt(password)
    
    # Add new user
    users[email] = {
        "username": username,
        "password": encrypted_password,
        "email": email,  # Add email to user data
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    # Save users
    if not save_users(users):
        return None, "Failed to save user"
    
    # Set up user folders
    from utils.file_helpers import setup_user_folders
    setup_user_folders(email)
    
    # Generate user ID
    user_id = generate_user_id(email, password)
    
    # Send welcome email (but not for admin accounts during company creation)
    # This will be handled separately for company admin creation
    if not email.startswith('admin@'):
        try:
            from models.company import send_welcome_email
            send_welcome_email(email, username)
        except Exception as e:
            print(f"Warning: Failed to send welcome email: {e}")
            # Don't fail registration if welcome email fails
    
    return {
        "user_id": user_id,
        "username": username,
        "email": email
    }, None

def authenticate_user(email, password):
    """Authenticate a user"""
    # Check if email is supported
    if not is_supported_email(email):
        return None, "Unsupported email domain"
    
    # Load users
    users = load_users()
    
    # Check if user exists
    if email not in users:
        return None, "User not found"
    
    # Check password
    try:
        encryption = Encryption()
        encrypted_password = users[email]['password']
        decrypted = encryption.decrypt(encrypted_password)
        
        if decrypted == password:
            user_id = generate_user_id(email, password)
            return {
                "user_id": user_id,
                "email": email,
                "username": users[email]['username']
            }, None
        else:
            return None, "Incorrect password"
    except Exception:
        return None, "Authentication failed"
    
# Add these functions to your existing user.py model

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

def update_user_last_login(email):
    """Update user's last login timestamp"""
    try:
        from datetime import datetime
        users = load_users()
        
        for user_id, user in users.items():
            if user.get('email') == email:
                users[user_id]['last_login'] = datetime.now().isoformat()
                save_users(users)
                return True
        
        return False
        
    except Exception as e:
        print(f"Error updating last login: {str(e)}")
        return False

def get_user_stats():
    """Get overall user statistics"""
    try:
        users = load_users()
        
        total_users = len(users)
        active_users = len([u for u in users.values() if u.get('status') == 'active'])
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users
        }
        
    except Exception as e:
        print(f"Error getting user stats: {str(e)}")
        return {'total_users': 0, 'active_users': 0, 'inactive_users': 0}