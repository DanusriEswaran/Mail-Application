import React from "react";

const TemplatesView = ({ templates, onCreateTemplate, onUseTemplate }) => {
  return (
    <div className="templates-view">
      <div className="templates-header">
        <h2>Email Templates</h2>
        <button onClick={onCreateTemplate}>Create Template</button>
      </div>
      <div className="templates-grid">
        {templates.map((template, index) => (
          <div key={index} className="template-card">
            <h3>{template.name}</h3>
            <p>{template.subject}</p>
            <div className="template-actions">
              <button onClick={() => onUseTemplate(template)}>Use</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TemplatesView;