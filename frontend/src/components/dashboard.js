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
  const [attachment, setAttachment] = useState(""); // New attachment field

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
      setAttachment(data.url); // Set attachment to uploaded file URL
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
          attachment, // Include attachment
        }),
      });

      const data = await res.json();
      if (data.message) {
        alert("Email sent successfully!");
        setShowCompose(false);
        setRecipient("");
        setSubject("");
        setBody("");
        setAttachment(""); // Reset attachment field
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
          <p>Used: {storageInfo.used_mb} MB</p>
          <p>Used (%): {storageInfo.percentage}%</p>
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
              <p><strong>From:</strong> {mail.from}</p>
              <p><strong>To:</strong> {mail.to}</p>
              <p><strong>Subject:</strong> {mail.subject}</p>
              <p><strong>Body:</strong> {mail.body}</p>
              {mail.attachment && (
  <p>
    <strong>Attachment:</strong>{" "}
    <a
      href={`${API_BASE_URL}${mail.attachment}`}
      target="_blank"
      rel="noopener noreferrer"
      download
    >
      {mail.attachment.split("/").pop()}
    </a>
  </p>
)}

              {/* <p><strong>Composed:</strong> {mail.date_of_compose ? new Date(mail.date_of_compose).toLocaleString() : "N/A"}</p> */}
              <p><strong>Received On:</strong> {mail.date_of_send ? new Date(mail.date_of_send).toLocaleString() : "N/A"}</p>
              {/* <p><strong>Status:</strong> {mail.message_status || "N/A"}</p> */}
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
            <div className="attachment-upload">
  <label htmlFor="file-upload" style={{ cursor: "pointer" }}>
    📎 Attach File
  </label>
  <input
    id="file-upload"
    type="file"
    style={{ display: "none" }}
    onChange={(e) => {
      setFile(e.target.files[0]);
    }}
  />
  <button onClick={handleFileUpload} disabled={!file}>
    Upload
  </button>
  {attachment && (
    <p>
      <strong>Attachment:</strong>{" "}
      <a href={attachment} target="_blank" rel="noopener noreferrer">
        {attachment.split("/").pop()}
      </a>
    </p>
  )}
</div>

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
