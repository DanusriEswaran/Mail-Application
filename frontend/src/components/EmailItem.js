import React, { useState } from "react";
import { API_BASE_URL } from "../config";

const EmailItem = ({
  mail,
  index,
  activeTab,
  isSelected,
  isChecked,
  onSelect,
  onCheck,
  onMarkAsRead,
  onMarkAsUnread,
  onMoveToTrash,
  onPermanentDelete,
  onRestore,
  onEditDraft,
  onDeleteDraft,
  onDeleteScheduled,
}) => {
  const [isMarkingRead, setIsMarkingRead] = useState(false);

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const dateOnly = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate()
      );
      const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const diffTime = nowOnly - dateOnly;
      const diffDays = diffTime / (1000 * 60 * 60 * 24);

      if (diffDays === 0) return "Today";
      if (diffDays === 1) return "Yesterday";
      if (diffDays < 7)
        return date.toLocaleDateString("en-US", { weekday: "short" });
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch (error) {
      console.error("Error formatting date:", error);
      return "Invalid Date";
    }
  };

  const getInitials = (email) => {
    if (!email) return "U";
    try {
      return email.split("@")[0].charAt(0).toUpperCase();
    } catch (error) {
      return "U";
    }
  };

  const handleEmailClick = async () => {
    // If email is being opened (not currently selected) and it's unread, mark it as read
    if (!isSelected && mail.message_status === "unread" && activeTab !== "drafts" && activeTab !== "trash") {
      setIsMarkingRead(true);
      try {
        await onMarkAsRead();
      } catch (error) {
        console.error("Error marking as read:", error);
      } finally {
        setIsMarkingRead(false);
      }
    }
    onSelect();
  };

  const getSenderDisplay = () => {
    try {
      if (activeTab === "sent" || activeTab === "scheduled") {
        return `To: ${mail.to?.split("@")[0] || "Unknown"}`;
      } else if (activeTab === "drafts") {
        return `Draft to: ${mail.to || "..."}`;
      } else {
        return mail.from?.split("@")[0] || "Unknown";
      }
    } catch (error) {
      return "Unknown";
    }
  };

  const getAvatarEmail = () => {
    if (activeTab === "sent" || activeTab === "scheduled") {
      return mail.to;
    }
    return mail.from;
  };

  const getEmailPreview = () => {
    if (!mail.body) return "No content";
    
    try {
      // Remove HTML tags if present and limit to 100 characters
      const cleanBody = mail.body.replace(/<[^>]*>/g, '').trim();
      return cleanBody.length > 100 ? cleanBody.substring(0, 100) + "..." : cleanBody;
    } catch (error) {
      return "Error reading content";
    }
  };

  const renderActionButtons = () => {
    if (activeTab === "scheduled") {
      return (
        <div className="scheduled-actions">
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onDeleteScheduled(); 
            }}
            title="Delete scheduled email"
          >
            🗑️
          </button>
        </div>
      );
    } else if (activeTab === "trash") {
      return (
        <div className="trash-actions">
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onRestore(); 
            }}
            title="Restore email"
          >
            ↺
          </button>
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onPermanentDelete(); 
            }}
            title="Delete permanently"
          >
            🗑️
          </button>
        </div>
      );
    } else if (activeTab === "drafts") {
      return (
        <div className="draft-actions">
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onEditDraft(); 
            }}
            title="Edit draft"
          >
            ✏️
          </button>
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onDeleteDraft(); 
            }}
            title="Delete draft"
          >
            🗑️
          </button>
        </div>
      );
    } else {
      return (
        <div className="email-actions-dropdown">
          <button 
            onClick={(e) => { 
              e.stopPropagation(); 
              onMoveToTrash(); 
            }}
            title="Move to trash"
          >
            🗑️
          </button>
          {mail.message_status === "unread" ? (
            <button 
              onClick={(e) => { 
                e.stopPropagation(); 
                onMarkAsRead(); 
              }}
              title="Mark as read"
            >
              👁️
            </button>
          ) : (
            <button 
              onClick={(e) => { 
                e.stopPropagation(); 
                onMarkAsUnread(); 
              }}
              title="Mark as unread"
            >
              👁️‍🗨️
            </button>
          )}
        </div>
      );
    }
  };

  const getEmailDate = () => {
    return mail.scheduled_date || mail.date_of_send || mail.date_of_compose;
  };

  return (
    <div
      className={`email-item ${
        isSelected ? "selected" : ""
      } ${mail.message_status === "unread" ? "unread" : ""} ${
        isMarkingRead ? "marking-read" : ""
      }`}
    >
      <div className="email-item-header">
        <input
          type="checkbox"
          checked={isChecked}
          onChange={(e) => onCheck(e.target.checked)}
          onClick={(e) => e.stopPropagation()}
        />
        <div className="sender-avatar">
          {getInitials(getAvatarEmail())}
        </div>
        <div className="email-meta" onClick={handleEmailClick}>
          <div className="sender-name">{getSenderDisplay()}</div>
          <div className="email-subject">
            {mail.subject || "No Subject"}
          </div>
          <div className="email-preview">
            {getEmailPreview()}
          </div>
        </div>
        <div className="email-actions">
          <span className="email-date">
            {formatDate(getEmailDate())}
          </span>
          {renderActionButtons()}
        </div>
      </div>

      {isSelected && (
        <div className="email-detail">
          <div className="email-full-header">
            <h4>{mail.subject || "No Subject"}</h4>
            <div className="email-addresses">
              <div>
                <strong>From:</strong> {mail.from || "Unknown"}
              </div>
              <div>
                <strong>To:</strong> {mail.to || "Unknown"}
              </div>
              <div>
                <strong>
                  {activeTab === "scheduled" ? "Scheduled for:" : "Date:"}
                </strong>{" "}
                {getEmailDate()
                  ? new Date(getEmailDate()).toLocaleString()
                  : "N/A"}
              </div>
            </div>
          </div>
          <div className="email-body">{mail.body || "No content"}</div>
          {mail.attachment && (
            <div className="email-attachment">
              <div className="attachment-item">
                <span className="attachment-icon">📎</span>
                <a
                  href={mail.attachment.startsWith('http') ? mail.attachment : `${API_BASE_URL}${mail.attachment}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                  className="attachment-link"
                >
                  {mail.attachment
                    .split("/")
                    .pop()
                    .split("_")
                    .slice(1)
                    .join("_") || "Attachment"}
                </a>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EmailItem;