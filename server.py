from flask import Flask, request, jsonify, send_from_directory
import os, json, hashlib
from cryptography.fernet import Fernet

# Constants
KEY_FILE = "secret.key"
MAIL_ROOT = 'mail_users'
MAX_STORAGE = 8 * 1024 * 1024  # 8 MB

app = Flask(__name__)

# Setup encryption
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'wb') as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, 'rb') as f:
    key = f.read()

cipher = Fernet(key)

# Users
USERS = {
    'user1': cipher.encrypt(b'qwerty').decode(),
    'user2': cipher.encrypt(b'123456').decode()
}

def generate_user_id(username, password):
    return hashlib.sha256((username + password).encode()).hexdigest()[:16]

USER_IDS = {
    'user1': generate_user_id('user1', 'qwerty'),
    'user2': generate_user_id('user2', '123456')
}

# Setup inbox
def setup_user_inbox_by_id(user_id):
    user_folder = os.path.join(MAIL_ROOT, user_id)
    inbox_file = os.path.join(user_folder, 'inbox.json')
    os.makedirs(user_folder, exist_ok=True)
    if not os.path.exists(inbox_file):
        with open(inbox_file, 'w') as f:
            json.dump([], f)

def get_folder_size(path):
    return sum(os.path.getsize(os.path.join(dp, f))
               for dp, _, files in os.walk(path) for f in files)

def show_storage_status(username):
    user_id = USER_IDS[username]
    folder = os.path.join(MAIL_ROOT, user_id)
    used = get_folder_size(folder)
    percent = (used / MAX_STORAGE) * 100
    return {
        "used_mb": round(used / (1024 * 1024), 2),
        "percentage": round(percent, 2),
        "status": "full" if percent >= 100 else "warning" if percent >= 90 else "ok"
    }

@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

# Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in USERS:
        try:
            decrypted = cipher.decrypt(USERS[username].encode()).decode()
            if decrypted == password:
                user_id = USER_IDS[username]
                setup_user_inbox_by_id(user_id)
                return jsonify({
                    "message": "Login successful",
                    "username": username,
                    "user_id": user_id
                })
            else:
                return jsonify({"error": "Incorrect password"}), 401
        except:
            return jsonify({"error": "Decryption failed"}), 500
    return jsonify({"error": "User not found"}), 404

@app.route('/send', methods=['POST'])
def send_mail():
    data = request.json
    sender = data.get('from')
    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')

    if sender not in USERS or recipient not in USERS:
        return jsonify({"error": "Sender or recipient not found"}), 404

    if show_storage_status(sender)['status'] == 'full':
        return jsonify({"error": "Sender's inbox is full"}), 403
    if show_storage_status(recipient)['status'] == 'full':
        return jsonify({"error": "Recipient's inbox is full"}), 403

    recipient_id = USER_IDS[recipient]
    setup_user_inbox_by_id(recipient_id)

    mail = {
        'from': sender,
        'to': recipient,
        'subject': subject,
        'body': cipher.encrypt(body.encode()).decode()
    }

    inbox_file = os.path.join(MAIL_ROOT, recipient_id, 'inbox.json')
    with open(inbox_file, 'r') as f:
        inbox = json.load(f)
    inbox.append(mail)
    with open(inbox_file, 'w') as f:
        json.dump(inbox, f, indent=2)

    return jsonify({"message": "Email sent successfully"})

@app.route('/inbox/<username>', methods=['GET'])
def view_inbox(username):
    if username not in USERS:
        return jsonify({"error": "User not found"}), 404

    user_id = USER_IDS[username]
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
            "body": decrypted_body
        })

    return jsonify({"inbox": decrypted_inbox})

@app.route('/storage/<username>', methods=['GET'])
def storage(username):
    if username not in USERS:
        return jsonify({"error": "User not found"}), 404
    return jsonify(show_storage_status(username))

# Run the server on your hotspot IP
if __name__ == '__main__':
    if not os.path.exists(MAIL_ROOT):
        os.makedirs(MAIL_ROOT)
    app.run(host='0.0.0.0', port=5000, debug=True)
