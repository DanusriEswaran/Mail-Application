import React from "react";

const Header = ({ searchQuery, onSearchChange, username, onLogout }) => {
  const getInitials = (name) => {
    return name ? name.charAt(0).toUpperCase() : "U";
  };

  return (
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
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
      </div>
      <div className="header-right">
        <div className="user-info">
          <div className="user-avatar">{getInitials(username)}</div>
          <span className="username">{username}</span>
        </div>
        <button className="logout-btn" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
};

export default Header;