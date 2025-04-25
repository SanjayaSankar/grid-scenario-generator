import React from 'react';
import { Alert, Button } from 'react-bootstrap';
// Try to import XCircle, but have a fallback if module not found
let XCircle;
try {
  // Dynamic import to handle potential missing module
  const icons = require('react-bootstrap-icons');
  XCircle = icons.XCircle;
} catch (error) {
  // Create a simple fallback component if the import fails
  XCircle = ({ size, className }) => (
    <span className={className} style={{ fontSize: size + 'px', fontWeight: 'bold' }}>✕</span>
  );
}

const ErrorMessage = ({ error, onRetry, onBack }) => {
  // Check if error is a server error with status code
  const isServerError = error && error.includes('status code');
  const statusCode = isServerError ? error.match(/status code (\d+)/)?.[1] : null;
  
  return (
    <Alert variant="danger" className="mb-4 error-alert">
      <div className="d-flex align-items-center mb-2">
        <XCircle size={24} className="text-danger me-2" />
        <h4 className="m-0">Error</h4>
      </div>
      
      <p className="mb-3">{error}</p>
      
      {isServerError && (
        <div className="server-error-info mb-3">
          <p className="mb-1">This appears to be a server error (Status: {statusCode}).</p>
          <p className="mb-0">The server might be temporarily unavailable or experiencing issues processing your request.</p>
        </div>
      )}
      
      <div className="d-flex gap-2">
        {onRetry && (
          <Button variant="outline-light" size="sm" onClick={onRetry}>
            Try Again
          </Button>
        )}
        
        {onBack && (
          <Button variant="outline-light" size="sm" onClick={onBack}>
            Back to Scenarios
          </Button>
        )}
      </div>
    </Alert>
  );
};

export default ErrorMessage; 