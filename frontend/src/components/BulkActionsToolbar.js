import React from "react";

const BulkActionsToolbar = ({ selectedCount, onBulkAction, onClearSelection, activeTab }) => {
  return (
    <div className="bulk-actions-toolbar">
      <span>{selectedCount} selected</span>
      
      {activeTab === "trash" ? (
        <button onClick={() => onBulkAction("restore")}>Restore</button>
      ) : (
        <button onClick={() => onBulkAction("delete")}>Delete</button>
      )}
      
      {activeTab !== "trash" && (
        <>
          <button onClick={() => onBulkAction("mark_read")}>Mark Read</button>
          <button onClick={() => onBulkAction("mark_unread")}>Mark Unread</button>
        </>
      )}
      
      <button onClick={onClearSelection}>Cancel</button>
    </div>
  );
};

export default BulkActionsToolbar;