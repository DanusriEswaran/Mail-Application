from flask import Flask, request, jsonify, send_from_directory
import uuid, os, json, hashlib
from cryptography.fernet import Fernet
from pathlib import Path
from flask_cors import CORS
from datetime import datetime,  timedelta

UPLOAD_FOLDER = os.path.join("mail_data", "attachments")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Constants
TRASH_EXPIRY_HOURS = 24
KEY_FILE = "secret.key"
MAIL_ROOT = 'mail_data'
MAX_STORAGE = 8 * 1024 * 1024  # 8 MB
DATA_DIR = Path("mail_users")
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
SUPPORTED_SERVICES = {
    "gmail": {"name": "Gmail", "domain": "gmail.com", "description": "Google Mail Service"},
    "hotmail": {"name": "Hotmail", "domain": "hotmail.com", "description": "Microsoft Hotmail"},
    "outlook": {"name": "Outlook", "domain": "outlook.com", "description": "Microsoft Outlook"},
    "yahoo": {"name": "Yahoo Mail", "domain": "yahoo.com", "description": "Yahoo Mail Service"},
    "custom": {"name": "Custom", "domain": "test.com", "description": "Custom Local Mail"}
}

app = Flask(__name__, static_folder=os.path.abspath('../frontend/build'), static_url_path='')
CORS(app)

# Setup encryption
os.makedirs(MAIL_ROOT, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(SESSIONS_FILE):
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]")

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'wb') as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, 'rb') as f:
    key = f.read()

cipher = Fernet(key)

# Users
def generate_user_id(username, password):
    return hashlib.sha256((username + password).encode()).hexdigest()[:16]

def get_user_id(username, password):
    return generate_user_id(username, password)

def load_users():
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def is_supported_email(email):
    return any(email.endswith("@" + service["domain"]) for service in SUPPORTED_SERVICES.values())

#sessions
def create_session(email):
    sessions = load_sessions()
    token = str(uuid.uuid4())
    sessions.append({"email": email, "token": token})
    save_sessions(sessions)
    return token

def load_sessions():
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]")
    with open(SESSIONS_FILE, 'r') as f:
        return json.load(f)

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

def delete_session(token):
    sessions = load_sessions()
    sessions = [s for s in sessions if s['token'] != token]
    save_sessions(sessions)

def get_email_from_token(token):
    sessions = load_sessions()
    for session in sessions:
        if session['token'] == token:
            return session['email']
    return None

# Setup inbox and sent folders
def setup_user_folders(email):
    user_folder = os.path.join(MAIL_ROOT, email)
    folders = ['inbox.json', 'sent.json', 'drafts.json', 'templates.json']
    
    os.makedirs(user_folder, exist_ok=True)
    
    for folder in folders:
        folder_path = os.path.join(user_folder, folder)
        if not os.path.exists(folder_path):
            with open(folder_path, 'w') as f:
                json.dump([], f)

def setup_user_inbox(email):
    setup_user_folders(email) # Keep for backward compatibility, but use setup_user_folders instead

def get_folder_size(path):
    return sum(os.path.getsize(os.path.join(dp, f))
               for dp, _, files in os.walk(path) for f in files)

def show_storage_status(email):
    folder = os.path.join(MAIL_ROOT, email)
    used = get_folder_size(folder)
    percent = (used / MAX_STORAGE) * 100
    return {
        "used_mb": round(used / (1024 * 1024), 2),
        "percentage": round(percent, 2),
        "status": "full" if percent >= 100 else "warning" if percent >= 90 else "ok"
    }

# Routes
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not is_supported_email(email):
        return jsonify({"error": "Unsupported email domain"}), 400

    users = load_users()
    if email in users:
        return jsonify({"error": "User already exists"}), 400

    encrypted_password = cipher.encrypt(password.encode()).decode()

    users[email] = {
        "username": username,
        "password": encrypted_password
    }

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

    user_id = generate_user_id(email, password)
    setup_user_folders(email)

    token = create_session(email)
    return jsonify({
    "message": "User registered successfully",
    "user_id": user_id,
    "username": username,
    "email": email,
    "token": token
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not is_supported_email(email):
        return jsonify({"error": "Unsupported email domain"}), 400

    users = load_users()
    print("users: ",users)
    
    if email in users:
        try:
            encrypted_password = users[email]['password']
            decrypted = cipher.decrypt(encrypted_password.encode()).decode()
            if decrypted == password:
                user_id = generate_user_id(email, password)
                setup_user_folders(email)
                token = create_session(email)
                return jsonify({
                    "message": "Login successful",
                    "email": email,
                    "user_id": user_id,
                    "token": token,
                    "username": users[email]['username']
                })
            else:
                return jsonify({"error": "Incorrect password"}), 401
        except:
            return jsonify({"error": "Decryption failed"}), 500
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/inbox/<email>', methods=['GET'])
def view_inbox(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404

    inbox_file = os.path.join(MAIL_ROOT, email, 'inbox.json')
    if not os.path.exists(inbox_file):
        return jsonify({"inbox": []})

    with open(inbox_file, 'r') as f:
        inbox = json.load(f)

    decrypted_inbox = []
    for mail in inbox:
        try:
            decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
        except:
            decrypted_body = "[Failed to decrypt]"
        decrypted_inbox.append({
            "from": mail['from'],
            "to": mail['to'],
            "subject": mail['subject'],
            "body": decrypted_body,
            "date_of_compose": mail.get('date_of_compose'),
            "date_of_send": mail.get('date_of_send'),
            "message_status": mail.get('message_status'),
            "attachment": mail.get('attachment')
        })

    return jsonify({"inbox": decrypted_inbox})

@app.route('/sent/<email>', methods=['GET'])
def view_sent(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    sent_file = os.path.join(MAIL_ROOT, email, 'sent.json')
    if not os.path.exists(sent_file):
        return jsonify({"sent": []})

    with open(sent_file, 'r') as f:
        sent = json.load(f)

    decrypted_sent = []
    for mail in sent:
        try:
            decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
        except:
            decrypted_body = "[Failed to decrypt]"
        decrypted_sent.append({
            "from": mail['from'],
            "to": mail['to'],
            "subject": mail['subject'],
            "body": decrypted_body,
            "date_of_compose": mail.get('date_of_compose'),
            "date_of_send": mail.get('date_of_send'),
            "message_status": mail.get('message_status'),
            "attachment": mail.get('attachment')
        })

    return jsonify({"sent": decrypted_sent})

@app.route('/drafts/<email>', methods=['GET'])
def view_drafts(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    drafts_file = os.path.join(MAIL_ROOT, email, 'drafts.json')
    if not os.path.exists(drafts_file):
        return jsonify({"drafts": []})
    
    try:
        with open(drafts_file, 'r') as f:
            drafts = json.load(f)
        
        decrypted_drafts = []
        for draft in drafts:
            try:
                decrypted_body = cipher.decrypt(draft['body'].encode()).decode()
            except:
                decrypted_body = "[Failed to decrypt]"
            
            decrypted_drafts.append({
                "from": draft['from'],
                "to": draft['to'],
                "subject": draft['subject'],
                "body": decrypted_body,
                "date_of_compose": draft.get('date_of_compose'),
                "message_status": draft.get('message_status'),
                "attachment": draft.get('attachment')
            })
        
        return jsonify({"drafts": decrypted_drafts})
    except Exception as e:
        return jsonify({"error": "Failed to load drafts"}), 500

@app.route('/templates/<email>', methods=['GET'])
def get_templates(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    templates_file = os.path.join(MAIL_ROOT, email, 'templates.json')
    if not os.path.exists(templates_file):
        return jsonify({"templates": []})
    
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        return jsonify({"templates": templates})
    except Exception as e:
        return jsonify({"error": "Failed to load templates"}), 500

@app.route('/trash/<email>', methods=['GET'])
def view_trash(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    deleted_emails = []
    now = datetime.now()
    
    # Check inbox for deleted emails
    inbox_file = os.path.join(MAIL_ROOT, email, 'inbox.json')
    if os.path.exists(inbox_file):
        with open(inbox_file, 'r') as f:
            inbox = json.load(f)
        
        for mail in inbox:
            if mail.get('message_status') == 'deleted':
                try:
                    decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
                except:
                    decrypted_body = "[Failed to decrypt]"
                
                mail_copy = mail.copy()
                mail_copy['body'] = decrypted_body
                mail_copy['original_folder'] = 'inbox'
                deleted_emails.append(mail_copy)
    
    # Check sent folder for deleted emails
    sent_file = os.path.join(MAIL_ROOT, email, 'sent.json')
    if os.path.exists(sent_file):
        with open(sent_file, 'r') as f:
            sent = json.load(f)
        
        for mail in sent:
            if mail.get('message_status') == 'deleted':
                try:
                    decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
                except:
                    decrypted_body = "[Failed to decrypt]"
                
                mail_copy = mail.copy()
                mail_copy['body'] = decrypted_body
                mail_copy['original_folder'] = 'sent'
                deleted_emails.append(mail_copy)

    # Check scheduled for deleted emails
    scheduled_file = os.path.join(MAIL_ROOT, email, 'scheduled.json')
    if os.path.exists(scheduled_file):
        with open(scheduled_file, 'r') as f:
            scheduled = json.load(f)

        for mail in scheduled:
            if mail.get('message_status') == 'deleted':
                try:
                    decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
                except:
                    decrypted_body = "[Failed to decrypt]"

                mail_copy = mail.copy()
                mail_copy['body'] = decrypted_body
                mail_copy['original_folder'] = 'scheduled'
                deleted_emails.append(mail_copy)

        for mail in inbox:
            if mail.get('message_status') == 'deleted':
                try:
                    decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
                except:
                    decrypted_body = "[Failed to decrypt]"
                
                mail_copy = mail.copy()
                mail_copy['body'] = decrypted_body
                mail_copy['original_folder'] = 'inbox'
                deleted_emails.append(mail_copy)

    return jsonify({"trash": deleted_emails})

@app.route('/storage/<email>', methods=['GET'])
def get_storage_info(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    try:
        storage_info = show_storage_status(email)  # Assuming this function exists
        
        # Convert to expected frontend format
        storage_data = {
            "used_mb": storage_info.get("used_mb", 0),
            "total_mb": storage_info.get("total_mb", 100),  # Default 100MB
            "percentage": storage_info.get("percentage", 0),
            "status": storage_info.get("status", "Normal")
        }
        
        return jsonify(storage_data)
    except Exception as e:
        return jsonify({"error": "Failed to get storage info"}), 500

@app.route('/search', methods=['POST'])
def search_emails():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    query = data.get('query', '').lower()
    folder = data.get('folder', 'inbox')
    
    file_path = f'mail_data/{email}/{folder}.json'
    
    try:
        if not os.path.exists(file_path):
            return jsonify({"results": []})
            
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        results = []
        for mail in mails:
            if mail.get('message_status') == 'deleted' and folder != 'trash':
                continue
                
            try:
                decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
            except:
                decrypted_body = ""
            
            if (query in mail.get('subject', '').lower() or
                query in mail.get('from', '').lower() or
                query in decrypted_body.lower()):
                
                results.append({
                    "from": mail['from'],
                    "to": mail['to'],
                    "subject": mail['subject'],
                    "body": decrypted_body,
                    "date_of_send": mail.get('date_of_send'),
                    "date_of_compose": mail.get('date_of_compose'),
                    "message_status": mail.get('message_status'),
                    "attachment": mail.get('attachment')
                })
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": "Search failed"}), 500

@app.route('/send', methods=['POST'])
def send_mail():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    print("sender: ",sender)

    if not sender:
        return jsonify({"error": "Invalid session"}), 401

    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    attachment = data.get('attachment', None)

    users = load_users()
    if sender not in users or recipient not in users:
        return jsonify({"error": "Sender or recipient not found"}), 404
    
    sender_encrypted_password = users[sender]['password']
    sender_password = cipher.decrypt(sender_encrypted_password.encode()).decode()
    recipient_encrypted_password = users[recipient]['password']
    recipient_password = cipher.decrypt(recipient_encrypted_password.encode()).decode()
    sender_id = generate_user_id(sender, sender_password)
    recipient_id = generate_user_id(recipient, recipient_password)

    if show_storage_status(sender)['status'] == 'full':
        return jsonify({"error": "Sender's inbox is full"}), 403
    if show_storage_status(recipient)['status'] == 'full':
        return jsonify({"error": "Recipient's inbox is full"}), 403

    setup_user_folders(recipient)
    setup_user_folders(sender)

    now = datetime.now().isoformat()

    # Create mail object
    mail = {
        'from': sender,
        'to': recipient,
        'subject': subject,
        'body': cipher.encrypt(body.encode()).decode(),
        'date_of_compose': now,
        'date_of_send': now,
        'message_status': 'unread',
        'attachment': attachment
    }

    # Add to recipient's inbox
    recipient_inbox_file = os.path.join(MAIL_ROOT, recipient, 'inbox.json')
    with open(recipient_inbox_file, 'r') as f:
        recipient_inbox = json.load(f)
    recipient_inbox.append(mail)
    with open(recipient_inbox_file, 'w') as f:
        json.dump(recipient_inbox, f, indent=2)

    # Add to sender's sent folder
    sender_sent_file = os.path.join(MAIL_ROOT, sender, 'sent.json')
    with open(sender_sent_file, 'r') as f:
        sender_sent = json.load(f)
    sender_sent.append(mail)
    with open(sender_sent_file, 'w') as f:
        json.dump(sender_sent, f, indent=2)

    return jsonify({"message": "Email sent successfully"})

@app.route('/schedule', methods=['POST'])
def schedule_email():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401

    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    attachment = data.get('attachment', None)
    scheduled_time = data.get('scheduleTime') 

    print("time scheduled: ",scheduled_time)
    if not scheduled_time:
        return jsonify({"error": "Scheduled time is required"}), 400

    users = load_users()
    if sender not in users or recipient not in users:
        return jsonify({"error": "Sender or recipient not found"}), 404

    sender_encrypted_password = users[sender]['password']
    sender_password = cipher.decrypt(sender_encrypted_password.encode()).decode()
    recipient_encrypted_password = users[recipient]['password']
    recipient_password = cipher.decrypt(recipient_encrypted_password.encode()).decode()
    sender_id = generate_user_id(sender, sender_password)
    recipient_id = generate_user_id(recipient, recipient_password)

    if show_storage_status(sender)['status'] == 'full':
        return jsonify({"error": "Sender's inbox is full"}), 403
    if show_storage_status(recipient)['status'] == 'full':
        return jsonify({"error": "Recipient's inbox is full"}), 403

    setup_user_folders(sender)

    now = datetime.now().isoformat()

    # Mail object with scheduled time
    mail = {
        'from': sender,
        'to': recipient,
        'subject': subject,
        'body': cipher.encrypt(body.encode()).decode(),
        'date_of_compose': now,
        'date_of_send': scheduled_time,
        'message_status': 'scheduled',
        'attachment': attachment
    }

    scheduled_file = os.path.join(MAIL_ROOT, sender, 'scheduled.json')
    if not os.path.exists(scheduled_file):
        with open(scheduled_file, 'w') as f:
            json.dump([], f)

    with open(scheduled_file, 'r') as f:
        scheduled_mails = json.load(f)

    scheduled_mails.append(mail)

    with open(scheduled_file, 'w') as f:
        json.dump(scheduled_mails, f, indent=2)

    return jsonify({"message": "Email scheduled successfully"})

@app.route('/scheduled', methods=['POST'])
def fetch_scheduled_emails():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401

    scheduled_file = os.path.join(MAIL_ROOT, sender, 'scheduled.json')
    if not os.path.exists(scheduled_file):
        return jsonify({"scheduled": []})

    with open(scheduled_file, 'r') as f:
        scheduled_mails = json.load(f)

    decrypted_scheduled = []
    for mail in scheduled_mails:
        try:
            decrypted_body = cipher.decrypt(mail['body'].encode()).decode()
        except:
            decrypted_body = "[Failed to decrypt]"
        decrypted_scheduled.append({
            "from": mail['from'],
            "to": mail['to'],
            "subject": mail['subject'],
            "body": decrypted_body,
            "date_of_compose": mail.get('date_of_compose'),
            "date_of_send": mail.get('date_of_send'),
            "message_status": mail.get('message_status'),
            "attachment": mail.get('attachment')
        })

    return jsonify({"scheduled": decrypted_scheduled})

@app.route('/attachments/<filename>', methods=['GET'])
def get_attachment(filename):
    return send_from_directory(
        UPLOAD_FOLDER, 
        filename, 
        as_attachment=True, 
        download_name=filename.split("_", 1)[1]  
    )

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        token = request.form.get('token')
        email = get_email_from_token(token)
        if not email:
            return jsonify({"error": "Invalid session"}), 401
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join('uploads', email)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_folder, filename)
        
        # Save file
        file.save(file_path)
        
        # Return URL that frontend expects
        file_url = f"/uploads/{email}/{filename}"
        return jsonify({"url": file_url})
        
    except Exception as e:
        return jsonify({"error": "File upload failed"}), 500

@app.route('/uploads/<email>/<filename>')
def serve_uploaded_file(email, filename):
    try:
        upload_folder = os.path.join('uploads', email)
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404

@app.route('/save_template', methods=['POST'])
def save_template():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    template = {
        'name': data.get('name'),
        'subject': data.get('subject'),
        'body': data.get('body'),
        'created_at': datetime.now().isoformat()
    }
    
    templates_file = os.path.join(MAIL_ROOT, email, 'templates.json')
    
    try:
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        
        templates.append(template)
        
        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)
        
        return jsonify({"message": "Template saved successfully"})
    except Exception as e:
        return jsonify({"error": "Failed to save template"}), 500

@app.route('/bulk_action', methods=['POST'])
def bulk_action():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    action = data.get('action')
    emails = data.get('emails')
    folder = data.get('folder', 'inbox')
    
    file_path = f'mail_data/{email}/{folder}.json'
    
    try:
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        updated_count = 0
        for mail in mails:
            for target_email in emails:
                if (mail.get('from') == target_email.get('from') and
                    mail.get('to') == target_email.get('to') and
                    mail.get('subject') == target_email.get('subject') and
                    mail.get('date_of_send') == target_email.get('date_of_send')):
                    
                    if action == 'delete':
                        mail['message_status'] = 'deleted'
                    elif action == 'mark_read':
                        mail['message_status'] = 'read'
                    elif action == 'mark_unread':
                        mail['message_status'] = 'unread'
                    
                    updated_count += 1
                    break
        
        with open(file_path, 'w') as f:
            json.dump(mails, f, indent=2)
        
        return jsonify({"message": f"Bulk action completed on {updated_count} emails"})
    except Exception as e:
        return jsonify({"error": "Bulk action failed"}), 500

@app.route('/delete_mail', methods=['POST'])
def delete_mail():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    active = data.get('activeTab')
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    target_fields = data.get('mail')
    if not target_fields:
        return jsonify({"error": "Missing mail data"}), 400
    file_path = f'mail_data/{email}/{active}.json'
    print("file path: ",file_path)

    try:
        if not os.path.exists(file_path):
            return jsonify({"error": "Mailbox not found"}), 404

        with open(file_path, 'r') as f:
            mails = json.load(f)

        mail_found = False

        for mail in mails:
            if (
                mail.get('from') == target_fields.get('from') and
                mail.get('to') == target_fields.get('to') and
                mail.get('subject') == target_fields.get('subject') and
                mail.get('date_of_send') == target_fields.get('date_of_send')
            ):
                print("hello")
                mail['message_status'] = 'deleted'
                mail_found = True
                break

        if not mail_found:
            return jsonify({"error": "Mail not found"}), 404

        with open(file_path, 'w') as f:
            json.dump(mails, f, indent=2)

        return jsonify({
    "message_status": mail['message_status'],
    "message": "Deleted successfully"
}), 200


    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An error occurred"}), 500

@app.route('/mark_read', methods=['POST'])
def mark_read():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    active = data.get('activeTab', 'inbox')
    
    file_path = f'mail_data/{email}/{active}.json'
    
    try:
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        for mail in mails:
            if (mail.get('from') == target_fields.get('from') and
                mail.get('to') == target_fields.get('to') and
                mail.get('subject') == target_fields.get('subject') and
                mail.get('date_of_send') == target_fields.get('date_of_send')):
                mail['message_status'] = 'read'
                break
        
        with open(file_path, 'w') as f:
            json.dump(mails, f, indent=2)
        
        return jsonify({"message": "Email marked as read"})
    except Exception as e:
        return jsonify({"error": "Failed to mark email"}), 500

@app.route('/mark_unread', methods=['POST'])
def mark_unread():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    active = data.get('activeTab', 'inbox')
    
    file_path = f'mail_data/{email}/{active}.json'
    
    try:
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        for mail in mails:
            if (mail.get('from') == target_fields.get('from') and
                mail.get('to') == target_fields.get('to') and
                mail.get('subject') == target_fields.get('subject') and
                mail.get('date_of_send') == target_fields.get('date_of_send')):
                mail['message_status'] = 'unread'
                break
        
        with open(file_path, 'w') as f:
            json.dump(mails, f, indent=2)
        
        return jsonify({"message": "Email marked as unread"})
    except Exception as e:
        return jsonify({"error": "Failed to mark email"}), 500

@app.route('/save_draft', methods=['POST'])
def save_draft():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401
    
    draft = {
        'from': sender,
        'to': data.get('to', ''),
        'subject': data.get('subject', ''),
        'body': cipher.encrypt(data.get('body', '').encode()).decode(),
        'date_of_compose': datetime.now().isoformat(),
        'message_status': 'draft',
        'attachment': data.get('attachment', None)
    }
    
    drafts_file = os.path.join(MAIL_ROOT, sender, 'drafts.json')
    
    try:
        with open(drafts_file, 'r') as f:
            drafts = json.load(f)
        
        drafts.append(draft)
        
        with open(drafts_file, 'w') as f:
            json.dump(drafts, f, indent=2)
        
        return jsonify({"message": "Draft saved successfully"})
    except Exception as e:
        return jsonify({"error": "Failed to save draft"}), 500

@app.route('/delete_draft', methods=['POST'])
def delete_draft():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('draft')
    
    drafts_file = os.path.join(MAIL_ROOT, email, 'drafts.json')
    
    try:
        with open(drafts_file, 'r') as f:
            drafts = json.load(f)
        
        updated_drafts = []
        for draft in drafts:
            if not (draft.get('from') == target_fields.get('from') and
                   draft.get('to') == target_fields.get('to') and
                   draft.get('subject') == target_fields.get('subject') and
                   draft.get('date_of_compose') == target_fields.get('date_of_compose')):
                updated_drafts.append(draft)
        
        with open(drafts_file, 'w') as f:
            json.dump(updated_drafts, f, indent=2)
        
        return jsonify({"message": "Draft deleted successfully"})
    except Exception as e:
        return jsonify({"error": "Failed to delete draft"}), 500

@app.route('/permanent_delete', methods=['POST'])
def permanent_delete():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    original_folder = target_fields.get('original_folder', 'inbox')
    
    file_path = f'mail_data/{email}/{original_folder}.json'
    
    try:
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        updated_mails = []
        for mail in mails:
            if not (mail.get('from') == target_fields.get('from') and
                   mail.get('to') == target_fields.get('to') and
                   mail.get('subject') == target_fields.get('subject') and
                   mail.get('date_of_send') == target_fields.get('date_of_send')):
                updated_mails.append(mail)
        
        with open(file_path, 'w') as f:
            json.dump(updated_mails, f, indent=2)
        
        return jsonify({"message": "Email permanently deleted"})
    except Exception as e:
        return jsonify({"error": "Failed to delete email"}), 500

@app.route('/restore_email', methods=['POST'])
def restore_email():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    original_folder = target_fields.get('original_folder', 'inbox')
    
    file_path = f'mail_data/{email}/{original_folder}.json'
    
    try:
        with open(file_path, 'r') as f:
            mails = json.load(f)
        
        for mail in mails:
            if (mail.get('from') == target_fields.get('from') and
                mail.get('to') == target_fields.get('to') and
                mail.get('subject') == target_fields.get('subject') and
                mail.get('date_of_send') == target_fields.get('date_of_send')):
                mail['message_status'] = 'unread'
                break
        
        with open(file_path, 'w') as f:
            json.dump(mails, f, indent=2)
        
        return jsonify({"message": "Email restored successfully"})
    except Exception as e:
        return jsonify({"error": "Failed to restore email"}), 500

@app.route('/stats/<email>', methods=['GET'])
def get_email_stats(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    stats = {
        "total_received": 0,
        "total_sent": 0,
        "unread_count": 0,
        "deleted_count": 0,
        "draft_count": 0,
        "storage_used": show_storage_status(email)
    }
    
    try:
        # Count inbox emails
        inbox_file = os.path.join(MAIL_ROOT, email, 'inbox.json')
        if os.path.exists(inbox_file):
            with open(inbox_file, 'r') as f:
                inbox = json.load(f)
            stats["total_received"] = len([m for m in inbox if m.get('message_status') != 'deleted'])
            stats["unread_count"] = len([m for m in inbox if m.get('message_status') == 'unread'])
            stats["deleted_count"] += len([m for m in inbox if m.get('message_status') == 'deleted'])
        
        # Count sent emails
        sent_file = os.path.join(MAIL_ROOT, email, 'sent.json')
        if os.path.exists(sent_file):
            with open(sent_file, 'r') as f:
                sent = json.load(f)
            stats["total_sent"] = len([m for m in sent if m.get('message_status') != 'deleted'])
            stats["deleted_count"] += len([m for m in sent if m.get('message_status') == 'deleted'])
        
        # Count drafts
        drafts_file = os.path.join(MAIL_ROOT, email, 'drafts.json')
        if os.path.exists(drafts_file):
            with open(drafts_file, 'r') as f:
                drafts = json.load(f)
            stats["draft_count"] = len(drafts)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": "Failed to get stats"}), 500

@app.route('/recipients', methods=['GET'])
def get_recipients():
    try:
        users = load_users()
        recipient_list = list(users.keys())
        return jsonify({"recipients": recipient_list})
    except Exception as e:
        return jsonify({"error": "Failed to fetch recipients"}), 500

@app.route('/logout', methods=['POST'])
def logout():
    token = request.json.get('token')
    delete_session(token)
    return jsonify({"message": "Logged out successfully"})

# Run the server
if __name__ == '__main__':
    if not os.path.exists(MAIL_ROOT):
        os.makedirs(MAIL_ROOT)
    app.run(host='0.0.0.0', port=5000, debug=True)
