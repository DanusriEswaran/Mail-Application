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
  const email = localStorage.getItem("email");
  const token = localStorage.getItem("token");
  const [file, setFile] = useState(null);
  const [trash, setTrash] = useState([]);

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
      const res = await fetch(`${API_BASE_URL}/inbox/${email}`);
      const data = await res.json();
      console.log("Inbox data: ", data);
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

  const fetchStorage = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/storage/${email}`);
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
    if (activeTab === "sent") return sent;
    if (activeTab === "trash") return trash;
    return inbox;
  };

  const filteredEmails = getCurrentEmails().filter(
    (email) =>
      email.from.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.to.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.body.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
    return email.split("@")[0].charAt(0).toUpperCase();
  };

  const handleMoveToTrash = async (mailToDelete, activeTab) => {
    try {
      const res = await fetch(`${API_BASE_URL}/delete_mail`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mail: mailToDelete, activeTab, token }),
      });
      const result = await res.json();
      console.log("result: ", result);

      if (result.message === "Deleted successfully") {
        // Remove the deleted mail from state
        const isSameMail = (mail1, mail2) =>
          mail1.from === mail2.from &&
          mail1.to === mail2.to &&
          mail1.subject === mail2.subject &&
          mail1.body === mail2.body &&
          mail1.date_of_send === mail2.date_of_send;

        if (activeTab === "inbox") {
          setInbox((prevInbox) =>
            prevInbox.filter((mail) => !isSameMail(mail, mailToDelete))
          );
        } else if (activeTab === "sent") {
          setSent((prevSent) =>
            prevSent.filter((mail) => !isSameMail(mail, mailToDelete))
          );
        }

        // Optional: Show confirmation (Toast/snackbar)
        console.log("Message deleted successfully");
      } else {
        console.error("Failed to delete email:", result);
      }
    } catch (err) {
      console.error("Error moving to trash:", err);
    }
  };

  const renderEmailList = () => {
    let currentEmails = [];

    // Choose which emails to render based on the active tab
    if (activeTab === "inbox") {
      currentEmails = inbox;
    } else if (activeTab === "sent") {
      currentEmails = sent;
    } else if (activeTab === "trash") {
      currentEmails = trash;
    }

    const filteredEmailsToRender = searchQuery
      ? currentEmails.filter(
          (mail) =>
            mail.subject?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            mail.body?.toLowerCase().includes(searchQuery.toLowerCase())
        )
      : currentEmails;

    return (
      <div className="email-list">
        {filteredEmailsToRender.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              {activeTab === "trash" ? "🗑️" : "📫"}
            </div>
            <h3>
              {activeTab === "sent"
                ? "No sent emails"
                : activeTab === "trash"
                ? "Trash is empty"
                : "Your inbox is empty"}
            </h3>
            <p>
              {activeTab === "sent"
                ? "No emails sent yet."
                : activeTab === "trash"
                ? "No emails in Trash."
                : "No emails found matching your search."}
            </p>
          </div>
        ) : (
          filteredEmailsToRender.map((mail, index) => (
            <div
              key={index}
              className={`email-item ${
                selectedEmail === index ? "selected" : ""
              }`}
              onClick={() =>
                setSelectedEmail(selectedEmail === index ? null : index)
              }
            >
              <div className="email-item-header">
                <div className="sender-avatar">
                  {getInitials(activeTab === "sent" ? mail.to : mail.from)}
                </div>
                <div className="email-meta">
                  <div className="sender-name">
                    {activeTab === "sent"
                      ? `To: ${mail.to.split("@")[0]}`
                      : mail.from.split("@")[0]}
                  </div>
                  <div className="email-subject">
                    {mail.subject || "No Subject"}
                  </div>
                  <div className="email-preview">
                    {mail.body.substring(0, 100)}...
                  </div>
                </div>
                <div className="email-date-wrapper">
                  <span className="email-date">
                    {formatDate(mail.date_of_send)}
                  </span>
                  {activeTab !== "trash" && (
                    <span
                      className="delete-icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMoveToTrash(mail, activeTab);
                      }}
                    >
                      🗑️
                    </span>
                  )}
                </div>
              </div>

              {selectedEmail === index && (
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
                        <strong>Date:</strong>{" "}
                        {mail.date_of_send
                          ? new Date(mail.date_of_send).toLocaleString()
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
          ))
        )}
      </div>
    );
  };

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

  const fetchTrash = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/trash/${email}`);
      const data = await res.json();
      if (data.trash) {
        console.log("data getting ? : ", data.trash);
        setTrash(data.trash);
      }
    } catch (error) {
      console.error("Failed to fetch trash emails:", error);
    }
  };

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
            <button className="search-btn">
              <i className="fas fa-search"></i>
            </button>
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
                fetchSent();
              }}
            >
              <span className="nav-icon">📤</span>
              <span className="nav-text">Sent</span>
              <span className="nav-count">{sent.length}</span>
            </div>

            <div
              className={`nav-item ${activeTab === "storage" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("storage");
                setSelectedEmail(null);
                fetchStorage();
              }}
            >
              <span className="nav-icon">💾</span>
              <span className="nav-text">Storage</span>
            </div>

            <div
              className={`nav-item ${activeTab === "trash" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("trash");
                setSelectedEmail(null);
                fetchTrash(); // Make sure this function exists
              }}
            >
              <span className="nav-icon">🗑️</span>
              <span className="nav-text">Trash</span>
              <span className="nav-count">{trash.length}</span>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="gmail-main">
          {activeTab === "storage" && storageInfo
            ? renderStorageView()
            : renderEmailList()}
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
            </div>

            <div className="compose-footer">
              <button className="send-btn" onClick={handleSend}>
                Send
              </button>
              <button
                className="cancel-btn"
                onClick={() => setShowCompose(false)}
              >
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
