// src/components/Dashboard.js
import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { API_BASE_URL } from "../config";
const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("inbox");
  const [inbox, setInbox] = useState([]);
  const [storageInfo, setStorageInfo] = useState(null);
  const [showCompose, setShowCompose] = useState(false);

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const username = localStorage.getItem("username");
  const token = localStorage.getItem("token");

  // ✅ Fetch inbox
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

  // ✅ Fetch storage
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
    fetchInbox(); // Show inbox by default
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
        }),
      });

      const data = await res.json();
      if (data.message) {
        alert("Email sent successfully!");
        setShowCompose(false);
        setRecipient("");
        setSubject("");
        setBody("");
        fetchInbox();
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

  const renderContent = () => {
    if (activeTab === "storage" && storageInfo) {
      return (
        <div className="main-content">
          <h2>Storage</h2>
          <p>Used: {storageInfo.used_gb} GB</p>
          <p>Total: {storageInfo.total_gb} GB</p>
          <p>Status: {storageInfo.status}</p>
        </div>
      );
    }

    return (
      <div className="main-content">
        <h2>Inbox</h2>
        {inbox.length === 0 ? (
          <p>No emails yet.</p>
        ) : (
          inbox.map((mail, index) => (
            <div key={index} className="mail-card">
              <p>
                <strong>From:</strong> {mail.from}
              </p>
              <p>
                <strong>To:</strong> {mail.to}
              </p>
              <p>
                <strong>Subject:</strong> {mail.subject}
              </p>
              <p>{mail.body}</p>
              <hr />
            </div>
          ))
        )}
      </div>
    );
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="user-controls">
          <div className="user-email">{username}</div>
          <button className="compose-btn" onClick={() => setShowCompose(true)}>
            Compose
          </button>
        </div>
        <ul className="menu">
          <li
            onClick={() => {
              setActiveTab("inbox");
              fetchInbox();
            }}
          >
            Inbox
          </li>
          <li
            onClick={() => {
              setActiveTab("storage");
              fetchStorage();
            }}
          >
            Storage
          </li>
        </ul>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </aside>

      {renderContent()}

      {showCompose && (
        <div className="compose-popup">
          <div className="compose-card">
            <h3>Compose Mail</h3>
            <input
              type="email"
              placeholder="To"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            <textarea
              rows="8"
              placeholder="Message"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="compose-actions">
              <button onClick={handleSend}>Send</button>
              <button onClick={() => setShowCompose(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
