import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, Link, useLocation } from "react-router-dom";
import "./Login.css";
import { API_BASE_URL } from "../config";
import {
  FaEnvelope,
  FaEye,
  FaEyeSlash,
  FaBuilding,
  FaSpinner,
} from "react-icons/fa";
import { toast } from "react-toastify";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  // Check if user came from registration
  useEffect(() => {
    if (location.state?.registrationSuccess) {
      toast.success(location.state.message);

      // Pre-fill email if available
      if (location.state.email) {
        setEmail(location.state.email);
      }

      // Clear the success message after 5 seconds
      setTimeout(() => {
        setMessage("");
      }, 5000);
    }
  }, [location.state]);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage("");

    // Client-side validation
    if (!email.trim()) {
      setMessage("Email is required");
      return;
    }

    if (!password) {
      setMessage("Password is required");
      return;
    }

    setIsLoggingIn(true);

    try {
      // CORRECT ENDPOINT - Using /auth/login
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        email: email.trim().toLowerCase(),
        password,
      });

      // Store user data in localStorage
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("email", res.data.email);
      localStorage.setItem("username", res.data.username);
      localStorage.setItem("user_id", res.data.user_id);

      toast.success(`Welcome ${res.data.username}!`);

      // Show welcome message briefly, then redirect
      setTimeout(() => {
        navigate("/dashboard");
      }, 1000);
    } catch (error) {
      console.error("Login error:", error);

      let errorMessage = "Login failed. Please try again.";

      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.status === 401) {
        errorMessage =
          "Invalid email or password. Please check your credentials.";
      } else if (error.response?.status === 404) {
        errorMessage =
          "Account not found. Please check your email or register a new account.";
      } else if (error.response?.status === 429) {
        errorMessage = "Too many login attempts. Please try again later.";
      } else if (error.response?.status === 500) {
        errorMessage = "Server error. Please try again later.";
      } else if (error.code === "NETWORK_ERROR") {
        errorMessage =
          "Network error. Please check your connection and try again.";
      }

      toast.error(errorMessage);
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>Login</h2>
      <p className="subtitle">Welcome back! Please login to your account</p>

      <form onSubmit={handleLogin}>
        <div className="input-wrapper">
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoggingIn}
          />
          <FaEnvelope className="input-icon" />
        </div>

        <div className="input-wrapper">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoggingIn}
          />
          <span
            onClick={togglePasswordVisibility}
            className="input-icon clickable"
            style={{ cursor: isLoggingIn ? "not-allowed" : "pointer" }}
          >
            {showPassword ? <FaEyeSlash /> : <FaEye />}
          </span>
        </div>

        <button
          type="submit"
          disabled={isLoggingIn}
          className={isLoggingIn ? "button-disabled" : ""}
        >
          {isLoggingIn ? (
            <>
              <FaSpinner
                style={{
                  marginRight: "8px",
                  animation: "spin 1s linear infinite",
                }}
              />
              Logging in...
            </>
          ) : (
            "Login"
          )}
        </button>
      </form>

      <div className="auth-options">
        <p>
          Don't have an account?{" "}
          <Link to="/register" className="register-link">
            Register
          </Link>
        </p>

        <div className="separator">
          <span>OR</span>
        </div>

        <div className="company-option">
          <Link to="/admin/register" className="company-link">
            <FaBuilding className="company-icon" />
            Register a Company Domain
          </Link>
        </div>

        <p className="admin-login-text">
          Already have a company?{" "}
          <Link to="/admin/login" className="admin-link">
            Admin Login
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
