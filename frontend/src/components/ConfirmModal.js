import React from "react";

const ConfirmModal = ({ message, onConfirm, onCancel }) => {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        backgroundColor: "rgba(0, 0, 0, 0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "10px",
          padding: "24px",
          width: "300px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
          textAlign: "center",
        }}
      >
        <p style={{ fontSize: "16px", marginBottom: "20px" }}>
          {message}
        </p>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <button
            onClick={onConfirm}
            style={{
              backgroundColor: "#1976d2",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              padding: "8px 16px",
              cursor: "pointer",
            }}
          >
            Yes
          </button>
          <button
            onClick={onCancel}
            style={{
              backgroundColor: "#e0e0e0",
              color: "#333",
              border: "none",
              borderRadius: "4px",
              padding: "8px 16px",
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;