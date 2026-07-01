import React, { useState } from 'react';
import './App.css';

function App() {
  // Application State Management
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // Pipeline ML Model States
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isHeatmapView, setIsHeatmapView] = useState(false);
  const [estimatedCount, setEstimatedCount] = useState(0);
  const [densityStatus, setDensityStatus] = useState("No Input");
  const [inferenceTime, setInferenceTime] = useState("0 ms");

  // Camera node tracking mock lists
  const [cameraNodes, setCameraNodes] = useState([
    { id: "Feed_01", location: "North Entrance Gate", status: "Active", count: 142 },
    { id: "Feed_02", location: "South Ticket Plaza", status: "Active", count: 85 },
    { id: "Feed_03", location: "East Main Concourse", status: "Offline", count: 0 },
  ]);

  // System Config States
  const [alertThreshold, setAlertThreshold] = useState(100);
  const [gpuAcceleration, setGpuAcceleration] = useState(true);

  // Simulation handler matching regression deep analytic pipeline logic
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Set local mock blob URL source destination path 
    setUploadedImage(URL.createObjectURL(file));
    setIsProcessing(true);
    setDensityStatus("Analyzing...");
    
    // Simulating ML model processing lag
    setTimeout(() => {
      setIsProcessing(false);
      setEstimatedCount(142); 
      setDensityStatus("High Density");
      setInferenceTime("42 ms");
      setIsHeatmapView(true); // Automatically switch on the heatmap layer overlay
    }, 1200);
  };

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className={`dashboard-container ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">👁️</span>
          <h2>CrowdVision AI</h2>
        </div>
        
        <nav className="sidebar-menu">
          <div 
            className={`menu-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Analytics Dashboard
          </div>
          <div 
            className={`menu-item ${activeTab === 'feeds' ? 'active' : ''}`}
            onClick={() => setActiveTab('feeds')}
          >
            🎥 Node Camera Feeds
          </div>
          <div 
            className={`menu-item ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            📈 Spatial History
          </div>
          <div 
            className={`menu-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Configuration
          </div>
        </nav>
        
        <div className="sidebar-footer">
          <p>System Version: 2.5-Local</p>
        </div>
      </aside>

      {/* MAIN CONTENT RUNTIME SURFACE */}
      <main className="main-content">
        
        {/* GLOBAL HEADER HEADER BAR */}
        <header className="header">
          <div>
            <h1 className="main-title">Crowd Density Estimator</h1>
            <p className="main-subtitle">Automated spatial density metrics and machine learning deep regression analytics.</p>
          </div>
          
          <div className="header-controls">
            <button className="theme-toggle-btn" onClick={toggleTheme}>
              {isDarkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
            </button>
            <div className="status-indicator">
              <span className="pulse-dot"></span>
              <span>Model Server: <strong style={{color: '#10b981'}}>Connected</strong></span>
            </div>
          </div>
        </header>

        {/* DYNAMIC TAB INTERFACES CONTENT SCREEN SWITCHES */}
        
        {activeTab === 'dashboard' && (
          <div className="tab-view-container animate-fade">
            {/* EXPANDED METRICS DASHBOARD SECTION */}
            <section className="stats-grid">
              <div className="stat-card">
                <div className="card-meta">LIVE TELEMETRY</div>
                <h3>Estimated Crowd Count</h3>
                <div className="stat-value" style={{ color: estimatedCount > alertThreshold ? '#ef4444' : 'inherit' }}>
                  {isProcessing ? "..." : estimatedCount}
                </div>
                <div className="card-subtext">Active target frame heads detected</div>
              </div>
              
              <div className="stat-card">
                <div className="card-meta">THRESHOLD STATUS</div>
                <h3>Density Status</h3>
                <div className="stat-value" style={{ color: densityStatus === "High Density" ? '#f59e0b' : 'inherit' }}>
                  {densityStatus}
                </div>
                <div className="card-subtext">Current capacity alarm classification</div>
              </div>

              <div className="stat-card">
                <div className="card-meta">PERFORMANCE LATENCY</div>
                <h3>Inference Exec Speed</h3>
                <div className="stat-value" style={{ color: '#10b981' }}>{isProcessing ? "Inference..." : inferenceTime}</div>
                <div className="card-subtext">Backend GPU processing execution duration</div>
              </div>
            </section>

            {/* WORKSPACE LAYOUT CONTAINER */}
            <section className="workspace">
              
              {/* Main Media Feed Area */}
              <div className="viewer-card">
                <div className="viewer-toolbar">
                  <div className="view-toggle">
                    <button 
                      className={`btn ${!isHeatmapView ? 'primary' : ''}`} 
                      onClick={() => setIsHeatmapView(false)}
                      disabled={!uploadedImage || isProcessing}
                    >
                      Raw Video Stream
                    </button>
                    <button 
                      className={`btn ${isHeatmapView ? 'primary' : ''}`} 
                      onClick={() => setIsHeatmapView(true)}
                      disabled={!uploadedImage || isProcessing}
                    >
                      Density Heatmap
                    </button>
                  </div>
                  <div className="feed-badge">Pipeline Node: Feed_01</div>
                </div>

                <div className="video-display">
                  {isProcessing ? (
                    <div style={{ textAlign: 'center' }}>
                      <div className="pulse-dot processing-pulse"></div>
                      <p style={{ fontWeight: '500', color: '#6366f1', marginTop: '1rem' }}>Running Crowd Density Regression Array Model...</p>
                    </div>
                  ) : !uploadedImage ? (
                    <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                      <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📁</span>
                      <p>Inference queue empty. Upload an image below to generate density heatmap analytics.</p>
                    </div>
                  ) : (
                    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                      <img 
                        src={uploadedImage} 
                        alt="Uploaded Crowd Frame Source" 
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                      />
                      {isHeatmapView && (
                        <div className="mock-heatmap">
                          <span className="heatmap-overlay-text">🔥 Density Regression Heatmap Layer Active</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Side Control Interface Panel */}
              <div className="sidebar-panels">
                <div className="controls-card">
                  <h3>Model Control Panel</h3>
                  <hr className="divider" />
                  
                  <div style={{ marginBottom: '1.25rem' }}>
                    <label className="input-label">Processing Pipeline Source:</label>
                    <select className="premium-select">
                      <option>Static Image Testing (.png, .jpg)</option>
                      <option>Network CCTV RTSP Live Video</option>
                      <option>Sequence Video Batch Folder</option>
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Ingest Crowd Target Frame:</label>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleImageUpload} 
                      style={{ display: 'none' }} 
                      id="file-upload"
                    />
                    <label 
                      htmlFor="file-upload" 
                      className="btn primary custom-upload-btn"
                    >
                      {isProcessing ? "Processing Matrix..." : "Upload Local Image Stream"}
                    </label>
                  </div>
                </div>

                {/* System Log Console panel */}
                <div className="logs-card">
                  <h3>System Logs</h3>
                  <hr className="divider" />
                  <div className="logs-container">
                    <div className="log-item info">
                      <span className="log-timestamp">[LOCAL]</span> Handshake connection established.
                    </div>
                    <div className="log-item success">
                      <span className="log-timestamp">[CUDA]</span> Processing cores optimized successfully.
                    </div>
                    {estimatedCount > 0 && (
                      <div className="log-item error">
                        <span className="log-timestamp">[ML-EVENT]</span> Target Count baseline matched. Heatmap generated.
                      </div>
                    )}
                  </div>
                </div>
              </div>

            </section>
          </div>
        )}

        {activeTab === 'feeds' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card">
              <h3>Active Camera Feeds & Matrix Nodes</h3>
              <p style={{color: 'var(--text-muted)', marginBottom: '1.5rem'}}>Manage connected telemetry sensors currently routing to backend GPU clusters.</p>
              
              <div className="camera-grid">
                {cameraNodes.map((node) => (
                  <div className="camera-node-card" key={node.id}>
                    <div className="node-header">
                      <span className="node-id">⚙️ {node.id}</span>
                      <span className={`status-badge ${node.status.toLowerCase()}`}>{node.status}</span>
                    </div>
                    <h4>{node.location}</h4>
                    <div className="node-meta-row">
                      <span>Last Count: <strong>{node.count}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card">
              <div className="trends-header">
                <h3>Macro Temporal Spatial Trends Summary</h3>
                <span className="trends-indicator-badge">Loop Window: 24h Active Log Array</span>
              </div>
              <div className="trends-placeholder" style={{ height: '300px' }}>
                <p style={{fontSize: '2rem', margin: '0'}}>📊</p>
                <p style={{fontWeight: '600', marginTop: '0.5rem'}}>Spatial Graph Component Active Hub</p>
                <span style={{fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '450px', textAlign: 'center'}}>
                  Connect Recharts, Chart.js, or ApexCharts endpoints straight into backend matrix logs arrays to map out historical crowd regression variations over time.
                </span>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card configuration-panel">
              <h3>System Model Preferences & Configuration</h3>
              <hr className="divider" />
              
              <div className="setting-row">
                <div>
                  <h4>Capacity Notification Threshold</h4>
                  <p>Triggers critical dashboard visual state adjustments if a node count exceeds value limit bounds.</p>
                </div>
                <input 
                  type="number" 
                  className="premium-input" 
                  value={alertThreshold} 
                  onChange={(e) => setAlertThreshold(Number(e.target.value))} 
                />
              </div>

              <div className="setting-row">
                <div>
                  <h4>CUDA Acceleration Matrix Engine</h4>
                  <p>Routes image streams across system threads through tensor architectures to minimize model execution delay bounds.</p>
                </div>
                <button 
                  className={`btn ${gpuAcceleration ? 'primary' : ''}`}
                  onClick={() => setGpuAcceleration(!gpuAcceleration)}
                >
                  {gpuAcceleration ? "Matrix Enabled" : "Matrix Disabled"}
                </button>
              </div>
            </section>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;