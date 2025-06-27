import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Login.css";
import { API_BASE_URL } from "../config";
function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        username,
        password,
      });

      setMessage(response.data.message);
      if (response.data.token) {
  // Save login info like in login.js
  localStorage.setItem("token", response.data.token);
  localStorage.setItem("username", response.data.username);
  localStorage.setItem("user_id", response.data.user_id);

  navigate("/dashboard");
}

      setUsername("");
      setPassword("");
    } catch (error) {
      if (error.response) {
        setMessage(error.response.data.error);
      } else {
        setMessage("Registration failed.");
      }
    }
  };

  const goToLogin = () => {
    navigate("/login");
  };

  return (
    <div className="auth-container">
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <div>
          <label>User mail: </label>
          <br />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <br />
        <div>
          <label>Password: </label>
          <br />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <br />
        <button type="submit">Register</button>
      </form>

      <button
        type="button"
        className="secondary-button center-button"
        onClick={goToLogin}
      >
        Go to Login
      </button>

      {message && <p style={{ marginTop: "10px" }}>{message}</p>}
    </div>
  );
}

export default Register;
