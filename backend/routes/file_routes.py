import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory
from models.session import get_email_from_token
from config import UPLOAD_FOLDER

file_bp = Blueprint('file', __name__)

@file_bp.route('/attachments/<filename>', methods=['GET'])
def get_attachment(filename):
    return send_from_directory(
        UPLOAD_FOLDER, 
        filename, 
        as_attachment=True, 
        download_name=filename.split("_", 1)[1]  
    )

@file_bp.route('/upload', methods=['POST'])
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

@file_bp.route('/uploads/<email>/<filename>')
def serve_uploaded_file(email, filename):
    try:
        upload_folder = os.path.join('uploads', email)
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404