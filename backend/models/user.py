import json
import hashlib
import re
from config import USERS_FILE, SUPPORTED_SERVICES
from utils.encryption import Encryption
from datetime import datetime

def validate_email_format(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    email = email.strip().lower()
    
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    # Check email length
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address too long"
    
    local_part, domain = email.split('@')
    if len(local_part) > 64:  # RFC 5321 limit
        return False, "Email local part too long"
    
    return True, email

def validate_username(username):
    """Validate username"""
    if not username or not isinstance(username, str):
        return False, "Username must be a non-empty string"
    
    username = username.strip()
    
    if len(username) < 2:
        return False, "Username must be at least 2 characters"
    
    if len(username) > 100:
        return False, "Username too long (max 100 characters)"
    
    # Check for valid characters (letters, numbers, spaces, basic punctuation)
    if not re.match(r'^[a-zA-Z0-9\s\.\-\_]+$', username):
        return False, "Username contains invalid characters"
    
    return True, username

def validate_password(password):
    """Validate password strength"""
    if not password or not isinstance(password, str):
        return False, "Password must be a non-empty string"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if len(password) > 128:
        return False, "Password too long (max 128 characters)"
    
    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, password

def generate_user_id(username, password):
    """Generate a user ID based on username and password"""
    if not username or not password:
        raise ValueError("Username and password are required")
    
    combined = f"{username}:{password}:{datetime.now().isoformat()}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def get_user_id(username, password):
    """Get a user ID (for backward compatibility)"""
    return generate_user_id(username, password)

def load_users():
    """Load users from the users file with error handling"""
    try:
        if not USERS_FILE.exists():
            # Create directory and file if they don't exist
            USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            return {}
            
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            
        # Validate loaded data
        if not isinstance(users, dict):
            print("Warning: users.json contains invalid data, resetting")
            return {}
            
        return users
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in users.json: {e}")
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Save users to the users file with atomic write"""
    try:
        # Validate input
        if not isinstance(users, dict):
            raise ValueError("Users data must be a dictionary")
            
        # Ensure directory exists
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write atomically (write to temp file first)
        temp_file = USERS_FILE.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        # Replace original file
        temp_file.replace(USERS_FILE)
        return True
        
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def is_supported_email(email):
    """Check if an email domain is supported"""
    try:
        # Validate email format first
        valid, cleaned_email = validate_email_format(email)
        if not valid:
            return False
        
        email = cleaned_email
        domain = email.split('@')[1]
        
        # Check if it's one of the supported services
        if any(email.endswith("@" + service["domain"]) for service in SUPPORTED_SERVICES.values()):
            return True
        
        # Check if it's a registered custom domain
        from models.company import get_company_by_domain
        company = get_company_by_domain(domain)
        return company is not None
        
    except Exception as e:
        print(f"Error checking email support: {e}")
        return False

def register_user(username, email, password):
    """Register a new user with comprehensive validation"""
    try:
        # Validate inputs
        valid, clean_username = validate_username(username)
        if not valid:
            return None, clean_username
        
        valid, clean_email = validate_email_format(email)
        if not valid:
            return None, clean_email
        
        valid, clean_password = validate_password(password)
        if not valid:
            return None, clean_password
        
        username = clean_username
        email = clean_email
        password = clean_password
        
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
        
        # Generate user ID
        user_id = generate_user_id(email, password)
        
        # Add new user
        users[email] = {
            "user_id": user_id,
            "username": username,
            "password": encrypted_password,
            "email": email,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0
        }
        
        # Save users
        if not save_users(users):
            return None, "Failed to save user"
        
        # Set up user folders
        from utils.file_helpers import setup_user_folders
        try:
            setup_user_folders(email)
        except Exception as e:
            print(f"Warning: Failed to setup user folders: {e}")
            # Don't fail registration if folder setup fails
        
        # Send welcome email (but not for admin accounts during company creation)
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
            "email": email,
            "status": "active",
            "created_at": users[email]["created_at"]
        }, None
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return None, f"Registration failed: {str(e)}"

def authenticate_user(email, password):
    """Authenticate a user with enhanced security"""
    try:
        # Validate inputs
        if not email or not password:
            return None, "Email and password are required"
        
        valid, clean_email = validate_email_format(email)
        if not valid:
            return None, "Invalid email format"
        
        email = clean_email
        
        # Check if email is supported
        if not is_supported_email(email):
            return None, "Unsupported email domain"
        
        # Load users
        users = load_users()
        
        # Check if user exists
        if email not in users:
            return None, "User not found"
        
        user_data = users[email]
        
        # Check if user is active
        if user_data.get('status') != 'active':
            return None, "Account is inactive"
        
        # Check password
        try:
            encryption = Encryption()
            encrypted_password = user_data['password']
            decrypted = encryption.decrypt(encrypted_password)
            
            if decrypted == password:
                # Update login stats
                users[email]['last_login'] = datetime.now().isoformat()
                users[email]['login_count'] = user_data.get('login_count', 0) + 1
                save_users(users)
                
                user_id = user_data.get('user_id') or generate_user_id(email, password)
                
                return {
                    "user_id": user_id,
                    "email": email,
                    "username": user_data['username'],
                    "status": user_data.get('status', 'active'),
                    "last_login": users[email]['last_login']
                }, None
            else:
                return None, "Incorrect password"
                
        except Exception as e:
            print(f"Error during password verification: {e}")
            return None, "Authentication failed"
            
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None, f"Authentication failed: {str(e)}"

def update_user_last_login(email):
    """Update user's last login timestamp"""
    try:
        if not email:
            return False
            
        valid, clean_email = validate_email_format(email)
        if not valid:
            return False
            
        email = clean_email
        users = load_users()
        
        if email in users:
            users[email]['last_login'] = datetime.now().isoformat()
            users[email]['login_count'] = users[email].get('login_count', 0) + 1
            return save_users(users)
        
        return False
        
    except Exception as e:
        print(f"Error updating last login: {str(e)}")
        return False

def get_users_by_domain(domain):
    """Get all users for a specific domain"""
    try:
        if not domain or not isinstance(domain, str):
            return []
            
        users = load_users()
        domain_users = []
        
        for user_email, user_data in users.items():
            if user_email.endswith(f'@{domain}'):
                domain_users.append({
                    'user_id': user_data.get('user_id', ''),
                    'username': user_data.get('username'),
                    'email': user_email,
                    'status': user_data.get('status', 'active'),
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login'),
                    'login_count': user_data.get('login_count', 0)
                })
        
        return domain_users
        
    except Exception as e:
        print(f"Error getting users by domain: {str(e)}")
        return []

def get_user_stats():
    """Get overall user statistics"""
    try:
        users = load_users()
        
        total_users = len(users)
        active_users = len([u for u in users.values() if u.get('status') == 'active'])
        inactive_users = total_users - active_users
        
        # Calculate users with recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_active = 0
        
        for user_data in users.values():
            last_login = user_data.get('last_login')
            if last_login:
                try:
                    login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    if login_date > thirty_days_ago:
                        recent_active += 1
                except Exception:
                    continue
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'recent_active_users': recent_active
        }
        
    except Exception as e:
        print(f"Error getting user stats: {str(e)}")
        return {'total_users': 0, 'active_users': 0, 'inactive_users': 0, 'recent_active_users': 0}

def update_user_status(email, status):
    """Update user status"""
    try:
        if status not in ['active', 'inactive']:
            return False, "Status must be 'active' or 'inactive'"
            
        valid, clean_email = validate_email_format(email)
        if not valid:
            return False, "Invalid email format"
            
        email = clean_email
        users = load_users()
        
        if email not in users:
            return False, "User not found"
        
        users[email]['status'] = status
        users[email]['updated_at'] = datetime.now().isoformat()
        
        if save_users(users):
            return True, None
        else:
            return False, "Failed to save user data"
            
    except Exception as e:
        print(f"Error updating user status: {e}")
        return False, f"Error updating status: {str(e)}"

def get_user_by_email(email):
    """Get user information by email"""
    try:
        if not email:
            return None
            
        valid, clean_email = validate_email_format(email)
        if not valid:
            return None
            
        email = clean_email
        users = load_users()
        
        if email not in users:
            return None
            
        user_data = users[email]
        return {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'email': email,
            'status': user_data.get('status', 'active'),
            'created_at': user_data.get('created_at'),
            'last_login': user_data.get('last_login'),
            'login_count': user_data.get('login_count', 0),
            'updated_at': user_data.get('updated_at')
        }
        
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None