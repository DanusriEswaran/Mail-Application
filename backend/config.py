import os
from pathlib import Path

# API Key
API_KEY = '0898c79d9edee1eaf79e1f97718ea84da47472f70884944ba1641b58ed24796c'

# File and directory paths
MAIL_ROOT = 'mail_data'
UPLOAD_FOLDER = os.path.join(MAIL_ROOT, "attachments")
DATA_DIR = Path("mail_users")
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
KEY_FILE = "secret.key"

# Constants
TRASH_EXPIRY_HOURS = 24
MAX_STORAGE = 8 * 1024 * 1024  # 8 MB

# Email service definitions
SUPPORTED_SERVICES = {
    "gmail": {"name": "Gmail", "domain": "gmail.com", "description": "Google Mail Service"},
    "hotmail": {"name": "Hotmail", "domain": "hotmail.com", "description": "Microsoft Hotmail"},
    "outlook": {"name": "Outlook", "domain": "outlook.com", "description": "Microsoft Outlook"},
    "yahoo": {"name": "Yahoo Mail", "domain": "yahoo.com", "description": "Yahoo Mail Service"},
    "custom": {"name": "Custom", "domain": "test.com", "description": "Custom Local Mail"}
}

# Function to load custom domains
def load_custom_domains():
    """Load custom domains from companies.json"""
    try:
        import json
        
        companies_file = DATA_DIR / "companies.json"
        if not companies_file.exists():
            return {}
            
        with open(companies_file, 'r') as f:
            companies = json.load(f)
            
        custom_domains = {}
        for company_id, company in companies.items():
            custom_domains[company_id] = {
                "name": company.get('name', 'Custom Domain'),
                "domain": company.get('domain'),
                "description": f"{company.get('name')} Custom Domain"
            }
            
        return custom_domains
    except Exception:
        return {}

# Update SUPPORTED_SERVICES to include custom domains
SUPPORTED_SERVICES.update(load_custom_domains())

# Create necessary directories
os.makedirs(MAIL_ROOT, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)