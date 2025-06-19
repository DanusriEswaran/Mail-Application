import json
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from pathlib import Path

# Data storage setup
DATA_DIR = Path("mail_data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
EMAILS_FILE = DATA_DIR / "emails.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

# Initialize data files
for file_path in [USERS_FILE, EMAILS_FILE, SESSIONS_FILE]:
    if not file_path.exists():
        file_path.write_text("[]")

# Supported email services
SUPPORTED_SERVICES = {
    "gmail": {"name": "Gmail", "domain": "gmail.com", "description": "Google Mail Service"},
    "hotmail": {"name": "Hotmail", "domain": "hotmail.com", "description": "Microsoft Hotmail"},
    "outlook": {"name": "Outlook", "domain": "outlook.com", "description": "Microsoft Outlook"},
    "yahoo": {"name": "Yahoo Mail", "domain": "yahoo.com", "description": "Yahoo Mail Service"},
    "custom": {"name": "Custom", "domain": "local.mail", "description": "Custom Local Mail"}
}

class MailService:
    def __init__(self):
        self.cleanup_thread = threading.Thread(target=self.cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def load_json_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_json_file(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed):
        return self.hash_password(password) == hashed
    
    def generate_token(self):
        return str(uuid.uuid4())
    
    def validate_email(self, email):
        return "@" in email and "." in email.split("@")[1]
    
    def get_user_by_token(self, token):
        if not token:
            return None
        
        sessions = self.load_json_file(SESSIONS_FILE)
        session = next((s for s in sessions if s["token"] == token), None)
        
        if not session:
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(session["expires_at"]) 
        if datetime.now() > expires_at:
            # Remove expired session
            sessions = [s for s in sessions if s["token"] != token]
            self.save_json_file(SESSIONS_FILE, sessions)
            return None
        
        users = self.load_json_file(USERS_FILE)
        return next((u for u in users if u["email"] == session["email"]), None)
    
    def cleanup_expired_sessions(self):
        while True:
            time.sleep(3600)  # Check every hour
            sessions = self.load_json_file(SESSIONS_FILE)
            now = datetime.now()
            active_sessions = []
            
            for session in sessions:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if now <= expires_at:
                    active_sessions.append(session)
            
            self.save_json_file(SESSIONS_FILE, active_sessions)
    
    def register_user(self, data):
        print("Arrived")
        users = self.load_json_file(USERS_FILE)
        
        # Validate required fields
        required_fields = ["username", "email", "password", "service"]
        for field in required_fields:
            if field not in data or not data[field]:
                return {"error": f"Missing required field: {field}", "status": 400}
        
        # Validate email format
        if not self.validate_email(data["email"]):
            return {"error": "Invalid email format", "status": 400}
        
        # Check if user exists
        if any(u["email"] == data["email"] for u in users):
            return {"error": "User already exists", "status": 400}
        
        # Validate service
        if data["service"] not in SUPPORTED_SERVICES:
            return {"error": "Unsupported email service", "status": 400}
        
        # Create user
        new_user = {
            "id": str(uuid.uuid4()),
            "username": data["username"],
            "email": data["email"],
            "password": self.hash_password(data["password"]),
            "service": data["service"],
            "full_name": data.get("full_name", ""),
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        users.append(new_user)
        self.save_json_file(USERS_FILE, users)
        
        return {"message": "User registered successfully", "user_id": new_user["id"], "status": 201}
    
    def login_user(self, data):
        users = self.load_json_file(USERS_FILE)
        
        if "email" not in data or "password" not in data:
            return {"error": "Email and password required", "status": 400}
        
        user = next((u for u in users if u["email"] == data["email"]), None)
        if not user or not self.verify_password(data["password"], user["password"]):
            return {"error": "Invalid credentials", "status": 401}
        
        if not user.get("is_active", True):
            return {"error": "Account deactivated", "status": 401}
        
        # Create session
        token = self.generate_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        sessions = self.load_json_file(SESSIONS_FILE)
        # Remove existing sessions for this user
        sessions = [s for s in sessions if s["email"] != user["email"]]
        
        sessions.append({
            "token": token,
            "email": user["email"],
            "user_id": user["id"],
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat()
        })
        
        self.save_json_file(SESSIONS_FILE, sessions)
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "service": user["service"],
                "full_name": user.get("full_name", "")
            },
            "expires_at": expires_at.isoformat(),
            "status": 200
        }
    
    def logout_user(self, token):
        sessions = self.load_json_file(SESSIONS_FILE)
        session = next((s for s in sessions if s["token"] == token), None)
        
        if not session:
            return {"error": "Invalid token", "status": 401}
        
        sessions = [s for s in sessions if s["token"] != token]
        self.save_json_file(SESSIONS_FILE, sessions)
        
        return {"message": "Logged out successfully", "status": 200}
    
    def get_profile(self, token):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        return {
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "service": user["service"],
                "full_name": user.get("full_name", ""),
                "created_at": user["created_at"]
            },
            "status": 200
        }
    
    def send_email(self, token, data):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        # Validate required fields
        required_fields = ["to", "subject", "body"]
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}", "status": 400}
        
        if not isinstance(data["to"], list) or not data["to"]:
            return {"error": "To field must be a non-empty list", "status": 400}
        
        # Validate recipients
        users = self.load_json_file(USERS_FILE)
        user_emails = [u["email"] for u in users if u.get("is_active", True)]
        
        all_recipients = data["to"] + data.get("cc", []) + data.get("bcc", [])
        invalid_recipients = [r for r in all_recipients if r not in user_emails]
        
        if invalid_recipients:
            return {"error": f"Invalid recipients: {', '.join(invalid_recipients)}", "status": 400}
        
        # Create email
        emails = self.load_json_file(EMAILS_FILE)
        email_id = str(uuid.uuid4())
        
        email_record = {
            "id": email_id,
            "from_email": user["email"],
            "from_service": user["service"],
            "to": data["to"],
            "cc": data.get("cc", []),
            "bcc": data.get("bcc", []),
            "subject": data["subject"],
            "body": data["body"],
            "timestamp": datetime.now().isoformat(),
            "read_by": []
        }
        
        emails.append(email_record)
        self.save_json_file(EMAILS_FILE, emails)
        
        return {"message": "Email sent successfully", "email_id": email_id, "status": 200}
    
    def get_inbox(self, token):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        emails = self.load_json_file(EMAILS_FILE)
        users = self.load_json_file(USERS_FILE)
        
        user_email = user["email"]
        inbox_emails = []
        
        for email in emails:
            if (user_email in email["to"] or 
                user_email in email.get("cc", []) or 
                user_email in email.get("bcc", [])):
                
                sender = next((u for u in users if u["email"] == email["from_email"]), None)
                sender_service = sender["service"] if sender else "unknown"
                
                inbox_emails.append({
                    "id": email["id"],
                    "from_email": email["from_email"],
                    "to": email["to"],
                    "cc": email.get("cc", []),
                    "bcc": email.get("bcc", []) if user_email == email["from_email"] else [],
                    "subject": email["subject"],
                    "body": email["body"],
                    "timestamp": email["timestamp"],
                    "read": user_email in email.get("read_by", []),
                    "service": sender_service
                })
        
        # Sort by timestamp (newest first)
        inbox_emails.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"emails": inbox_emails, "status": 200}
    
    def get_sent_emails(self, token):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        emails = self.load_json_file(EMAILS_FILE)
        user_email = user["email"]
        
        sent_emails = []
        for email in emails:
            if email["from_email"] == user_email:
                sent_emails.append({
                    "id": email["id"],
                    "from_email": email["from_email"],
                    "to": email["to"],
                    "cc": email.get("cc", []),
                    "bcc": email.get("bcc", []),
                    "subject": email["subject"],
                    "body": email["body"],
                    "timestamp": email["timestamp"],
                    "read": True,
                    "service": user["service"]
                })
        
        sent_emails.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"emails": sent_emails, "status": 200}
    
    def mark_email_read(self, token, email_id):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        emails = self.load_json_file(EMAILS_FILE)
        email = next((e for e in emails if e["id"] == email_id), None)
        
        if not email:
            return {"error": "Email not found", "status": 404}
        
        user_email = user["email"]
        if (user_email not in email["to"] and 
            user_email not in email.get("cc", []) and 
            user_email not in email.get("bcc", [])):
            return {"error": "Access denied", "status": 403}
        
        if user_email not in email.get("read_by", []):
            email["read_by"].append(user_email)
            self.save_json_file(EMAILS_FILE, emails)
        
        return {"message": "Email marked as read", "status": 200}
    
    def search_users(self, token, query=""):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        users = self.load_json_file(USERS_FILE)
        current_email = user["email"]
        
        filtered_users = []
        for u in users:
            if not u.get("is_active", True) or u["email"] == current_email:
                continue
            
            if not query or (
                query.lower() in u["email"].lower() or
                query.lower() in u["username"].lower() or
                query.lower() in u.get("full_name", "").lower()
            ):
                filtered_users.append({
                    "email": u["email"],
                    "username": u["username"],
                    "full_name": u.get("full_name", ""),
                    "service": u["service"]
                })
        
        return {"users": filtered_users, "status": 200}
    
    def get_stats(self, token):
        user = self.get_user_by_token(token)
        if not user:
            return {"error": "Invalid or expired token", "status": 401}
        
        emails = self.load_json_file(EMAILS_FILE)
        user_email = user["email"]
        
        sent_count = len([e for e in emails if e["from_email"] == user_email])
        
        received_count = len([
            e for e in emails 
            if (user_email in e["to"] or 
                user_email in e.get("cc", []) or 
                user_email in e.get("bcc", []))
        ])
        
        unread_count = len([
            e for e in emails 
            if (user_email in e["to"] or 
                user_email in e.get("cc", []) or 
                user_email in e.get("bcc", [])) and
            user_email not in e.get("read_by", [])
        ])
        
        return {
            "stats": {
                "sent": sent_count,
                "received": received_count,
                "unread": unread_count
            },
            "status": 200
        }

# HTTP Request Handler
class MailHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, mail_service=None, **kwargs):
        self.mail_service = mail_service
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_auth_token(self):
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    def parse_request_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            body = self.rfile.read(content_length)
            try:
                return json.loads(body.decode())
            except:
                return {}
        return {}
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/':
            self.send_json_response({
                "message": "Offline Mail Service API",
                "version": "1.0.0",
                "endpoints": [
                    "GET /services", "POST /register", "POST /login", "POST /logout",
                    "GET /profile", "POST /send", "GET /inbox", "GET /sent",
                    "PUT /email/{id}/read", "GET /users/search", "GET /stats"
                ]
            })
        
        elif path == '/services':
            self.send_json_response({"services": SUPPORTED_SERVICES})
        
        elif path == '/profile':
            token = self.get_auth_token()
            result = self.mail_service.get_profile(token)
            self.send_json_response(result, result.get('status', 200))
        
        elif path == '/inbox':
            token = self.get_auth_token()
            result = self.mail_service.get_inbox(token)
            self.send_json_response(result, result.get('status', 200))
        
        elif path == '/sent':
            token = self.get_auth_token()
            result = self.mail_service.get_sent_emails(token)
            self.send_json_response(result, result.get('status', 200))
        
        elif path == '/users/search':
            token = self.get_auth_token()
            query = query_params.get('q', [''])[0]
            result = self.mail_service.search_users(token, query)
            self.send_json_response(result, result.get('status', 200))
        
        elif path == '/stats':
            token = self.get_auth_token()
            result = self.mail_service.get_stats(token)
            self.send_json_response(result, result.get('status', 200))
        
        else:
            self.send_json_response({"error": "Not found"}, 404)
    
    # Replace your existing do_POST method with this enhanced version:

    def do_POST(self):
        print("=" * 50)
        print(f"POST request received for path: {self.path}")
        print(f"Headers: {dict(self.headers)}")
        
        try:
            # Check content length first
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"Content-Length: {content_length}")
            
            if content_length > 0:
                body = self.rfile.read(content_length)
                print(f"Raw body: {body}")
                
                try:
                    data = json.loads(body.decode())
                    print(f"Parsed data: {data}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    self.send_json_response({"error": "Invalid JSON"}, 400)
                    return
            else:
                data = {}
                print("No body data")
            
            if self.path == '/register':
                print("Processing registration...")
                result = self.mail_service.register_user(data)
                print(f"Registration result: {result}")
                status_code = result.get('status', 200)
                self.send_json_response(result, status_code)
            
            elif self.path == '/login':
                print("Processing login...")
                result = self.mail_service.login_user(data)
                print(f"Login result: {result}")
                status_code = result.get('status', 200)
                self.send_json_response(result, status_code)
            
            elif self.path == '/logout':
                print("Processing logout...")
                token = self.get_auth_token()
                result = self.mail_service.logout_user(token)
                print(f"Logout result: {result}")
                status_code = result.get('status', 200)
                self.send_json_response(result, status_code)
            
            elif self.path == '/send':
                print("Processing send email...")
                token = self.get_auth_token()
                result = self.mail_service.send_email(token, data)
                print(f"Send email result: {result}")
                status_code = result.get('status', 200)
                self.send_json_response(result, status_code)
            
            else:
                print(f"Unknown POST endpoint: {self.path}")
                self.send_json_response({"error": "Not found"}, 404)
                
        except Exception as e:
            print(f"CRITICAL ERROR in do_POST: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_json_response({"error": f"Server error: {str(e)}"}, 500)
            except:
                print("Failed to send error response")
        
        print("=" * 50)
    
    def do_PUT(self):
        path = self.path
        token = self.get_auth_token()
        
        if path.startswith('/email/') and path.endswith('/read'):
            email_id = path.split('/')[2]
            result = self.mail_service.mark_email_read(token, email_id)
            self.send_json_response(result, result.get('status', 200))
        
        else:
            self.send_json_response({"error": "Not found"}, 404)

def create_handler(mail_service):
    def handler(*args, **kwargs):
        MailHandler(*args, mail_service=mail_service, **kwargs)
    return handler

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Using Google's DNS as a dummy destination
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def run_server(host='0.0.0.0', port=8000):
    print("Yes")
    mail_service = MailService()
    handler = create_handler(mail_service)
    
    # Create the server first to catch port binding errors
    try:
        server = HTTPServer((host, port), handler)
    except OSError as e:
        print(f"Error: Could not bind to port {port}")
        print(f"Details: {e}")
        return
    
    local_ip = get_local_ip()
    print("=" * 50)
    print("📧 OFFLINE MAIL SERVICE STARTED")
    print("=" * 50)
    print(f"🏠 Local access:   http://127.0.0.1:{port}")
    print(f"🌐 Network access: http://{local_ip}:{port}")
    print("=" * 50)
    print("📋 Available endpoints:")
    print("  GET  /                 - API info")
    print("  GET  /services         - List supported services")
    print("  POST /register         - Register user")
    print("  POST /login           - Login user")
    print("  POST /logout          - Logout user")
    print("  GET  /profile         - Get user profile")
    print("  POST /send            - Send email")
    print("  GET  /inbox           - Get inbox")
    print("  GET  /sent            - Get sent emails")
    print("  PUT  /email/{id}/read - Mark email as read")
    print("  GET  /users/search    - Search users")
    print("  GET  /stats           - Get statistics")
    print("=" * 50)
    print("💡 Share the network URL with other devices on your WiFi")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("🛑 Shutting down server...")
        print("=" * 50)
        server.shutdown()

if __name__ == "__main__":
    run_server()