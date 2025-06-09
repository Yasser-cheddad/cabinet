import React from 'react';

// This component provides a bridge between the CDN-loaded MUI components
// and the imported components in our codebase
const MuiWrapper = ({ children }) => {
  // Make MUI components available globally in the app
  if (typeof window !== 'undefined') {
    window.MaterialUI = window.MaterialUI || {};
    
    // Ensure Material UI components are available
    if (window.MaterialUI) {
      React.MaterialUI = window.MaterialUI;
    }
  }
  
  return <>{children}</>;
};

export default MuiWrapper;
