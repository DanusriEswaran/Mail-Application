import React from "react";
import { API_BASE_URL } from "../config";
import { toast } from "react-toastify";
import EmailItem from "./EmailItem";
import BulkActionsToolbar from "./BulkActionsToolbar";

const EmailList = ({
  emails,
  activeTab,
  selectedEmail,
  selectedEmails,
  searchQuery,
  isSearching,
  onSelectEmail,
  onSelectEmails,
  onRefresh,
  onEditDraft,
  onShowCompose,
  onShowConfirm,
  token,
  fetchTrash,
  fetchInbox,
  fetchSent,
}) => {
  // Email actions
  const handleMarkAsRead = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/mark_read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, mail, activeTab }),
      });
      if (res.ok) {
        // Use a small delay to batch multiple updates if needed
        setTimeout(() => {
          onRefresh();
        }, 100);
      }
    } catch (err) {
      console.error("Error marking as read:", err);
    }
  };

  const handleMarkAsUnread = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/mark_unread`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, mail, activeTab }),
      });
      if (res.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error("Error marking as unread:", err);
    }
  };

  const handleMoveToTrash = async (mailToDelete) => {
    try {
      const res = await fetch(`${API_BASE_URL}/delete_mail`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mail: mailToDelete, activeTab, token }),
      });
      const result = await res.json();

      if (result.message === "Deleted successfully") {
        onRefresh();
        fetchTrash();
      }
    } catch (err) {
      console.error("Error moving to trash:", err);
    }
  };

  const handlePermanentDelete = (mail) => {
    onShowConfirm(
      "Are you sure you want to permanently delete this email?",
      async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/permanent_delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token, mail }),
          });
          if (res.ok) {
            fetchTrash();
          }
        } catch (err) {
          console.error("Error permanently deleting:", err);
        }
      }
    );
  };

  const handleRestoreEmail = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/restore_email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, mail }),
      });
      if (res.ok) {
        fetchTrash(); // Update trash count
        onRefresh(); // Update current folder
        
        // Update the folder where the email was restored to
        // Check if it's an inbox or sent email and refresh accordingly
        if (fetchInbox) fetchInbox(); // Refresh inbox
        if (fetchSent) fetchSent(); // Refresh sent
      }
    } catch (err) {
      console.error("Error restoring email:", err);
    }
  };

  const handleDeleteDraft = async (draft) => {
    try {
      const res = await fetch(`${API_BASE_URL}/delete_draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, draft }),
      });
      if (res.ok) {
        onRefresh();
      }
    } catch (err) {
      console.error("Error deleting draft:", err);
    }
  };

  const handleDeleteScheduled = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/delete_mail`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          activeTab: "scheduled",
          mail: {
            from: mail.from,
            to: mail.to,
            subject: mail.subject,
            date_of_send: mail.date_of_send,
          },
        }),
      });

      const result = await res.json();

      if (result.message === "Deleted successfully") {
        onRefresh();
      } else {
        toast.error(result.error || "Failed to delete scheduled email.");
      }
    } catch (err) {
      console.error(err);
      toast.error("An error occurred while deleting scheduled email.");
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedEmails.length === 0) return;

    try {
      const res = await fetch(`${API_BASE_URL}/bulk_action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          action,
          emails: selectedEmails,
          folder: activeTab,
        }),
      });
      if (res.ok) {
        onSelectEmails([]);
        onRefresh();
        
        // If bulk restoring from trash, refresh inbox and sent
        if (action === "restore" && activeTab === "trash") {
          if (fetchInbox) fetchInbox();
          if (fetchSent) fetchSent();
        }
      }
    } catch (err) {
      console.error("Bulk action error:", err);
    }
  };

  const handleEmailSelect = (mail, isChecked) => {
    const match = (m) =>
      m.subject === mail.subject &&
      m.to === mail.to &&
      m.from === mail.from &&
      (m.date_of_send === mail.date_of_send ||
        m.scheduled_date === mail.scheduled_date);

    if (isChecked) {
      onSelectEmails([...selectedEmails, mail]);
    } else {
      onSelectEmails(selectedEmails.filter((m) => !match(m)));
    }
  };

  const isEmailSelected = (mail) => {
    return selectedEmails.some(
      (m) =>
        m.subject === mail.subject &&
        m.to === mail.to &&
        m.from === mail.from &&
        (m.date_of_send === mail.date_of_send ||
          m.scheduled_date === mail.scheduled_date)
    );
  };

  const getEmptyStateConfig = () => {
    const configs = {
      sent: { icon: "📫", text: "No sent emails" },
      trash: { icon: "🗑️", text: "Trash is empty" },
      drafts: { icon: "📝", text: "No drafts" },
      scheduled: { icon: "📋", text: "No scheduled emails" },
      default: { icon: "📫", text: isSearching ? "No search results" : "Your inbox is empty" }
    };
    
    return configs[activeTab] || configs.default;
  };

  const emptyState = getEmptyStateConfig();

  return (
    <div className="email-list">
      {selectedEmails.length > 0 && (
        <BulkActionsToolbar
          selectedCount={selectedEmails.length}
          onBulkAction={handleBulkAction}
          onClearSelection={() => onSelectEmails([])}
          activeTab={activeTab}
        />
      )}

      {emails.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">{emptyState.icon}</div>
          <h3>{emptyState.text}</h3>
        </div>
      ) : (
        emails.map((mail, index) => (
          <EmailItem
            key={index}
            mail={mail}
            index={index}
            activeTab={activeTab}
            isSelected={selectedEmail === index}
            isChecked={isEmailSelected(mail)}
            onSelect={() => onSelectEmail(selectedEmail === index ? null : index)}
            onCheck={(isChecked) => handleEmailSelect(mail, isChecked)}
            onMarkAsRead={() => handleMarkAsRead(mail)}
            onMarkAsUnread={() => handleMarkAsUnread(mail)}
            onMoveToTrash={() => handleMoveToTrash(mail)}
            onPermanentDelete={() => handlePermanentDelete(mail)}
            onRestore={() => handleRestoreEmail(mail)}
            onEditDraft={() => {
              onEditDraft(mail);
              onShowCompose(true);
            }}
            onDeleteDraft={() => handleDeleteDraft(mail)}
            onDeleteScheduled={() => handleDeleteScheduled(mail)}
          />
        ))
      )}
    </div>
  );
};

export default EmailList;