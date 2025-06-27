// src/components/Dashboard.js
import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { API_BASE_URL } from "../config";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("inbox");
  const [inbox, setInbox] = useState([]);
  const [sent, setSent] = useState([]);
  const [storageInfo, setStorageInfo] = useState(null);
  const [showCompose, setShowCompose] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachment, setAttachment] = useState("");

  const username = localStorage.getItem("username");
  const token = localStorage.getItem("token");
  const [file, setFile] = useState(null);

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

  const fetchInbox = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/inbox/${username}`);
      const data = await res.json();
      if (data.inbox) {
        setInbox(data.inbox);
      }
    } catch (err) {
      console.error("Error fetching inbox:", err);
    }
  };

  const fetchSent = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sent/${username}`);
      const data = await res.json();
      if (data.sent) {
        setSent(data.sent);
      }
    } catch (err) {
      console.error("Error fetching sent:", err);
    }
  };

  const fetchStorage = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/storage/${username}`);
      const data = await res.json();
      setStorageInfo(data);
    } catch (err) {
      console.error("Error fetching storage:", err);
    }
  };

  useEffect(() => {
    fetchInbox();
    fetchSent();
  }, []);

  const handleSend = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
        setShowCompose(false);
        setRecipient("");
        setSubject("");
        setBody("");
        setAttachment("");
        setFile(null);
        fetchInbox();
        fetchSent(); // Refresh sent folder after sending
      } else {
        alert(data.error || "Failed to send email.");
      }
    } catch (err) {
      console.error("Send error:", err);
      alert("An error occurred while sending the email.");
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

  const getCurrentEmails = () => {
    return activeTab === "sent" ? sent : inbox;
  };

  const filteredEmails = getCurrentEmails().filter(email => 
    email.from.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.to.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.body.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return "Today";
    if (diffDays === 2) return "Yesterday";
    if (diffDays <= 7) return date.toLocaleDateString('en-US', { weekday: 'short' });
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getInitials = (email) => {
    return email.split('@')[0].charAt(0).toUpperCase();
  };

  const renderEmailList = () => (
    <div className="email-list">
      {filteredEmails.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📫</div>
          <h3>{activeTab === "sent" ? "No sent emails" : "Your inbox is empty"}</h3>
          <p>{activeTab === "sent" ? "No emails sent yet." : "No emails found matching your search."}</p>
        </div>
      ) : (
        filteredEmails.map((mail, index) => (
          <div 
            key={index} 
            className={`email-item ${selectedEmail === index ? 'selected' : ''}`}
            onClick={() => setSelectedEmail(selectedEmail === index ? null : index)}
          >
            <div className="email-item-header">
              <div className="sender-avatar">
                {getInitials(activeTab === "sent" ? mail.to : mail.from)}
              </div>
              <div className="email-meta">
                <div className="sender-name">
                  {activeTab === "sent" 
                    ? `To: ${mail.to.split('@')[0]}` 
                    : mail.from.split('@')[0]
                  }
                </div>
                <div className="email-subject">{mail.subject || "No Subject"}</div>
                <div className="email-preview">{mail.body.substring(0, 100)}...</div>
              </div>
              <div className="email-date">{formatDate(mail.date_of_send)}</div>
              {mail.attachment && <div className="attachment-indicator">📎</div>}
            </div>
            
            {selectedEmail === index && (
              <div className="email-detail">
                <div className="email-full-header">
                  <h4>{mail.subject || "No Subject"}</h4>
                  <div className="email-addresses">
                    <div><strong>From:</strong> {mail.from}</div>
                    <div><strong>To:</strong> {mail.to}</div>
                    <div><strong>Date:</strong> {mail.date_of_send ? new Date(mail.date_of_send).toLocaleString() : "N/A"}</div>
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

  const renderStorageView = () => (
    <div className="storage-view">
      <div className="storage-card">
        <h2>Storage Usage</h2>
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
      </div>
    </div>
  );

  return (
    <div className="gmail-dashboard">
      {/* Header */}
      <header className="gmail-header">
        <div className="header-left">
          <div className="gmail-logo">
            <span className="logo-text">✉️ Mail</span>
          </div>
          <div className="search-container">
            <input
              type="text"
              placeholder="Search mail"
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button className="search-btn">🔍</button>
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
            <span className="compose-icon">✏️</span>
            Compose
          </button>
          
          <nav className="sidebar-nav">
            <div 
              className={`nav-item ${activeTab === 'inbox' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab("inbox");
                setSelectedEmail(null);
                fetchInbox();
              }}
            >
              <span className="nav-icon">📥</span>
              <span className="nav-text">Inbox</span>
              <span className="nav-count">{inbox.length}</span>
            </div>
            
            <div 
              className={`nav-item ${activeTab === 'sent' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab("sent");
                setSelectedEmail(null);
                fetchSent();
              }}
            >
              <span className="nav-icon">📤</span>
              <span className="nav-text">Sent</span>
              <span className="nav-count">{sent.length}</span>
            </div>
            
            <div 
              className={`nav-item ${activeTab === 'storage' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab("storage");
                setSelectedEmail(null);
                fetchStorage();
              }}
            >
              <span className="nav-icon">💾</span>
              <span className="nav-text">Storage</span>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="gmail-main">
          {activeTab === "storage" && storageInfo ? renderStorageView() : renderEmailList()}
        </main>
      </div>

      {/* Compose Modal */}
      {showCompose && (
        <div className="compose-overlay">
          <div className="compose-modal">
            <div className="compose-header">
              <h3>New Message</h3>
              <button 
                className="close-btn"
                onClick={() => setShowCompose(false)}
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
            </div>
            
            <div className="compose-footer">
              <button className="send-btn" onClick={handleSend}>
                Send
              </button>
              <button className="cancel-btn" onClick={() => setShowCompose(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;