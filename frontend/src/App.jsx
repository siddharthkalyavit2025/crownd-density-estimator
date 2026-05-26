import React, { useState } from 'react';
import './App.css';

function App() {
  // 1. React States for managing UI behavior
  const [isHeatmapView, setIsHeatmapView] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [estimatedCount, setEstimatedCount] = useState(0);
  const [densityStatus, setDensityStatus] = useState("No Input");
  const [inferenceTime, setInferenceTime] = useState("0 ms");

  // 2. Simulated function to handle a file upload
  const handleFileUpload = (e) => {
    setIsProcessing(true);
    setDensityStatus("Analyzing...");
    
    // Simulating ML model processing lag
    setTimeout(() => {
      setIsProcessing(false);
      setEstimatedCount(142); 
      setDensityStatus("High Density");
      setInferenceTime("42 ms");
      setIsHeatmapView(true); // Automatically switch to show off the heatmap
    }, 1500);
  };

  return (
    <div className="dashboard-container">
      
      {/* SIDEBAR COMPONENT */}
      <aside className="sidebar">
        <h2>👁️ CrowdVision AI</h2>
        <nav>
          <div className="menu-item active">Dashboard</div>
          <div className="menu-item">Camera Feeds</div>
          <div className="menu-item">Analytics History</div>
          <div className="menu-item">Model Settings</div>
        </nav>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">
        
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="main-title">Crowd Density Estimator</h1>
          </div>
          <div className="status-indicator">
            <span className="pulse-dot"></span>
            <span>Model Server: Operational</span>
          </div>
        </header>

        {/* METRICS ROW */}
        <section className="stats-grid">
          <div className="stat-card">
            <h3>Estimated Crowd Count</h3>
            <div className="stat-value" style={{ color: estimatedCount > 100 ? '#ef4444' : '#f8fafc' }}>
              {isProcessing ? "..." : estimatedCount}
            </div>
          </div>
          <div className="stat-card">
            <h3>Density Status</h3>
            <div className="stat-value" style={{ color: densityStatus === "High Density" ? '#f59e0b' : '#f8fafc' }}>
              {densityStatus}
            </div>
          </div>
          <div className="stat-card">
            <h3>Latency / Inference Time</h3>
            <div className="stat-value" style={{ color: '#10b981' }}>{isProcessing ? "Running..." : inferenceTime}</div>
          </div>
        </section>

        {/* WORKSPACE */}
        <section className="workspace">
          
          {/* Main Viewer Card */}
          <div className="viewer-card">
            <div className="view-toggle">
              <button 
                className={`btn ${!isHeatmapView ? 'primary' : ''}`} 
                onClick={() => setIsHeatmapView(false)}
              >
                Raw Feed
              </button>
              <button 
                className={`btn ${isHeatmapView ? 'primary' : ''}`} 
                onClick={() => setIsHeatmapView(true)}
              >
                Density Heatmap
              </button>
            </div>

            <div className="video-display">
              {isProcessing ? (
                <div style={{ textAlign: 'center' }}>
                  <div className="pulse-dot" style={{ margin: '0 auto 1rem', width: '20px', height: '20px' }}></div>
                  <p>Running Density Map Regression Model...</p>
                </div>
              ) : estimatedCount === 0 ? (
                <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                  <p>📁 Drag & drop CCTV image/video or click the Upload panel</p>
                </div>
              ) : (
                // When an image is analyzed, show either raw mock background or heatmap overlay
                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                  {/* Standard placeholder image to simulate a crowd */}
                  <img 
                    src="https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=800&q=80" 
                    alt="Crowd Feed" 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  {isHeatmapView && (
                    <div className="mock-heatmap">
                      <span className="heatmap-overlay-text">🔥 Density Regression Layer Active</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Control/Upload Side Panel */}
          <div className="controls-card">
            <h3>Model Input Panel</h3>
            <hr style={{ borderColor: '#334155', marginBottom: '1.5rem' }} />
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>
                Select Source Type:
              </label>
              <select style={{ width: '100%', padding: '0.5rem', background: '#0f172a', color: 'white', border: '1px solid #334155', borderRadius: '4px' }}>
                <option>Static Image (.png, .jpg)</option>
                <option>Live RTSP Video Stream</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#94a3b8' }}>
                Upload Mock Frame:
              </label>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileUpload} 
                style={{ display: 'none' }} 
                id="file-upload"
              />
              <label 
                htmlFor="file-upload" 
                className="btn primary" 
                style={{ display: 'block', textAlign: 'center', padding: '0.75rem' }}
              >
                {isProcessing ? "Processing..." : "Simulate ML Upload"}
              </label>
            </div>

            <div style={{ marginTop: '2rem', fontSize: '0.85rem', color: '#94a3b8', background: '#0f172a', padding: '1rem', borderRadius: '6px' }}>
              <strong>Teammates Integration Note:</strong><br/>
              The state logic is decoupled. To wire up your backend/ML Flask/FastAPI server, replace the simulated timer function inside <code>handleFileUpload</code> with an <code>axios.post()</code> call sending the image file and setting these exact state metrics with your model's JSON response output.
            </div>
          </div>

        </section>
      </main>
    </div>
  );
}

export default App;