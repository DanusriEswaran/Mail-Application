import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import MAIL_ROOT, DATA_DIR, UPLOAD_FOLDER, SESSIONS_FILE

# Import route blueprints
from routes.auth_routes import auth_bp
from routes.mail_routes import mail_bp
from routes.file_routes import file_bp
from routes.template_routes import template_bp
from routes.company_routes import company_bp
from routes.service_routes import service_bp  # Add this import

# Create and configure the app
app = Flask(__name__, static_folder=os.path.abspath('../frontend/build'), static_url_path='')

# Configure CORS to allow external applications
CORS(app, origins=['*'])  # For development - restrict in production

# Initialize application
def init_app():
    # Create necessary directories
    os.makedirs(MAIL_ROOT, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Initialize sessions file if it doesn't exist
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'w') as f:
            f.write("[]")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(mail_bp)
app.register_blueprint(file_bp)
app.register_blueprint(template_bp)
app.register_blueprint(company_bp)
app.register_blueprint(service_bp)  # Add this line

# Root routes for serving frontend
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Initialize the app
init_app()

# Run the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)