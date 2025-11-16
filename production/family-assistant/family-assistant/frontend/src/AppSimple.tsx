import React from 'react';

function AppSimple() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Family Assistant Dashboard</h1>
      <p style={{ color: 'green', fontSize: '18px' }}>✅ Frontend is working!</p>
      <p>This is a simplified test version to verify React is loading correctly.</p>
      <div style={{
        backgroundColor: '#f0f0f0',
        padding: '15px',
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h2>System Status:</h2>
        <ul>
          <li>✅ React Application Loaded</li>
          <li>✅ CSS Styling Working</li>
          <li>✅ JavaScript Executing</li>
        </ul>
      </div>
    </div>
  );
}

export default AppSimple;