import React, { useState } from "react";
import { API_BASE_URL } from "../config";

const RecipientInput = ({ recipient, onRecipientChange, token }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [knownRecipients, setKnownRecipients] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const fetchRecipients = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/recipients`);
      const data = await res.json();
      setKnownRecipients(data.recipients || []);
    } catch (err) {
      console.error("Error fetching recipients", err);
    }
  };

  const handleFocus = () => {
    fetchRecipients();
    setShowSuggestions(true);
  };

  const handleInputChange = (e) => {
    const input = e.target.value;
    onRecipientChange(input);

    if (input.trim()) {
      const filtered = knownRecipients.filter((email) =>
        email.toLowerCase().includes(input.toLowerCase())
      );
      setSuggestions(filtered);
    } else {
      setSuggestions([]);
    }
  };

  const handleSuggestionClick = (email) => {
    onRecipientChange(email);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => setShowSuggestions(false), 150);
  };

  return (
    <div className="form-row">
      <label>To</label>
      <div style={{ position: "relative", flex: 1 }}>
        <input
          type="email"
          placeholder="Recipients"
          value={recipient}
          onFocus={handleFocus}
          onChange={handleInputChange}
          onBlur={handleBlur}
          required
        />
        
        {showSuggestions && suggestions.length > 0 && (
          <ul className="suggestions-dropdown">
            {suggestions.map((email, idx) => (
              <li
                key={idx}
                onClick={() => handleSuggestionClick(email)}
              >
                {email}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default RecipientInput;