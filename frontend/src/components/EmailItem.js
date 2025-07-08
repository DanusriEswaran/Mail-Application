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
  };

  const getInitials = (email) => {
    return email ? email.split("@")[0].charAt(0).toUpperCase() : "U";
  };

  const handleEmailClick = async () => {
    // If email is being opened (not currently selected) and it's unread, mark it as read
    if (!isSelected && mail.message_status === "unread" && activeTab !== "drafts" && activeTab !== "trash") {
      setIsMarkingRead(true);
      await onMarkAsRead();
      setIsMarkingRead(false);
    }
    onSelect();
  };

  const getSenderDisplay = () => {
    if (activeTab === "sent" || activeTab === "scheduled") {
      return `To: ${mail.to?.split("@")[0] || "Unknown"}`;
    } else if (activeTab === "drafts") {
      return `Draft to: ${mail.to || "..."}`;
    } else {
      return mail.from?.split("@")[0] || "Unknown";
    }
  };

  const getAvatarEmail = () => {
    if (activeTab === "sent" || activeTab === "scheduled") {
      return mail.to;
    }
    return mail.from;
  };

  const renderActionButtons = () => {
    if (activeTab === "scheduled") {
      return (
        <div className="scheduled-actions">
          <button onClick={(e) => { e.stopPropagation(); onDeleteScheduled(); }}>
            🗑️
          </button>
        </div>
      );
    } else if (activeTab === "trash") {
      return (
        <div className="trash-actions">
          <button onClick={(e) => { e.stopPropagation(); onRestore(); }}>
            ↺
          </button>
          <button onClick={(e) => { e.stopPropagation(); onPermanentDelete(); }}>
            🗑️
          </button>
        </div>
      );
    } else if (activeTab === "drafts") {
      return (
        <div className="draft-actions">
          <button onClick={(e) => { e.stopPropagation(); onEditDraft(); }}>✏️</button>
          <button onClick={(e) => { e.stopPropagation(); onDeleteDraft(); }}>
            🗑️
          </button>
        </div>
      );
    } else {
      return (
        <div className="email-actions-dropdown">
          <button onClick={(e) => { e.stopPropagation(); onMoveToTrash(); }}>
            🗑️
          </button>
          {mail.message_status === "unread" ? (
            <button onClick={(e) => { e.stopPropagation(); onMarkAsRead(); }}>
              👁️
            </button>
          ) : (
            <button onClick={(e) => { e.stopPropagation(); onMarkAsUnread(); }}>
              👁️‍🗨️
            </button>
          )}
        </div>
      );
    }
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
            {mail.body.substring(0, 100)}...
          </div>
        </div>
        <div className="email-actions">
          <span className="email-date">
            {formatDate(
              mail.scheduled_date ||
                mail.date_of_send ||
                mail.date_of_compose
            )}
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
                <strong>From:</strong> {mail.from}
              </div>
              <div>
                <strong>To:</strong> {mail.to}
              </div>
              <div>
                <strong>
                  {activeTab === "scheduled" ? "Scheduled for:" : "Date:"}
                </strong>{" "}
                {mail.scheduled_date ||
                mail.date_of_send ||
                mail.date_of_compose
                  ? new Date(
                      mail.scheduled_date ||
                        mail.date_of_send ||
                        mail.date_of_compose
                    ).toLocaleString()
                  : "N/A"}
              </div>
            </div>
          </div>
          <div className="email-body">{mail.body}</div>
          {mail.attachment && (
            <div className="email-attachment">
              <div className="attachment-item">
                <span className="attachment-icon">📎</span>
                <a
                  href={`${API_BASE_URL}${mail.attachment}`}
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
                    .join("_")}
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