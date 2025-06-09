import React from 'react';

function MinimalApp() {
  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '800px', 
      margin: '0 auto', 
      fontFamily: 'Inter, sans-serif',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    }}>
      <h1 style={{ color: '#2563eb', fontSize: '2rem', marginBottom: '1rem' }}>
        Medical Cabinet Application
      </h1>
      <p style={{ fontSize: '1.1rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
        This is a minimal test page to verify that React rendering is working correctly.
        If you can see this, your React application is rendering properly!
      </p>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button 
          style={{ 
            backgroundColor: '#2563eb', 
            color: 'white', 
            padding: '0.75rem 1.5rem',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
          onClick={() => alert('You clicked the Test button!')}
        >
          Test Button
        </button>
        <button 
          style={{ 
            backgroundColor: '#10b981', 
            color: 'white', 
            padding: '0.75rem 1.5rem',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
          onClick={() => console.log('Console log test')}
        >
          Log to Console
        </button>
      </div>
    </div>
  );
}

export default MinimalApp;
