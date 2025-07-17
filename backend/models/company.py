import json
import os
from pathlib import Path
from datetime import datetime
from config import DATA_DIR
from utils.encryption import Encryption
from models.user import register_user
from services.mail_service import MailService
from utils.file_helpers import setup_user_folders

# Constants
COMPANIES_FILE = DATA_DIR / "companies.json"

def load_companies():
    """Load companies from the companies file"""
    try:
        if not COMPANIES_FILE.exists():
            with open(COMPANIES_FILE, 'w') as f:
                json.dump({}, f)
        with open(COMPANIES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_companies(companies):
    """Save companies to the companies file"""
    try:
        with open(COMPANIES_FILE, 'w') as f:
            json.dump(companies, f, indent=2)
        return True
    except Exception:
        return False

def is_domain_available(domain):
    """Check if a domain is available"""
    companies = load_companies()
    
    # Check if domain is already registered
    for company_id, company in companies.items():
        if company.get('domain') == domain:
            return False
    
    # Check if domain is in the supported services
    from config import SUPPORTED_SERVICES
    for service_key, service in SUPPORTED_SERVICES.items():
        if service.get('domain') == domain:
            return False
    
    return True

def register_company(company_name, domain, admin_name, admin_email=None):
    """Register a new company"""
    # Validate domain format
    if not domain or '.' not in domain:
        return None, "Invalid domain format. Please use format like 'example.com'"
    
    # Check if domain is available
    if not is_domain_available(domain):
        return None, f"Domain '{domain}' is already registered"
    
    # Create company entry
    company_id = company_name.lower().replace(' ', '_')
    
    # Check if company ID is unique
    companies = load_companies()
    if company_id in companies:
        # Add a number to make it unique
        base_id = company_id
        counter = 1
        while company_id in companies:
            company_id = f"{base_id}_{counter}"
            counter += 1
    
    # Create company record with proper timestamp
    companies[company_id] = {
        'name': company_name,
        'domain': domain,
        'admin_name': admin_name,
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    # Save companies
    if not save_companies(companies):
        return None, "Failed to save company data"
    
    # Add domain to supported services BEFORE creating admin user
    from config import SUPPORTED_SERVICES
    SUPPORTED_SERVICES[company_id] = {
        "name": company_name,
        "domain": domain,
        "description": f"{company_name} Custom Domain"
    }
    
    # Create admin account automatically
    admin_email = f"admin@{domain}"
    admin_password = "admin@1234"  # Default password
    
    # Register admin user
    admin_user, error = register_user(admin_name, admin_email, admin_password)
    if error:
        # If failed to create admin, rollback company creation
        del companies[company_id]
        save_companies(companies)
        # Also remove from supported services
        if company_id in SUPPORTED_SERVICES:
            del SUPPORTED_SERVICES[company_id]
        return None, f"Failed to create admin account: {error}"
    
    # Send welcome email to admin (since we skipped it in register_user for admin accounts)
    try:
        # Create a simple welcome email for the admin
        from services.mail_service import MailService
        
        subject = f"Welcome to {company_name} Mail - Admin Account Created"
        body = f"""Hello {admin_name},

Your company '{company_name}' has been successfully registered in our mail system!

Your admin account details:
- Email: {admin_email}
- Password: {admin_password}
- Domain: {domain}

As an admin, you can now:
- Access the admin panel
- Monitor company email statistics
- Manage users in your domain

Please change your password after first login for security.

Best regards,
Mail System Team
"""
        
        # For admin welcome, we'll save it directly to their inbox since there's no other admin to send from
        from utils.encryption import Encryption
        encryption = Encryption()
        encrypted_body = encryption.encrypt(body)
        
        now = datetime.now().isoformat()
        
        admin_welcome_mail = {
            'from': 'system@mailservice.com',
            'to': admin_email,
            'subject': subject,
            'body': encrypted_body,
            'date_of_compose': now,
            'date_of_send': now,
            'message_status': 'unread',
            'attachment': None
        }
        
        # Add to admin's inbox
        from utils.file_helpers import read_mail_file, save_mail_file
        admin_inbox = read_mail_file(admin_email, 'inbox')
        admin_inbox.append(admin_welcome_mail)
        save_mail_file(admin_email, 'inbox', admin_inbox)
        
    except Exception as e:
        print(f"Warning: Failed to send admin welcome email: {e}")
        # Don't fail company registration if welcome email fails
    
    return {
        'company_id': company_id,
        'name': company_name,
        'domain': domain,
        'admin_email': admin_email,
        'admin_password': admin_password
    }, None
def get_company_by_domain(domain):
    """Get company information by domain"""
    companies = load_companies()
    
    for company_id, company in companies.items():
        if company.get('domain') == domain:
            return {
                'company_id': company_id,
                'name': company.get('name'),
                'domain': domain,
                'admin_name': company.get('admin_name'),
                'status': company.get('status', 'active'),
                'created_at': company.get('created_at')
            }
    
    return None

def get_all_companies():
    """Get all registered companies"""
    companies = load_companies()
    company_list = []
    
    for company_id, company in companies.items():
        company_list.append({
            'id': company_id,
            'name': company.get('name'),
            'domain': company.get('domain'),
            'admin_name': company.get('admin_name'),
            'status': company.get('status', 'active'),
            'created_at': company.get('created_at')
        })
    
    return company_list

def get_admin_email_by_domain(domain):
    """Get admin email for a domain"""
    return f"admin@{domain}"

def update_company_status(company_id, status):
    """Update company status (active/inactive)"""
    companies = load_companies()
    
    if company_id in companies:
        companies[company_id]['status'] = status
        if save_companies(companies):
            return True, None
        else:
            return False, "Failed to save company data"
    
    return False, "Company not found"

def delete_company(company_id):
    """Delete a company (use with caution)"""
    companies = load_companies()
    
    if company_id in companies:
        # Get domain before deletion
        domain = companies[company_id].get('domain')
        
        # Remove from companies
        del companies[company_id]
        
        # Remove from supported services
        from config import SUPPORTED_SERVICES
        if company_id in SUPPORTED_SERVICES:
            del SUPPORTED_SERVICES[company_id]
        
        # Save changes
        if save_companies(companies):
            return True, None
        else:
            return False, "Failed to save company data"
    
    return False, "Company not found"

def send_welcome_email(user_email, username):
    """Send welcome email to new user from their domain admin"""
    try:
        # Extract domain from email
        domain = user_email.split('@')[1]
        
        # Get company info
        company = get_company_by_domain(domain)
        admin_email = f"admin@{domain}"
        
        if company:
            # Custom domain company
            company_name = company.get('name')
        else:
            # Check if it's one of the default domains
            from config import SUPPORTED_SERVICES
            company_name = None
            for service_key, service in SUPPORTED_SERVICES.items():
                if service.get('domain') == domain:
                    company_name = service.get('name', 'Mail Service')
                    break
            
            if not company_name:
                return False, "Unknown domain"
        
        # Prepare welcome email
        subject = f"Welcome to {company_name} Mail!"
        body = f"""Hello {username},

Welcome to {company_name} Mail!

Your account has been successfully created. You can now send and receive emails using your new address: {user_email}.

Getting started:
- Log in to your account to start sending and receiving emails
- Check your inbox regularly for new messages
- Use the compose feature to send emails to other users

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The {company_name} Team
"""
        
        # Send email using mail service
        from services.mail_service import MailService
        success, error = MailService.send_mail(admin_email, user_email, subject, body)
        
        if not success:
            return False, f"Failed to send welcome email: {error}"
        
        return True, None
        
    except Exception as e:
        return False, f"Error sending welcome email: {str(e)}"
    
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
