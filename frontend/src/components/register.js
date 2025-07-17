import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import "./Login.css";
import { API_BASE_URL } from "../config";
import { FaUser, FaEnvelope, FaEye, FaEyeSlash, FaSpinner } from "react-icons/fa";

function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  const navigate = useNavigate();

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  // Email validation
  const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Password validation
  const isValidPassword = (password) => {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage("");

    // Client-side validation
    if (!username.trim()) {
      setMessage("Username is required");
      return;
    }

    if (username.length < 3) {
      setMessage("Username must be at least 3 characters long");
      return;
    }

    if (!email.trim()) {
      setMessage("Email is required");
      return;
    }

    if (!isValidEmail(email)) {
      setMessage("Please enter a valid email address");
      return;
    }

    if (!password) {
      setMessage("Password is required");
      return;
    }

    if (!isValidPassword(password)) {
      setMessage("Password must be at least 8 characters with uppercase, lowercase, and number");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    setIsRegistering(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        username: username.trim(),
        email: email.trim().toLowerCase(),
        password,
      });

      // Check if registration was successful
      if (response.data.message && response.data.message.includes('successfully')) {
        setMessage("✅ " + response.data.message);
        
        // Show success message for 2 seconds, then redirect to login
        setTimeout(() => {
          setMessage("🔄 Redirecting to login page...");
          
          // Clear form
          setUsername("");
          setEmail("");
          setPassword("");
          setConfirmPassword("");
          
          // Redirect to login page after another second
          setTimeout(() => {
            navigate("/login", { 
              state: { 
                registrationSuccess: true, 
                email: email.trim().toLowerCase(),
                message: "Registration successful! Please login with your credentials."
              } 
            });
          }, 1000);
        }, 2000);
        
      } else {
        // Handle unexpected response format
        setMessage("Registration completed, but please login manually");
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      }

    } catch (error) {
      console.error("Registration error:", error);
      
      let errorMessage = "Registration failed. Please try again.";
      
      if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.status === 409) {
        errorMessage = "This email is already registered. Please use a different email or try logging in.";
      } else if (error.response?.status === 400) {
        errorMessage = "Invalid input. Please check your details and try again.";
      } else if (error.response?.status === 500) {
        errorMessage = "Server error. Please try again later.";
      } else if (error.code === 'NETWORK_ERROR') {
        errorMessage = "Network error. Please check your connection and try again.";
      }
      
      setMessage("❌ " + errorMessage);
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>Create Your Account</h2>
      <p className="subtitle">Join us and start managing your emails efficiently</p>
      
      <form onSubmit={handleRegister}>
        <div className="input-wrapper">
          <input
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
            maxLength={50}
            disabled={isRegistering}
          />
          <FaUser className="input-icon" />
        </div>

        <div className="input-wrapper">
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            maxLength={100}
            disabled={isRegistering}
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
            minLength={8}
            maxLength={100}
            disabled={isRegistering}
          />
          <span
            onClick={togglePasswordVisibility}
            className="input-icon clickable"
            style={{ cursor: isRegistering ? 'not-allowed' : 'pointer' }}
          >
            {showPassword ? <FaEyeSlash /> : <FaEye />}
          </span>
        </div>

        <div className="input-wrapper">
          <input
            type={showConfirmPassword ? "text" : "password"}
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            maxLength={100}
            disabled={isRegistering}
          />
          <span
            onClick={toggleConfirmPasswordVisibility}
            className="input-icon clickable"
            style={{ cursor: isRegistering ? 'not-allowed' : 'pointer' }}
          >
            {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
          </span>
        </div>

        <button 
          type="submit" 
          disabled={isRegistering}
          className={isRegistering ? 'button-disabled' : ''}
        >
          {isRegistering ? (
            <>
              <FaSpinner style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
              Registering...
            </>
          ) : (
            'Register'
          )}
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('❌') ? 'error' : ''}`}>
          {message}
        </div>
      )}

      <div className="auth-options">
        <p>
          Already have an account?{" "}
          <Link to="/login" className="login-link">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Register;