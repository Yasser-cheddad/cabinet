import React from 'react';

function TestPage() {
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ color: 'blue', fontSize: '2rem' }}>Test Page</h1>
      <p>This is a simple test page to verify that React rendering is working correctly.</p>
      <button 
        style={{ 
          backgroundColor: 'green', 
          color: 'white', 
          padding: '0.5rem 1rem',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
        onClick={() => alert('Button clicked!')}
      >
        Click Me
      </button>
    </div>
  );
}

export default TestPage;
