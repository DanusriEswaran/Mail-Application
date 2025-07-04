import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { API_BASE_URL } from "../config";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("inbox");
  const [inbox, setInbox] = useState([]);
  const [sent, setSent] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [trash, setTrash] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [storageInfo, setStorageInfo] = useState(null);
  const [emailStats, setEmailStats] = useState(null);
  const [showCompose, setShowCompose] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [selectedEmails, setSelectedEmails] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  // Compose form states
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachment, setAttachment] = useState("");
  const [file, setFile] = useState(null);
  const [isDraft, setIsDraft] = useState(false);
  const [editingDraft, setEditingDraft] = useState(null);

  // Template states
  const [templateName, setTemplateName] = useState("");
  const [templateSubject, setTemplateSubject] = useState("");
  const [templateBody, setTemplateBody] = useState("");

  const username = localStorage.getItem("username");
  const email = localStorage.getItem("email");
  const token = localStorage.getItem("token");

  // Utility functions
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    const now = new Date();
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffTime = nowOnly - dateOnly;
    const diffDays = diffTime / (1000 * 60 * 60 * 24);

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return date.toLocaleDateString("en-US", { weekday: "short" });
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const getInitials = (email) => {
    return email.split("@")[0].charAt(0).toUpperCase();
  };

  // File upload handler
  const handleFileUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("token", token);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.url) {
        setAttachment(data.url);
      } else {
        alert("Failed to upload file");
      }
    } catch (err) {
      console.error("File upload error:", err);
      alert("Error uploading file");
    }
  };

  // Fetch functions
  const fetchInbox = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/inbox/${email}`);
      const data = await res.json();
      if (data.inbox) {
        const filteredInbox = data.inbox.filter(
          (mail) => mail.message_status !== "deleted"
        );
        setInbox(filteredInbox);
      }
    } catch (err) {
      console.error("Error fetching inbox:", err);
    }
  };

  const fetchSent = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sent/${email}`);
      const data = await res.json();
      if (data.sent) {
        const filteredSent = data.sent.filter(
          (mail) => mail.message_status !== "deleted"
        );
        setSent(filteredSent);
      }
    } catch (err) {
      console.error("Error fetching sent:", err);
    }
  };

  const fetchDrafts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/drafts/${email}`);
      const data = await res.json();
      if (data.drafts) {
        setDrafts(data.drafts);
      }
    } catch (err) {
      console.error("Error fetching drafts:", err);
    }
  };

  const fetchTrash = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/trash/${email}`);
      const data = await res.json();
      if (data.trash) {
        setTrash(data.trash);
      }
    } catch (error) {
      console.error("Failed to fetch trash emails:", error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/templates/${email}`);
      const data = await res.json();
      if (data.templates) {
        setTemplates(data.templates);
      }
    } catch (err) {
      console.error("Error fetching templates:", err);
    }
  };

  const fetchStorage = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/storage/${email}`);
      const data = await res.json();
      setStorageInfo(data);
    } catch (err) {
      console.error("Error fetching storage:", err);
    }
  };

  const fetchEmailStats = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/stats/${email}`);
      const data = await res.json();
      setEmailStats(data);
    } catch (err) {
      console.error("Error fetching email stats:", err);
    }
  };

  // Search functionality
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(`${API_BASE_URL}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          query: searchQuery,
          folder: activeTab === "sent" ? "sent" : "inbox"
        }),
      });
      const data = await res.json();
      if (data.results) {
        setSearchResults(data.results);
      }
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  // Email actions
  const handleMarkAsRead = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/mark_read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, mail, activeTab }),
      });
      if (res.ok) {
        refreshCurrentFolder();
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
        refreshCurrentFolder();
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
        refreshCurrentFolder();
        fetchTrash(); // Refresh trash count
      }
    } catch (err) {
      console.error("Error moving to trash:", err);
    }
  };

  const handlePermanentDelete = async (mail) => {
    if (window.confirm("Are you sure you want to permanently delete this email?")) {
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
  };

  const handleRestoreEmail = async (mail) => {
    try {
      const res = await fetch(`${API_BASE_URL}/restore_email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, mail }),
      });
      if (res.ok) {
        fetchTrash();
        refreshCurrentFolder();
      }
    } catch (err) {
      console.error("Error restoring email:", err);
    }
  };

  // Draft functions
  const handleSaveDraft = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/save_draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          to: recipient,
          subject,
          body,
          attachment,
        }),
      });
      if (res.ok) {
        alert("Draft saved successfully!");
        setShowCompose(false);
        resetComposeForm();
        fetchDrafts();
      }
    } catch (err) {
      console.error("Error saving draft:", err);
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
        fetchDrafts();
      }
    } catch (err) {
      console.error("Error deleting draft:", err);
    }
  };

  const handleEditDraft = (draft) => {
    setEditingDraft(draft);
    setRecipient(draft.to);
    setSubject(draft.subject);
    setBody(draft.body);
    setAttachment(draft.attachment || "");
    setShowCompose(true);
  };

  // Template functions
  const handleSaveTemplate = async () => {
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
        alert("Template saved successfully!");
        setShowTemplateModal(false);
        setTemplateName("");
        setTemplateSubject("");
        setTemplateBody("");
        fetchTemplates();
      }
    } catch (err) {
      console.error("Error saving template:", err);
    }
  };

  const handleUseTemplate = (template) => {
    setSubject(template.subject);
    setBody(template.body);
  };

  // Bulk operations
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
        setSelectedEmails([]);
        refreshCurrentFolder();
      }
    } catch (err) {
      console.error("Bulk action error:", err);
    }
  };

  // Send email
  const handleSend = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          to: recipient,
          subject,
          body,
          attachment,
        }),
      });

      const data = await res.json();
      if (data.message) {
        alert("Email sent successfully!");
        
        // If editing draft, delete it after sending
        if (editingDraft) {
          await handleDeleteDraft(editingDraft);
        }
        
        setShowCompose(false);
        resetComposeForm();
        fetchSent();
      } else {
        alert(data.error || "Failed to send email.");
      }
    } catch (err) {
      console.error("Send error:", err);
      alert("An error occurred while sending the email.");
    }
  };

  // Utility functions
  const resetComposeForm = () => {
    setRecipient("");
    setSubject("");
    setBody("");
    setAttachment("");
    setFile(null);
    setEditingDraft(null);
  };

  const refreshCurrentFolder = () => {
    switch (activeTab) {
      case "inbox":
        fetchInbox();
        break;
      case "sent":
        fetchSent();
        break;
      case "drafts":
        fetchDrafts();
        break;
      case "trash":
        fetchTrash();
        break;
      default:
        break;
    }
  };

  const handleLogout = () => {
    fetch(`${API_BASE_URL}/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    }).then(() => {
      localStorage.clear();
      window.location.href = "/";
    });
  };

  // Get current emails based on active tab
  const getCurrentEmails = () => {
    if (isSearching && searchResults.length > 0) {
      return searchResults;
    }
    
    switch (activeTab) {
      case "sent":
        return sent;
      case "drafts":
        return drafts;
      case "trash":
        return trash;
      default:
        return inbox;
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchInbox();
    fetchSent();
    fetchDrafts();
    fetchEmailStats();
  }, []);

  // Search effect
  useEffect(() => {
    if (searchQuery.trim()) {
      handleSearch();
    } else {
      setSearchResults([]);
      setIsSearching(false);
    }
  }, [searchQuery]);

  // Render functions
  const renderEmailList = () => {
    const currentEmails = getCurrentEmails();

    return (
      <div className="email-list">
        {/* Bulk actions toolbar */}
        {selectedEmails.length > 0 && (
          <div className="bulk-actions-toolbar">
            <span>{selectedEmails.length} selected</span>
            <button onClick={() => handleBulkAction("delete")}>Delete</button>
            <button onClick={() => handleBulkAction("mark_read")}>Mark Read</button>
            <button onClick={() => handleBulkAction("mark_unread")}>Mark Unread</button>
            <button onClick={() => setSelectedEmails([])}>Cancel</button>
          </div>
        )}

        {currentEmails.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              {activeTab === "trash" ? "🗑️" : activeTab === "drafts" ? "📝" : "📫"}
            </div>
            <h3>
              {activeTab === "sent"
                ? "No sent emails"
                : activeTab === "trash"
                ? "Trash is empty"
                : activeTab === "drafts"
                ? "No drafts"
                : isSearching
                ? "No search results"
                : "Your inbox is empty"}
            </h3>
          </div>
        ) : (
          currentEmails.map((mail, index) => (
            <div
              key={index}
              className={`email-item ${
                selectedEmail === index ? "selected" : ""
              } ${mail.message_status === "unread" ? "unread" : ""}`}
            >
              <div className="email-item-header">
                <input
                  type="checkbox"
                  checked={selectedEmails.includes(mail)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedEmails([...selectedEmails, mail]);
                    } else {
                      setSelectedEmails(selectedEmails.filter(m => m !== mail));
                    }
                  }}
                />
                <div className="sender-avatar">
                  {getInitials(activeTab === "sent" ? mail.to : mail.from)}
                </div>
                <div 
                  className="email-meta"
                  onClick={() => setSelectedEmail(selectedEmail === index ? null : index)}
                >
                  <div className="sender-name">
                    {activeTab === "sent"
                      ? `To: ${mail.to.split("@")[0]}`
                      : activeTab === "drafts"
                      ? `Draft to: ${mail.to || "..."}`
                      : mail.from.split("@")[0]}
                  </div>
                  <div className="email-subject">
                    {mail.subject || "No Subject"}
                  </div>
                  <div className="email-preview">
                    {mail.body.substring(0, 100)}...
                  </div>
                </div>
                <div className="email-actions">
                  <span className="email-date">
                    {formatDate(mail.date_of_send || mail.date_of_compose)}
                  </span>
                  
                  {/* Action buttons based on tab */}
                  {activeTab === "trash" ? (
                    <div className="trash-actions">
                      <button onClick={() => handleRestoreEmail(mail)}>↺</button>
                      <button onClick={() => handlePermanentDelete(mail)}>🗑️</button>
                    </div>
                  ) : activeTab === "drafts" ? (
                    <div className="draft-actions">
                      <button onClick={() => handleEditDraft(mail)}>✏️</button>
                      <button onClick={() => handleDeleteDraft(mail)}>🗑️</button>
                    </div>
                  ) : (
                    <div className="email-actions-dropdown">
                      <button onClick={() => handleMoveToTrash(mail)}>🗑️</button>
                      {mail.message_status === "unread" ? (
                        <button onClick={() => handleMarkAsRead(mail)}>👁️</button>
                      ) : (
                        <button onClick={() => handleMarkAsUnread(mail)}>👁️‍🗨️</button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {selectedEmail === index && (
                <div className="email-detail">
                  <div className="email-full-header">
                    <h4>{mail.subject || "No Subject"}</h4>
                    <div className="email-addresses">
                      <div><strong>From:</strong> {mail.from}</div>
                      <div><strong>To:</strong> {mail.to}</div>
                      <div>
                        <strong>Date:</strong>{" "}
                        {mail.date_of_send || mail.date_of_compose
                          ? new Date(mail.date_of_send || mail.date_of_compose).toLocaleString()
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
                          {mail.attachment.split("/").pop().split("_").slice(1).join("_")}
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    );
  };

  const renderStorageView = () => (
    <div className="storage-view">
      <div className="storage-card">
        <h2>Storage Usage</h2>
        {storageInfo && (
          <div className="storage-info">
            <div className="storage-bar">
              <div
                className="storage-fill"
                style={{ width: `${storageInfo.percentage}%` }}
              ></div>
            </div>
            <div className="storage-details">
              <span className="storage-used">{storageInfo.used_mb} MB used</span>
              <span className="storage-status">{storageInfo.status}</span>
            </div>
            <div className="storage-percentage">{storageInfo.percentage}%</div>
          </div>
        )}
      </div>
      
      {emailStats && (
        <div className="stats-card">
          <h2>Email Statistics</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">{emailStats.total_received}</div>
              <div className="stat-label">Received</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{emailStats.total_sent}</div>
              <div className="stat-label">Sent</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{emailStats.unread_count}</div>
              <div className="stat-label">Unread</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{emailStats.draft_count}</div>
              <div className="stat-label">Drafts</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{emailStats.deleted_count}</div>
              <div className="stat-label">Deleted</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTemplatesView = () => (
    <div className="templates-view">
      <div className="templates-header">
        <h2>Email Templates</h2>
        <button onClick={() => setShowTemplateModal(true)}>Create Template</button>
      </div>
      <div className="templates-grid">
        {templates.map((template, index) => (
          <div key={index} className="template-card">
            <h3>{template.name}</h3>
            <p>{template.subject}</p>
            <div className="template-actions">
              <button onClick={() => handleUseTemplate(template)}>Use</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="gmail-dashboard">
      {/* Header */}
      <header className="gmail-header">
        <div className="header-left">
          <div className="gmail-logo">
            <img src="logo.png" alt="Logo" className="logo-img" />
          </div>
          <div className="search-container">
            <input
              type="text"
              placeholder="Search mail"
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <div className="header-right">
          <div className="user-info">
            <div className="user-avatar">{getInitials(username)}</div>
            <span className="username">{username}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="gmail-body">
        {/* Sidebar */}
        <aside className="gmail-sidebar">
          <button
            className="compose-button"
            onClick={() => setShowCompose(true)}
          >
            <i className="fas fa-pen-nib compose-icon"></i>
            Compose
          </button>

          <nav className="sidebar-nav">
            <div
              className={`nav-item ${activeTab === "inbox" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("inbox");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchInbox();
              }}
            >
              <span className="nav-icon">📥</span>
              <span className="nav-text">Inbox</span>
              <span className="nav-count">{inbox.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "sent" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("sent");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchSent();
              }}
            >
              <span className="nav-icon">📤</span>
              <span className="nav-text">Sent</span>
              <span className="nav-count">{sent.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "drafts" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("drafts");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchDrafts();
              }}
            >
              <span className="nav-icon">📝</span>
              <span className="nav-text">Drafts</span>
              <span className="nav-count">{drafts.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "templates" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("templates");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchTemplates();
              }}
            >
              <span className="nav-icon">📋</span>
              <span className="nav-text">Templates</span>
              <span className="nav-count">{templates.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "trash" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("trash");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchTrash();
              }}
            >
              <span className="nav-icon">🗑️</span>
              <span className="nav-text">Trash</span>
              <span className="nav-count">{trash.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "storage" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("storage");
                setSelectedEmail(null);
                setSearchQuery("");
                fetchStorage();
                fetchEmailStats();
              }}
            >
              <span className="nav-icon">💾</span>
              <span className="nav-text">Storage</span>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="gmail-main">
          {activeTab === "storage" 
            ? renderStorageView()
            : activeTab === "templates"
            ? renderTemplatesView()
            : renderEmailList()}
        </main>
      </div>

      {/* Compose Modal */}
      {showCompose && (
        <div className="compose-overlay">
          <div className="compose-modal">
            <div className="compose-header">
              <h3>{editingDraft ? "Edit Draft" : "New Message"}</h3>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCompose(false);
                  resetComposeForm();
                }}
              >
                ✕
              </button>
            </div>

            <div className="compose-form">
              <div className="form-row">
                <label>To</label>
                <input
                  type="email"
                  placeholder="Recipients"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  required
                />
              </div>

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
                    <a href={attachment} target="_blank" rel="noopener noreferrer">
                      {attachment.split("/").pop()}
                    </a>
                  </div>
                )}
              </div>

              {/* Template selection */}
              <div className="template-selection">
                <label>Use Template:</label>
                <select onChange={(e) => {
                  const template = templates.find(t => t.name === e.target.value);
                  if (template) handleUseTemplate(template);
                }}>
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
                  className="send-btn" 
                  onClick={handleSend}
                  disabled={!recipient.trim()}
                >
                  Send
                </button>
                <button 
                  className="draft-btn" 
                  onClick={handleSaveDraft}
                >
                  Save Draft
                </button>
                <button 
                  className="discard-btn"
                  onClick={() => {
                    setShowCompose(false);
                    resetComposeForm();
                  }}
                >
                  Discard
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Template Modal */}
      {showTemplateModal && (
        <div className="template-overlay">
          <div className="template-modal">
            <div className="template-header">
              <h3>Create New Template</h3>
              <button
                className="close-btn"
                onClick={() => setShowTemplateModal(false)}
              >
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
                <button 
                  className="cancel-btn"
                  onClick={() => {
                    setShowTemplateModal(false);
                    setTemplateName("");
                    setTemplateSubject("");
                    setTemplateBody("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;