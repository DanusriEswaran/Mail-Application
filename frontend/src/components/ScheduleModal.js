import React, { useState } from "react";

const ScheduleModal = ({ onClose, onSchedule }) => {
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");

  const handleSchedule = () => {
    onSchedule(scheduleDate, scheduleTime);
  };

  return (
    <div className="schedule-overlay">
      <div className="schedule-modal-card">
        <h4>📅 Schedule Email</h4>

        <div className="schedule-fields">
          <div className="date-picker">
            <label>Date</label>
            <input
              type="date"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
            />
          </div>
          <div className="time-picker">
            <label>Time</label>
            <input
              type="time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
            />
          </div>
        </div>

        <div className="schedule-actions">
          <button onClick={handleSchedule} className="btn primary">
            Schedule
          </button>
          <button onClick={onClose} className="btn muted">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScheduleModal;