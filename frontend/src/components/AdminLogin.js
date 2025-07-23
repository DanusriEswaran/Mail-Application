import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import "./Login.css"; // Use the unified CSS
import { API_BASE_URL } from "../config";
import { FaEnvelope, FaEye, FaEyeSlash } from "react-icons/fa";

function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    
    // Validate the email is an admin email
    if (!email.startsWith('admin@')) {
      setMessage("Please enter a valid admin email address");
      return;
    }
    
    try {
      // ✅ CORRECT ENDPOINT - Using /auth/login (same endpoint for both user and admin)
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password,
      });
      
      setMessage(`Welcome ${res.data.username}`);

      // Store admin information
      localStorage.setItem("admin_token", res.data.token);
      localStorage.setItem("admin_email", res.data.email);
      localStorage.setItem("admin_username", res.data.username);
      localStorage.setItem("admin_id", res.data.user_id);
      localStorage.setItem("is_admin", "true");

      // Extract domain from email (admin@domain.com)
      const domain = email.split('@')[1];
      localStorage.setItem("admin_domain", domain);

      navigate("/admin/dashboard");
    } catch (error) {
      if (error.response) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Login failed. Please check your credentials.");
      }
    }
  };

  return (
    <div className="auth-container">
      <h2>Admin Login</h2>
      <p className="subtitle">Login to manage your company domain</p>
      
      <form onSubmit={handleLogin}>
        <div className="input-wrapper">
          <input
            type="email"
            placeholder="Admin Email (admin@yourdomain.com)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <FaEnvelope className="input-icon" />
        </div>

        <div className="input-wrapper">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <span
            onClick={togglePasswordVisibility}
            className="input-icon clickable"
          >
            {showPassword ? <FaEyeSlash /> : <FaEye />}
          </span>
        </div>

        <button type="submit">Admin Login</button>
      </form>

      {message && <p className="message">{message}</p>}

      <div className="auth-options">
        <p>
          Need to register a company?{" "}
          <Link to="/admin/register" className="register-link">
            Register Company
          </Link>
        </p>
        
        <div className="back-to-main">
          <Link to="/login" className="main-link">
            Back to Main Login
          </Link>
        </div>
      </div>
    </div>
  );
}

export default AdminLogin;