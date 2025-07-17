from flask import Blueprint, request, jsonify
from services.mail_service import MailService
from models.session import get_email_from_token
from models.user import load_users
from utils.storage import show_storage_status

mail_bp = Blueprint('mail', __name__)

@mail_bp.route('/inbox/<email>', methods=['GET'])
def view_inbox(email):
    inbox, error = MailService.get_inbox(email)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"inbox": inbox})

@mail_bp.route('/sent/<email>', methods=['GET'])
def view_sent(email):
    sent, error = MailService.get_sent(email)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"sent": sent})

@mail_bp.route('/drafts/<email>', methods=['GET'])
def view_drafts(email):
    drafts, error = MailService.get_drafts(email)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"drafts": drafts})

@mail_bp.route('/trash/<email>', methods=['GET'])
def view_trash(email):
    trash, error = MailService.get_trash(email)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"trash": trash})

@mail_bp.route('/storage/<email>', methods=['GET'])
def get_storage_info(email):
    users = load_users()
    if email not in users:
        return jsonify({"error": "User not found"}), 404
    
    try:
        storage_info = show_storage_status(email)
        
        # Convert to expected frontend format
        storage_data = {
            "used_mb": storage_info.get("used_mb", 0),
            "total_mb": storage_info.get("total_mb", 8),
            "percentage": storage_info.get("percentage", 0),
            "status": storage_info.get("status", "ok")
        }
        
        return jsonify(storage_data)
    except Exception as e:
        return jsonify({"error": "Failed to get storage info"}), 500

@mail_bp.route('/search', methods=['POST'])
def search_emails():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    query = data.get('query', '')
    folder = data.get('folder', 'inbox')
    
    results, error = MailService.search_emails(email, query, folder)
    if error:
        return jsonify({"error": error}), 500
    
    return jsonify({"results": results})

@mail_bp.route('/send', methods=['POST'])
def send_mail():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401
    
    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    attachment = data.get('attachment')
    
    success, error = MailService.send_mail(sender, recipient, subject, body, attachment)
    if not success:
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Email sent successfully"})

@mail_bp.route('/schedule', methods=['POST'])
def schedule_email():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401
    
    recipient = data.get('to')
    subject = data.get('subject')
    body = data.get('body')
    scheduled_time = data.get('scheduleTime')
    attachment = data.get('attachment')
    
    if not scheduled_time:
        return jsonify({"error": "Scheduled time is required"}), 400
    
    success, error = MailService.schedule_mail(sender, recipient, subject, body, scheduled_time, attachment)
    if not success:
        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Email scheduled successfully"})

@mail_bp.route('/scheduled', methods=['POST'])
def fetch_scheduled_emails():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401
    
    scheduled, error = MailService.get_scheduled(sender)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({"scheduled": scheduled})

@mail_bp.route('/bulk_action', methods=['POST'])
def bulk_action():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    action = data.get('action')
    emails = data.get('emails')
    folder = data.get('folder', 'inbox')
    
    updated_count, error = MailService.bulk_action(email, action, emails, folder)
    if error:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": f"Bulk action completed on {updated_count} emails"})

@mail_bp.route('/delete_mail', methods=['POST'])
def delete_mail():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    active = data.get('activeTab')
    
    if not target_fields:
        return jsonify({"error": "Missing mail data"}), 400
    
    success, error = MailService.delete_mail(email, target_fields, active)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({
        "message_status": "deleted",
        "message": "Deleted successfully"
    }), 200

@mail_bp.route('/mark_read', methods=['POST'])
def mark_read():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    active = data.get('activeTab', 'inbox')
    
    success, error = MailService.mark_read(email, target_fields, active)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Email marked as read"})

@mail_bp.route('/mark_unread', methods=['POST'])
def mark_unread():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    active = data.get('activeTab', 'inbox')
    
    success, error = MailService.mark_unread(email, target_fields, active)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Email marked as unread"})

@mail_bp.route('/save_draft', methods=['POST'])
def save_draft():
    data = request.json
    token = data.get('token')
    sender = get_email_from_token(token)
    if not sender:
        return jsonify({"error": "Invalid session"}), 401
    
    recipient = data.get('to', '')
    subject = data.get('subject', '')
    body = data.get('body', '')
    attachment = data.get('attachment')
    
    success, error = MailService.save_draft(sender, recipient, subject, body, attachment)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Draft saved successfully"})

@mail_bp.route('/delete_draft', methods=['POST'])
def delete_draft():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('draft')
    
    # This is actually a permanent delete, not just marking as deleted
    success, error = MailService.permanent_delete(email, target_fields, 'drafts')
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Draft deleted successfully"})

@mail_bp.route('/permanent_delete', methods=['POST'])
def permanent_delete():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    original_folder = target_fields.get('original_folder', 'inbox')
    
    success, error = MailService.permanent_delete(email, target_fields, original_folder)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Email permanently deleted"})

@mail_bp.route('/restore_email', methods=['POST'])
def restore_email():
    data = request.json
    token = data.get('token')
    email = get_email_from_token(token)
    if not email:
        return jsonify({"error": "Invalid session"}), 401
    
    target_fields = data.get('mail')
    original_folder = target_fields.get('original_folder', 'inbox')
    
    success, error = MailService.restore_email(email, target_fields, original_folder)
    if not success:
        return jsonify({"error": error}), 500
    
    return jsonify({"message": "Email restored successfully"})

@mail_bp.route('/stats/<email>', methods=['GET'])
def get_email_stats(email):
    stats, error = MailService.get_stats(email)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify(stats)

@mail_bp.route('/recipients', methods=['GET'])
def get_recipients():
    try:
        users = load_users()
        recipient_list = list(users.keys())
        return jsonify({"recipients": recipient_list})
    except Exception as e:
        return jsonify({"error": "Failed to fetch recipients"}), 500