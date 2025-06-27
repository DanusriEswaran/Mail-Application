from flask import Flask, request, jsonify, send_from_directory
import uuid, os, json, hashlib
from cryptography.fernet import Fernet
from pathlib import Path
from flask_cors import CORS
from datetime import datetime
from flask import send_file

UPLOAD_FOLDER = os.path.join("mail_data", "attachments")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Constants
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

def create_session(username):
    sessions = load_sessions()
    token = str(uuid.uuid4())
    sessions.append({"username": username, "token": token})
    save_sessions(sessions)
    return token

def get_username_from_token(token):
    sessions = load_sessions()
    for session in sessions:
        if session['token'] == token:
            return session['username']
    return None

def delete_session(token):
    sessions = load_sessions()
    sessions = [s for s in sessions if s['token'] != token]
    save_sessions(sessions)

# Setup inbox and sent folders
def setup_user_folders_by_id(user_id):
    user_folder = os.path.join(MAIL_ROOT, user_id)
    inbox_file = os.path.join(user_folder, 'inbox.json')
    sent_file = os.path.join(user_folder, 'sent.json')
    os.makedirs(user_folder, exist_ok=True)
    if not os.path.exists(inbox_file):
        with open(inbox_file, 'w') as f:
            json.dump([], f)
    if not os.path.exists(sent_file):
        with open(sent_file, 'w') as f:
            json.dump([], f)

def setup_user_inbox_by_id(user_id):
    # Keep for backward compatibility, but use setup_user_folders_by_id instead
    setup_user_folders_by_id(user_id)

def get_folder_size(path):
    return sum(os.path.getsize(os.path.join(dp, f))
               for dp, _, files in os.walk(path) for f in files)

def show_storage_status(user_id):
    folder = os.path.join(MAIL_ROOT, user_id)
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
    password = data.get('password')

    if not is_supported_email(username):
        return jsonify({"error": "Unsupported email domain"}), 400

    users = load_users()
    if username in users:
        return jsonify({"error": "User already exists"}), 400

    encrypted_password = cipher.encrypt(password.encode()).decode()
    users[username] = encrypted_password
    save_users(users)

    user_id = generate_user_id(username, password)
    setup_user_folders_by_id(user_id)

    token = create_session(username)
    return jsonify({
        "message": "User registered successfully",
        "user_id": user_id,
        "username": username,
        "token": token
    })

@app.route('/attachments/<filename>', methods=['GET'])
def get_attachment(filename):
    return send_from_directory(
        UPLOAD_FOLDER, 
        filename, 
        as_attachment=True, 
        download_name=filename.split("_", 1)[1]  # Extract original filename
    )



@app.route('/upload', methods=['POST'])
def upload_file():
    token = request.form.get('token')
    sender = get_username_from_token(token)
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


@app.route('/login', methods=['POST'])
def login():
    print("Arrive1")
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not is_supported_email(username):
        return jsonify({"error": "Unsupported email domain"}), 400

    users = load_users()
    if username in users:
        try:
            decrypted = cipher.decrypt(users[username].encode()).decode()
            if decrypted == password:
                user_id = generate_user_id(username, password)
                setup_user_folders_by_id(user_id)

                token = create_session(username)
                print("Arrives")
                return jsonify({
                    "message": "Login successful",
                    "username": username,
                    "user_id": user_id,
                    "token": token
                })
            else:
                return jsonify({"error": "Incorrect password"}), 401
        except:
            return jsonify({"error": "Decryption failed"}), 500
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/send', methods=['POST'])
def send_mail():
    data = request.json
    token = data.get('token')
    sender = get_username_from_token(token)

    if not sender:
        return jsonify({"error": "Invalid session"}), 401

    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    attachment = data.get('attachment', None)  # Optional field

    users = load_users()
    if sender not in users or recipient not in users:
        return jsonify({"error": "Sender or recipient not found"}), 404

    sender_password = cipher.decrypt(users[sender].encode()).decode()
    recipient_password = cipher.decrypt(users[recipient].encode()).decode()
    sender_id = generate_user_id(sender, sender_password)
    recipient_id = generate_user_id(recipient, recipient_password)

    if show_storage_status(sender_id)['status'] == 'full':
        return jsonify({"error": "Sender's inbox is full"}), 403
    if show_storage_status(recipient_id)['status'] == 'full':
        return jsonify({"error": "Recipient's inbox is full"}), 403

    setup_user_folders_by_id(recipient_id)
    setup_user_folders_by_id(sender_id)

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
    recipient_inbox_file = os.path.join(MAIL_ROOT, recipient_id, 'inbox.json')
    with open(recipient_inbox_file, 'r') as f:
        recipient_inbox = json.load(f)
    recipient_inbox.append(mail)
    with open(recipient_inbox_file, 'w') as f:
        json.dump(recipient_inbox, f, indent=2)

    # Add to sender's sent folder
    sender_sent_file = os.path.join(MAIL_ROOT, sender_id, 'sent.json')
    with open(sender_sent_file, 'r') as f:
        sender_sent = json.load(f)
    sender_sent.append(mail)
    with open(sender_sent_file, 'w') as f:
        json.dump(sender_sent, f, indent=2)

    return jsonify({"message": "Email sent successfully"})

@app.route('/inbox/<username>', methods=['GET'])
def view_inbox(username):
    users = load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404

    try:
        password = cipher.decrypt(users[username].encode()).decode()
        user_id = generate_user_id(username, password)
    except:
        return jsonify({"error": "Decryption failed"}), 500

    inbox_file = os.path.join(MAIL_ROOT, user_id, 'inbox.json')
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

@app.route('/sent/<username>', methods=['GET'])
def view_sent(username):
    users = load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404

    try:
        password = cipher.decrypt(users[username].encode()).decode()
        user_id = generate_user_id(username, password)
    except:
        return jsonify({"error": "Decryption failed"}), 500

    sent_file = os.path.join(MAIL_ROOT, user_id, 'sent.json')
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

@app.route('/storage/<username>', methods=['GET'])
def storage(username):
    users = load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404

    try:
        password = cipher.decrypt(users[username].encode()).decode()
        user_id = generate_user_id(username, password)
    except:
        return jsonify({"error": "Decryption failed"}), 500

    return jsonify(show_storage_status(user_id))

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