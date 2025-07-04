from flask import Flask, request, jsonify, send_from_directory
import uuid, os, json, hashlib
from cryptography.fernet import Fernet
from pathlib import Path
from flask_cors import CORS
from datetime import datetime

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
    "custom": {"name": "Custom", "domain": "local.mail", "description": "Custom Local Mail"}
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

def load_users():
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_id(username, password):
    return generate_user_id(username, password)

def is_supported_email(email):
    return any(email.endswith("@" + service["domain"]) for service in SUPPORTED_SERVICES.values())


#sessions
def load_sessions():
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]")
    with open(SESSIONS_FILE, 'r') as f:
        return json.load(f)

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)

def create_session(email):
    sessions = load_sessions()
    token = str(uuid.uuid4())
    sessions.append({"email": email, "token": token})
    save_sessions(sessions)
    return token

def get_email_from_token(token):
    sessions = load_sessions()
    for session in sessions:
        if session['token'] == token:
            return session['email']
    return None

def delete_session(token):
    sessions = load_sessions()
    sessions = [s for s in sessions if s['token'] != token]
    save_sessions(sessions)

# Setup inbox and sent folders
def setup_user_folders(email):
    user_folder = os.path.join(MAIL_ROOT, email)
    inbox_file = os.path.join(user_folder, 'inbox.json')
    sent_file = os.path.join(user_folder, 'sent.json')
    os.makedirs(user_folder, exist_ok=True)
    if not os.path.exists(inbox_file):
        with open(inbox_file, 'w') as f:
            json.dump([], f)
    if not os.path.exists(sent_file):
        with open(sent_file, 'w') as f:
            json.dump([], f)

def setup_user_inbox(email):
    # Keep for backward compatibility, but use setup_user_folders instead
    setup_user_folders(email)

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
    token = request.form.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No filename"}), 400

    filename = str(uuid.uuid4()) + "_" + file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return jsonify({"message": "File uploaded", "url": f"/attachments/{filename}"})

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

@app.route('/storage/<email>', methods=['GET'])
def storage(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404

    return jsonify(show_storage_status(email))

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
                mail['deleted_at'] = datetime.now().isoformat()
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

@app.route('/trash/<email>', methods=['GET'])
def view_trash(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    # Load inbox and sent JSON files
    inbox_path = f"mail_data/{email}/inbox.json"
    sent_path = f"mail_data/{email}/sent.json"
    if not os.path.exists(inbox_path):
        inbox_data = []
    else:
        with open(inbox_path, "r") as f:
            inbox_data = json.load(f)
    if not os.path.exists(sent_path):
        sent_data = []
    else:
        with open(sent_path, "r") as f:
            sent_data = json.load(f)

    now = datetime.now()
    deleted_emails = []

    # Filter deleted inbox mails
    updated_inbox = []
    for mail in inbox_data:
        if mail['message_status'] == 'deleted':
            deleted_emails.append(mail)
    for mail in sent_data:
        print("mail in sent_data: ",mail)
        if mail['message_status'] == 'deleted':
           deleted_emails.append(mail)

    return jsonify({"trash": deleted_emails}), 200


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
