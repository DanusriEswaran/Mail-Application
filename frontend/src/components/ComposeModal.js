import React, { useState, useEffect } from "react";
import { API_BASE_URL } from "../config";
import { toast } from "react-toastify";
import RecipientInput from "./RecipientInput";
import ScheduleModal from "./ScheduleModal";

const ComposeModal = ({
  onClose,
  onSent,
  onDraftSaved,
  onScheduled,
  templates,
  editingDraft,
  token,
}) => {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachment, setAttachment] = useState("");
  const [file, setFile] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  // Load draft data if editing
  useEffect(() => {
    if (editingDraft) {
      setRecipient(editingDraft.to || "");
      setSubject(editingDraft.subject || "");
      setBody(editingDraft.body || "");
      setAttachment(editingDraft.attachment || "");
    }
  }, [editingDraft]);

  const resetForm = () => {
    setRecipient("");
    setSubject("");
    setBody("");
    setAttachment("");
    setFile(null);
  };

  const handleFileUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      // ✅ CORRECT ENDPOINT - Using /file/upload
      const res = await fetch(`${API_BASE_URL}/file/upload`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });
      const data = await res.json();
      if (data.url) {
        setAttachment(data.url);
        toast.success("File uploaded successfully!");
      } else {
        toast.error("Failed to upload file");
      }
    } catch (err) {
      console.error("File upload error:", err);
      toast.error("Error uploading file");
    }
  };

  const handleSend = async () => {
    if (!recipient.trim()) {
      toast.error("Please enter a recipient");
      return;
    }

    try {
      // ✅ CORRECT ENDPOINT - Using /mail/send
      const res = await fetch(`${API_BASE_URL}/mail/send`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          to: recipient,
          subject,
          body,
          attachment,
        }),
      });

      const data = await res.json();
      if (data.message) {
        toast.success("Email sent successfully!");

        // If editing draft, delete it after sending
        if (editingDraft) {
          await handleDeleteDraft(editingDraft);
        }

        onSent();
        onClose();
        resetForm();
      } else {
        toast.error(data.error || "Failed to send email.");
      }
    } catch (err) {
      console.error("Send error:", err);
      toast.error("An error occurred while sending the email.");
    }
  };

  const handleSaveDraft = async () => {
    try {
      // ✅ CORRECT ENDPOINT - Using /mail/save_draft
      const res = await fetch(`${API_BASE_URL}/mail/save_draft`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          to: recipient,
          subject,
          body,
          attachment,
        }),
      });
      
      if (res.ok) {
        toast.success("Draft saved successfully!");
        onDraftSaved();
        onClose();
        resetForm();
      } else {
        const errorData = await res.json();
        toast.error(errorData.error || "Failed to save draft");
      }
    } catch (err) {
      console.error("Error saving draft:", err);
      toast.error("Error saving draft");
    }
  };

  const handleDeleteDraft = async (draft) => {
    try {
      // ✅ CORRECT ENDPOINT - Using /mail/delete_draft
      const res = await fetch(`${API_BASE_URL}/mail/delete_draft`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ draft }),
      });
      return res.ok;
    } catch (err) {
      console.error("Error deleting draft:", err);
      return false;
    }
  };

  const handleUseTemplate = (template) => {
    setSubject(template.subject);
    setBody(template.body);
  };

  const handleScheduleEmail = async (scheduleDate, scheduleTime) => {
    if (!scheduleDate || !scheduleTime) {
      toast.error("Please select both date and time.");
      return;
    }

    if (!recipient.trim()) {
      toast.error("Please enter a recipient");
      return;
    }

    const scheduledDateTime = new Date(`${scheduleDate}T${scheduleTime}`);
    
    // Check if scheduled time is in the future
    if (scheduledDateTime <= new Date()) {
      toast.error("Scheduled time must be in the future");
      return;
    }
    
    try {
      // ✅ CORRECT ENDPOINT - Using /mail/schedule
      const res = await fetch(`${API_BASE_URL}/mail/schedule`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          to: recipient,
          subject,
          body,
          attachment,
          scheduleTime: scheduledDateTime.toISOString(),
        }),
      });

      const data = await res.json();
      if (data.message) {
        toast.success("Email scheduled successfully!");
        setShowScheduleModal(false);
        onScheduled();
        onClose();
        resetForm();
      } else {
        toast.error(data.error || "Failed to schedule email.");
      }
    } catch (err) {
      console.error("Schedule error:", err);
      toast.error("An error occurred while scheduling the email.");
    }
  };

  return (
    <div className="compose-overlay">
      <div className="compose-modal">
        <div className="compose-header">
          <h3>{editingDraft ? "Edit Draft" : "New Message"}</h3>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="compose-form">
          <RecipientInput
            recipient={recipient}
            onRecipientChange={setRecipient}
            token={token}
          />

          <div className="form-row">
            <label>Subject</label>
            <input
              type="text"
              placeholder="Subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>

          <div className="form-row message-row">
            <textarea
              placeholder="Compose your message..."
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows="12"
            />
          </div>

          <div className="attachment-section">
            <input
              type="file"
              id="file-input"
              style={{ display: "none" }}
              onChange={(e) => setFile(e.target.files[0])}
            />
            <label htmlFor="file-input" className="attach-btn">
              📎 Attach files
            </label>
            {file && (
              <div className="file-selected">
                <span>{file.name}</span>
                <button onClick={handleFileUpload} className="upload-btn">
                  Upload
                </button>
              </div>
            )}
            {attachment && (
              <div className="attachment-preview">
                <span className="attachment-icon">📎</span>
                <a
                  href={attachment}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {attachment.split("/").pop()}
                </a>
              </div>
            )}
          </div>

          <div className="template-selection">
            <label>Use Template:</label>
            <select
              onChange={(e) => {
                const template = templates.find(
                  (t) => t.name === e.target.value
                );
                if (template) handleUseTemplate(template);
              }}
            >
              <option value="">Select a template...</option>
              {templates.map((template, index) => (
                <option key={index} value={template.name}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          <div className="compose-actions">
            <button
              className="btn primary"
              onClick={handleSend}
              disabled={!recipient.trim()}
            >
              Send
            </button>

            <button
              className="btn secondary"
              onClick={() => setShowScheduleModal(true)}
              disabled={!recipient.trim()}
            >
              Schedule & Send
            </button>

            <button className="btn outline" onClick={handleSaveDraft}>
              Save Draft
            </button>

            <button className="btn muted" onClick={onClose}>
              Discard
            </button>
          </div>
        </div>
      </div>

      {showScheduleModal && (
        <ScheduleModal
          onClose={() => setShowScheduleModal(false)}
          onSchedule={handleScheduleEmail}
        />
      )}
    </div>
  );
};

export default ComposeModal;