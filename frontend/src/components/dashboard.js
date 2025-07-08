import React, { useEffect, useState } from "react";
import "./Dashboard.css";
import { API_BASE_URL } from "../config";
import { toast } from "react-toastify";

// Import all components
import Header from "./Header";
import Sidebar from "./Sidebar";
import EmailList from "./EmailList";
import StorageView from "./StorageView";
import TemplatesView from "./TemplatesView";
import ComposeModal from "./ComposeModal";
import TemplateModal from "./TemplateModal";
import ConfirmModal from "./ConfirmModal";

const Dashboard = () => {
  // All state variables
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
  const [scheduled, setScheduled] = useState([]);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState("");
  const [onConfirm, setOnConfirm] = useState(null);
  const [editingDraft, setEditingDraft] = useState(null);

  const username = localStorage.getItem("username");
  const email = localStorage.getItem("email");
  const token = localStorage.getItem("token");

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

  const fetchScheduled = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/scheduled`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      });

      const data = await res.json();

      if (Array.isArray(data.scheduled)) {
        const filteredScheduled = data.scheduled.filter(
          (mail) => mail.message_status !== "deleted"
        );
        setScheduled(filteredScheduled);
      } else {
        console.error("Unexpected response:", data);
        toast.error("Failed to load scheduled emails.");
      }
    } catch (err) {
      console.error("Error fetching scheduled emails:", err);
      toast.error("An error occurred while fetching scheduled emails.");
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
          folder: activeTab === "sent" ? "sent" : "inbox",
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

  // Get current emails based on active tab
  const getCurrentEmails = () => {
    switch (activeTab) {
      case "inbox":
        return inbox;
      case "sent":
        return sent;
      case "trash":
        return trash;
      case "drafts":
        return drafts;
      case "scheduled":
        return scheduled;
      default:
        return [];
    }
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
      case "scheduled":
        fetchScheduled();
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

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedEmail(null);
    setSearchQuery("");
    
    switch (tab) {
      case "inbox":
        fetchInbox();
        break;
      case "sent":
        fetchSent();
        break;
      case "drafts":
        fetchDrafts();
        break;
      case "templates":
        fetchTemplates();
        break;
      case "scheduled":
        fetchScheduled();
        break;
      case "trash":
        fetchTrash();
        break;
      case "storage":
        fetchStorage();
        fetchEmailStats();
        break;
      default:
        break;
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

  const renderMainContent = () => {
    switch (activeTab) {
      case "storage":
        return <StorageView storageInfo={storageInfo} emailStats={emailStats} />;
      case "templates":
        return (
          <TemplatesView
            templates={templates}
            onCreateTemplate={() => setShowTemplateModal(true)}
            onUseTemplate={(template) => {
              // This would be passed to compose modal
              setShowCompose(true);
            }}
          />
        );
      default:
        return (
          <EmailList
            emails={getCurrentEmails()}
            activeTab={activeTab}
            selectedEmail={selectedEmail}
            selectedEmails={selectedEmails}
            searchQuery={searchQuery}
            isSearching={isSearching}
            onSelectEmail={setSelectedEmail}
            onSelectEmails={setSelectedEmails}
            onRefresh={refreshCurrentFolder}
            onEditDraft={setEditingDraft}
            onShowCompose={setShowCompose}
            onShowConfirm={(message, callback) => {
              setConfirmMessage(message);
              setOnConfirm(() => callback);
              setShowConfirmModal(true);
            }}
            token={token}
            fetchTrash={fetchTrash}
            fetchInbox={fetchInbox}
            fetchSent={fetchSent}
          />
        );
    }
  };

  return (
    <div className="gmail-dashboard">
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        username={username}
        onLogout={handleLogout}
      />

      <div className="gmail-body">
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onCompose={() => setShowCompose(true)}
          counts={{
            inbox: inbox.length,
            sent: sent.length,
            drafts: drafts.length,
            templates: templates.length,
            scheduled: scheduled.length,
            trash: trash.length,
          }}
        />

        <main className="gmail-main">
          {renderMainContent()}
        </main>
      </div>

      {showCompose && (
        <ComposeModal
          onClose={() => {
            setShowCompose(false);
            setEditingDraft(null);
          }}
          onSent={() => {
            fetchSent();
            refreshCurrentFolder();
          }}
          onDraftSaved={() => {
            fetchDrafts();
          }}
          onScheduled={() => {
            fetchScheduled();
          }}
          templates={templates}
          editingDraft={editingDraft}
          token={token}
        />
      )}

      {showTemplateModal && (
        <TemplateModal
          onClose={() => setShowTemplateModal(false)}
          onSaved={() => {
            fetchTemplates();
            setShowTemplateModal(false);
          }}
          token={token}
        />
      )}

      {showConfirmModal && (
        <ConfirmModal
          message={confirmMessage}
          onConfirm={() => {
            if (onConfirm) onConfirm();
            setShowConfirmModal(false);
          }}
          onCancel={() => setShowConfirmModal(false)}
        />
      )}
    </div>
  );
};

export default Dashboard;