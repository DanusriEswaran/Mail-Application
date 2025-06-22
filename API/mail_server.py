import json
import hashlib
from unittest import result
import uuid
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from pathlib import Path
import traceback

# Data storage setup
DATA_DIR = Path("mail_data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
EMAILS_FILE = DATA_DIR / "emails.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"

for file_path in [USERS_FILE, EMAILS_FILE, SESSIONS_FILE]:
    if not file_path.exists():
        file_path.write_text("[]")


SUPPORTED_SERVICES = {
    "gmail": {"name": "Gmail", "domain": "gmail.com", "description": "Google Mail Service"},
    "hotmail": {"name": "Hotmail", "domain": "hotmail.com", "description": "Microsoft Hotmail"},
    "outlook": {"name": "Outlook", "domain": "outlook.com", "description": "Microsoft Outlook"},
    "yahoo": {"name": "Yahoo Mail", "domain": "yahoo.com", "description": "Yahoo Mail Service"},
    "custom": {"name": "Custom", "domain": "local.mail", "description": "Custom Local Mail"}
}

class MailService:
    def __init__(self):
        threading.Thread(target=self.cleanup_expired_sessions, daemon=True).start()

    def _load(self, path): 
        try: return json.load(open(path))
        except: return []

    def _save(self, path, data): 
        json.dump(data, open(path, 'w'), indent=2, default=str)

    def _hash(self, password): 
        return hashlib.sha256(password.encode()).hexdigest()

    def _token(self): 
        return str(uuid.uuid4())

    def _validate_email(self, email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if re.match(pattern, email):
            return True 
        else:
            return False

    def _get_user_by_token(self, token):
        if not token: return None
        sessions = self._load(SESSIONS_FILE)
        session = None
        for s in sessions:
            if s["token"] == token:
                session = s
                break
            else:
                return None
        expiry_time = datetime.fromisoformat(session["expires_at"])
        current_time = datetime.now()
        if current_time > expiry_time:
            active_sessions = [s for s in sessions if s["token"] != token]
            self._save(SESSIONS_FILE, active_sessions)
            return None
        users = self._load(USERS_FILE)
        user = next((u for u in users if u["email"] == session["email"]), None)
        return user

    def cleanup_expired_sessions(self):
        while True:
            time.sleep(3600)
            sessions = self._load(SESSIONS_FILE)
            valid_sessions = []
            for session in sessions:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if expires_at > datetime.now():
                    valid_sessions.append(session)
            self._save(SESSIONS_FILE, valid_sessions)

    def register_user(self, data):
        users = self._load(USERS_FILE)
        for field in ["username", "email", "password", "service"]:
            if not data.get(field): return {"error": f"Missing {field}", "status": 400}
        if not self._validate_email(data["email"]): return {"error": "Invalid email", "status": 400}
        if any(u["email"] == data["email"] for u in users): return {"error": "User exists", "status": 400}
        if data["service"] not in SUPPORTED_SERVICES: return {"error": "Service unsupported", "status": 400}

        user = {
            "id": self._token(), "username": data["username"], "email": data["email"],
            "password": self._hash(data["password"]), "service": data["service"],
            "full_name": data.get("full_name", ""), "created_at": datetime.now().isoformat(), "is_active": True
        }
        users.append(user)
        self._save(USERS_FILE, users)
        return {"message": "Registered", "user_id": user["id"], "status": 201}

    def login_user(self, data):
        users = self._load(USERS_FILE)
        email, pwd = data.get("email"), data.get("password")
        if not email or not pwd: return {"error": "Email and password required", "status": 400}

        user = next((u for u in users if u["email"] == email), None)
        if not user or self._hash(pwd) != user["password"]: return {"error": "Invalid credentials", "status": 401}
        if not user.get("is_active", True): return {"error": "Account deactivated", "status": 401}

        token, expires = self._token(), datetime.now() + timedelta(hours=24)
        sessions = [s for s in self._load(SESSIONS_FILE) if s["email"] != email]
        sessions.append({
            "token": token, "email": email, "user_id": user["id"],
            "created_at": datetime.now().isoformat(), "expires_at": expires.isoformat()
        })
        self._save(SESSIONS_FILE, sessions)

        return {"token": token, "user": {k: user[k] for k in ("id", "username", "email", "service", "full_name")},
                "expires_at": expires.isoformat(), "status": 200}

    def logout_user(self, token):
        sessions = [s for s in self._load(SESSIONS_FILE) if s["token"] != token]
        self._save(SESSIONS_FILE, sessions)
        return {"message": "Logged out", "status": 200}

    def get_profile(self, token):
        user = self._get_user_by_token(token)
        return {"user": user, "status": 200} if user else {"error": "Invalid token", "status": 401}

    def send_email(self, token, data):
        user = self._get_user_by_token(token)
        if not user: return {"error": "Invalid token", "status": 401}
        for field in ["to", "subject", "body"]:
            if not data.get(field): return {"error": f"Missing {field}", "status": 400}
        to_field = data.get("to")
        if not isinstance(to_field, list) or not to_field:
            return {
                "error": "'to' must be a list of at least one recipient email address",
                "status": 400
            }

        users = self._load(USERS_FILE)
        valid_emails = [u["email"] for u in users if u.get("is_active", True)]
        recipients = data["to"] + data.get("cc", []) + data.get("bcc", [])
        invalid = [r for r in recipients if r not in valid_emails]
        if invalid: return {"error": f"Invalid recipients: {', '.join(invalid)}", "status": 400}

        emails = self._load(EMAILS_FILE)
        email = {
            "id": self._token(), "from_email": user["email"], "from_service": user["service"],
            "to": data["to"], "cc": data.get("cc", []), "bcc": data.get("bcc", []),
            "subject": data["subject"], "body": data["body"],
            "timestamp": datetime.now().isoformat(), "read_by": []
        }
        emails.append(email)
        self._save(EMAILS_FILE, emails)
        return {"message": "Sent", "email_id": email["id"], "status": 200}

    def get_inbox(self, token):
        user = self._get_user_by_token(token)
        if not user:
            return {"error": "Invalid token", "status": 401}
        user_email = user["email"]
        all_emails = self._load(EMAILS_FILE)
        all_users = self._load(USERS_FILE)
        inbox = []
        for email in all_emails:
            is_recipient = (
                user_email in email.get("to", []) or
                user_email in email.get("cc", []) or
                user_email in email.get("bcc", [])
            )
            if is_recipient:
                sender = next((u for u in all_users if u["email"] == email["from_email"]), None)
                inbox_entry = {
                    "id": email["id"],
                    "from_email": email["from_email"],
                    "to": email.get("to", []),
                    "cc": email.get("cc", []),
                    "bcc": email.get("bcc", []) if user_email == email["from_email"] else [],
                    "subject": email["subject"],
                    "body": email["body"],
                    "timestamp": email["timestamp"],
                    "read": user_email in email.get("read_by", []),
                    "service": sender["service"] if sender else "unknown"
                }
                inbox.append(inbox_entry)
        inbox.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"emails": inbox, "status": 200}


    def get_sent_emails(self, token):
        user = self._get_user_by_token(token)
        if not user: return {"error": "Invalid token", "status": 401}
        emails = self._load(EMAILS_FILE)
        sent = [e for e in emails if e["from_email"] == user["email"]]
        sent.sort(key=lambda x: x["timestamp"], reverse=True)
        sent_emails = []
        for email in sent:
            email_copy = email.copy()
            email_copy["read"] = True
            email_copy["service"] = user["service"]
            sent_emails.append(email_copy)
        return {
            "emails": sent_emails,
            "status": 200
        }

    # def mark_email_read(self, token, email_id):
    #     user = self._get_user_by_token(token)
    #     if not user: return {"error": "Invalid token", "status": 401}
    #     emails = self._load(EMAILS_FILE)
    #     email = next((e for e in emails if e["id"] == email_id), None)
    #     if not email: return {"error": "Email not found", "status": 404}
    #     if user["email"] not in email.get("read_by", []):
    #         email.setdefault("read_by", []).append(user["email"])
    #         self._save(EMAILS_FILE, emails)
    #     return {"message": "Marked as read", "status": 200}

# HTTP Request Handler
class MailHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, mail_service=None):
        self.mail_service = mail_service
        super().__init__(request, client_address, server)

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps(data).encode('utf-8')
        self.wfile.write(response)

    def get_auth_token(self):
        auth = self.headers.get('Authorization')
        return auth[7:] if auth and auth.startswith('Bearer ') else None

    def parse_request_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length:
            try:
                return json.loads(self.rfile.read(length).decode())
            except:
                return {}
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)
        token = self.get_auth_token()

        routes = {
            '/': lambda: {
                "message": "Offline Mail Service API",
                "version": "1.0.0",
                "endpoints": [
                    "GET /services", "POST /register", "POST /login", "POST /logout",
                    "GET /profile", "POST /send", "GET /inbox", "GET /sent",
                    "PUT /email/{id}/read", "GET /users/search", "GET /stats"
                ]
            },
            '/services': lambda: {"services": SUPPORTED_SERVICES},
            '/profile': lambda: self.mail_service.get_profile(token),
            '/inbox': lambda: self.mail_service.get_inbox(token),
            '/sent': lambda: self.mail_service.get_sent_emails(token),
            '/users/search': lambda: self.mail_service.search_users(token, params.get('q', [''])[0]),
            '/stats': lambda: self.mail_service.get_stats(token)
        }

        handler = routes.get(path)
        result = handler() if handler else {"error": "Not found"}
        if isinstance(result, dict):
            status_code = result.get('status', 200)
        else:
            status_code = 200
        self.send_json_response(result, status_code)

    def do_POST(self):
        print(f"POST request received: {self.path}")
        try:
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            data = json.loads(body.decode()) if body else {}
            token = self.get_auth_token()
            if self.path == '/register':
                result = self.mail_service.register_user(data)
            elif self.path == '/login':
                result = self.mail_service.login_user(data)
            elif self.path == '/logout':
                result = self.mail_service.logout_user(token)
            elif self.path == '/send':
                result = self.mail_service.send_email(token, data)
            else:
                result = {"error": "Not found"}
            status = result.get('status', 200)
            self.send_json_response(result, status)
        except Exception as e:
            print("Error handling POST:", e)
            traceback.print_exc()
            self.send_json_response({"error": "Server error"}, 500)

    def do_PUT(self):
        token = self.get_auth_token()
        if self.path.startswith('/email/') and self.path.endswith('/read'):
            email_id = self.path.split('/')[2]
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
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        print("ip: ",ip)
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def run_server(host='0.0.0.0', port=8000):
    print("hello")
    mail_service = MailService()
    handler = create_handler(mail_service)
    try:
        server = HTTPServer((host, port), handler)
    except OSError as e:
        print(f"Could not bind to port {port}: {e}")
        return
    print(f"Server running at http://127.0.0.1:{port}")
    print(f"Network access at http://{get_local_ip()}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server()