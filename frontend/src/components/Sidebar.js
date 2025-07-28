import React from "react";

const Sidebar = ({ activeTab, onTabChange, onCompose, counts }) => {
  const navItems = [
    { id: "inbox", icon: "fas fa-inbox", text: "Inbox", count: counts.inbox },
    { id: "sent", icon: "fas fa-paper-plane", text: "Sent", count: counts.sent },
    { id: "drafts", icon: "fas fa-file-alt", text: "Drafts", count: counts.drafts },
    { id: "templates", icon: "fas fa-clone", text: "Templates", count: counts.templates },
    { id: "scheduled", icon: "fas fa-clock", text: "Scheduled", count: counts.scheduled },
    { id: "trash", icon: "fas fa-trash", text: "Trash", count: counts.trash },
    { id: "storage", icon: "fas fa-database", text: "Storage", count: null },
  ];

  return (
    <aside className="gmail-sidebar">
      <button className="compose-button" onClick={onCompose}>
        <i className="fas fa-pen-nib compose-icon"></i>
        Compose
      </button>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => onTabChange(item.id)}
          >
            <span className="nav-icon">
              <i className={item.icon}></i>
            </span>
            <span className="nav-text">{item.text}</span>
            {item.count !== null && (
              <span className="nav-count">{item.count}</span>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;