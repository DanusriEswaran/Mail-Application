import React, { useState } from "react";
import { API_BASE_URL } from "../config";
import { toast } from "react-toastify";

const TemplateModal = ({ onClose, onSaved, token }) => {
  const [templateName, setTemplateName] = useState("");
  const [templateSubject, setTemplateSubject] = useState("");
  const [templateBody, setTemplateBody] = useState("");

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      toast.error("Please enter a template name");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/save_template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          name: templateName,
          subject: templateSubject,
          body: templateBody,
        }),
      });
      
      if (res.ok) {
        toast.success("Template saved successfully!");
        onSaved();
      } else {
        toast.error("Failed to save template");
      }
    } catch (err) {
      console.error("Error saving template:", err);
      toast.error("Error saving template");
    }
  };

  const handleCancel = () => {
    setTemplateName("");
    setTemplateSubject("");
    setTemplateBody("");
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="template-modal">
        <div className="template-header">
          <h3>Create New Template</h3>
          <button className="close-btn" onClick={handleCancel}>
            ✕
          </button>
        </div>

        <div className="template-form">
          <div className="form-row">
            <label>Template Name</label>
            <input
              type="text"
              placeholder="Template name"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <label>Subject</label>
            <input
              type="text"
              placeholder="Subject"
              value={templateSubject}
              onChange={(e) => setTemplateSubject(e.target.value)}
            />
          </div>

          <div className="form-row">
            <label>Template Body</label>
            <textarea
              placeholder="Template content..."
              value={templateBody}
              onChange={(e) => setTemplateBody(e.target.value)}
              rows="8"
            />
          </div>

          <div className="template-actions">
            <button
              className="save-template-btn"
              onClick={handleSaveTemplate}
              disabled={!templateName.trim()}
            >
              Save Template
            </button>
            <br />
            <button className="cancel-btn" onClick={handleCancel}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateModal;