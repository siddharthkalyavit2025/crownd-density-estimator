import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

function App() {
  // Application State
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isDarkMode, setIsDarkMode] = useState(true);

  // ML Pipeline States
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isHeatmapView, setIsHeatmapView] = useState(false);
  const [estimatedCount, setEstimatedCount] = useState(0);
  const [densityStatus, setDensityStatus] = useState('No Input');
  const [inferenceTime, setInferenceTime] = useState('0 ms');

  // Backend response data
  const [heatmapUrl, setHeatmapUrl] = useState(null);
  const [overlayUrl, setOverlayUrl] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [densityStats, setDensityStats] = useState(null);

  // Server status
  const [serverStatus, setServerStatus] = useState('Checking...');
  const [serverConnected, setServerConnected] = useState(false);

  // Error state
  const [error, setError] = useState(null);

  // Camera node tracking
  const [cameraNodes] = useState([
    { id: 'Feed_01', location: 'North Entrance Gate', status: 'Active', count: 142 },
    { id: 'Feed_02', location: 'South Ticket Plaza', status: 'Active', count: 85 },
    { id: 'Feed_03', location: 'East Main Concourse', status: 'Offline', count: 0 },
  ]);

  // System Config
  const [alertThreshold, setAlertThreshold] = useState(100);
  const [gpuAcceleration, setGpuAcceleration] = useState(true);

  // Analytics history from backend
  const [analysisHistory, setAnalysisHistory] = useState([]);

  // Check server health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          setServerStatus('Connected');
          setServerConnected(true);
        } else {
          setServerStatus('Error');
          setServerConnected(false);
        }
      } catch {
        setServerStatus('Disconnected');
        setServerConnected(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch analytics history when history tab is active
  useEffect(() => {
    if (activeTab === 'history') {
      const fetchHistory = async () => {
        try {
          const res = await fetch('/api/analytics/history?per_page=20');
          if (res.ok) {
            const data = await res.json();
            if (data.success) {
              setAnalysisHistory(data.data.analyses || []);
            }
          }
        } catch {
          // Silently fail — history is non-critical
        }
      };
      fetchHistory();
    }
  }, [activeTab]);

  // Real API call to backend
  const handleImageUpload = useCallback(async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Cleanup previous blob URL
    if (uploadedImage) {
      URL.revokeObjectURL(uploadedImage);
    }

    const previewUrl = URL.createObjectURL(file);
    setUploadedImage(previewUrl);
    setIsProcessing(true);
    setDensityStatus('Analyzing...');
    setError(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        body: formData,
      });

      const json = await res.json();

      if (json.success) {
        const d = json.data;
        setEstimatedCount(d.estimated_count);
        setDensityStatus(d.density_status);
        setInferenceTime(d.inference_time);
        setHeatmapUrl(d.heatmap_url);
        setOverlayUrl(d.overlay_url);
        setOriginalUrl(d.original_url);
        setAnalysisId(d.analysis_id);
        setDensityStats(d.density_map_stats || null);
        setIsHeatmapView(true);
      } else {
        setError(json.error?.message || 'Prediction failed.');
        setDensityStatus('Error');
      }
    } catch (err) {
      setError('Failed to connect to the backend server. Make sure the Flask server is running on port 5000.');
      setDensityStatus('Error');
    } finally {
      setIsProcessing(false);
    }
  }, [uploadedImage]);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (uploadedImage) {
        URL.revokeObjectURL(uploadedImage);
      }
    };
  }, [uploadedImage]);

  const toggleTheme = () => setIsDarkMode(!isDarkMode);

  const dismissError = () => setError(null);

  // Determine which image to show in the viewer
  const displayImageSrc = isHeatmapView && overlayUrl
    ? overlayUrl
    : originalUrl || uploadedImage;

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
            📈 Analysis History
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

      {/* MAIN CONTENT */}
      <main className="main-content">

        {/* HEADER */}
        <header className="header">
          <div>
            <h1 className="main-title">Crowd Density Estimator</h1>
            <p className="main-subtitle">Real-time crowd density analysis powered by CSRNet deep learning.</p>
          </div>

          <div className="header-controls">
            <button className="theme-toggle-btn" onClick={toggleTheme}>
              {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
            </button>
            <div className="status-indicator">
              <span className={`pulse-dot ${!serverConnected ? 'disconnected' : ''}`}></span>
              <span>Model Server: <strong style={{ color: serverConnected ? '#10b981' : '#ef4444' }}>{serverStatus}</strong></span>
            </div>
          </div>
        </header>

        {/* ERROR BANNER */}
        {error && (
          <div className="error-banner animate-fade">
            <span>⚠️ {error}</span>
            <button className="error-dismiss" onClick={dismissError}>✕</button>
          </div>
        )}

        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && (
          <div className="tab-view-container animate-fade">
            <section className="stats-grid">
              <div className="stat-card">
                <div className="card-meta">LIVE TELEMETRY</div>
                <h3>Estimated Crowd Count</h3>
                <div className="stat-value" style={{ color: estimatedCount > alertThreshold ? '#ef4444' : 'inherit' }}>
                  {isProcessing ? '...' : estimatedCount}
                </div>
                <div className="card-subtext">Heads detected via density map regression</div>
              </div>

              <div className="stat-card">
                <div className="card-meta">THRESHOLD STATUS</div>
                <h3>Density Status</h3>
                <div className="stat-value" style={{ color: densityStatus === 'High Density' || densityStatus === 'Critical Density' ? '#f59e0b' : densityStatus === 'Error' ? '#ef4444' : 'inherit' }}>
                  {densityStatus}
                </div>
                <div className="card-subtext">Current capacity classification</div>
              </div>

              <div className="stat-card">
                <div className="card-meta">PERFORMANCE</div>
                <h3>Inference Time</h3>
                <div className="stat-value" style={{ color: '#10b981' }}>
                  {isProcessing ? 'Running...' : inferenceTime}
                </div>
                <div className="card-subtext">Backend model execution duration</div>
              </div>
            </section>

            {/* Density map stats row */}
            {densityStats && (
              <section className="stats-grid stats-grid-secondary">
                <div className="stat-card mini">
                  <div className="card-meta">DENSITY MAP</div>
                  <h3>Max Density</h3>
                  <div className="stat-value small">{densityStats.max_density?.toFixed(4) || '—'}</div>
                </div>
                <div className="stat-card mini">
                  <div className="card-meta">DENSITY MAP</div>
                  <h3>Mean Density</h3>
                  <div className="stat-value small">{densityStats.mean_density?.toFixed(4) || '—'}</div>
                </div>
                {analysisId && (
                  <div className="stat-card mini">
                    <div className="card-meta">RECORD</div>
                    <h3>Analysis ID</h3>
                    <div className="stat-value small">{analysisId}</div>
                  </div>
                )}
              </section>
            )}

            <section className="workspace">
              {/* Main Image/Heatmap Viewer */}
              <div className="viewer-card">
                <div className="viewer-toolbar">
                  <div className="view-toggle">
                    <button
                      className={`btn ${!isHeatmapView ? 'primary' : ''}`}
                      onClick={() => setIsHeatmapView(false)}
                      disabled={!uploadedImage || isProcessing}
                    >
                      Original Image
                    </button>
                    <button
                      className={`btn ${isHeatmapView ? 'primary' : ''}`}
                      onClick={() => setIsHeatmapView(true)}
                      disabled={!overlayUrl || isProcessing}
                    >
                      Density Heatmap
                    </button>
                  </div>
                  {analysisId && <div className="feed-badge">Analysis: {analysisId}</div>}
                </div>

                <div className="video-display">
                  {isProcessing ? (
                    <div style={{ textAlign: 'center' }}>
                      <div className="pulse-dot processing-pulse"></div>
                      <p style={{ fontWeight: '500', color: '#6366f1', marginTop: '1rem' }}>Running CSRNet inference...</p>
                    </div>
                  ) : !uploadedImage && !originalUrl ? (
                    <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                      <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📁</span>
                      <p>Upload a crowd image to generate density heatmap analysis.</p>
                    </div>
                  ) : (
                    <img
                      src={displayImageSrc}
                      alt={isHeatmapView ? 'Density heatmap overlay' : 'Original crowd image'}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  )}
                </div>

                {/* Heatmap-only view link */}
                {heatmapUrl && !isProcessing && (
                  <div className="heatmap-link-row">
                    <a href={heatmapUrl} target="_blank" rel="noopener noreferrer" className="btn">
                      🔥 View Standalone Heatmap
                    </a>
                  </div>
                )}
              </div>

              {/* Right Side Panels */}
              <div className="sidebar-panels">
                <div className="controls-card">
                  <h3>Model Control Panel</h3>
                  <hr className="divider" />

                  <div style={{ marginBottom: '1.25rem' }}>
                    <label className="input-label">Processing Pipeline Source:</label>
                    <select className="premium-select">
                      <option>Static Image Upload (.png, .jpg)</option>
                      <option>Network CCTV RTSP Live Video</option>
                      <option>Batch Video Frame Analysis</option>
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Upload Crowd Image:</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      style={{ display: 'none' }}
                      id="file-upload"
                      disabled={isProcessing}
                    />
                    <label
                      htmlFor="file-upload"
                      className={`btn primary custom-upload-btn ${isProcessing ? 'disabled' : ''}`}
                    >
                      {isProcessing ? 'Processing...' : 'Upload Image for Analysis'}
                    </label>
                  </div>
                </div>

                <div className="logs-card">
                  <h3>System Logs</h3>
                  <hr className="divider" />
                  <div className="logs-container">
                    <div className={`log-item ${serverConnected ? 'success' : 'error'}`}>
                      <span className="log-timestamp">[SYS]</span>
                      {serverConnected ? 'Backend server connected.' : 'Backend server unreachable.'}
                    </div>
                    {estimatedCount > 0 && (
                      <div className="log-item info">
                        <span className="log-timestamp">[ML]</span>
                        Count: {estimatedCount} | Status: {densityStatus} | Time: {inferenceTime}
                      </div>
                    )}
                    {overlayUrl && (
                      <div className="log-item success">
                        <span className="log-timestamp">[OUT]</span>
                        Heatmap and overlay generated successfully.
                      </div>
                    )}
                    {error && (
                      <div className="log-item error">
                        <span className="log-timestamp">[ERR]</span>
                        {error}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* CAMERA FEEDS TAB */}
        {activeTab === 'feeds' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card">
              <h3>Active Camera Feeds</h3>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>Connected CCTV sources routing to the ML backend.</p>

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

        {/* HISTORY TAB */}
        {activeTab === 'history' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card">
              <div className="trends-header">
                <h3>Analysis History</h3>
                <span className="trends-indicator-badge">{analysisHistory.length} Records</span>
              </div>

              {analysisHistory.length > 0 ? (
                <div className="history-table-wrapper">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Count</th>
                        <th>Status</th>
                        <th>Inference</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisHistory.map((item) => (
                        <tr key={item.analysis_id}>
                          <td><code>{item.analysis_id}</code></td>
                          <td><strong>{item.estimated_count}</strong></td>
                          <td><span className={`status-badge ${item.density_status?.toLowerCase().includes('low') ? 'active' : item.density_status?.toLowerCase().includes('critical') ? 'offline' : 'active'}`}>{item.density_status}</span></td>
                          <td>{item.inference_time_ms?.toFixed(1)} ms</td>
                          <td>{item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="trends-placeholder" style={{ height: '200px' }}>
                  <p style={{ fontSize: '2rem', margin: '0' }}>📊</p>
                  <p style={{ fontWeight: '600', marginTop: '0.5rem' }}>No Analysis Records Yet</p>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Upload images on the Dashboard tab to create analysis records.
                  </span>
                </div>
              )}
            </section>
          </div>
        )}

        {/* SETTINGS TAB */}
        {activeTab === 'settings' && (
          <div className="tab-view-container animate-fade">
            <section className="generic-card configuration-panel">
              <h3>System Configuration</h3>
              <hr className="divider" />

              <div className="setting-row">
                <div>
                  <h4>Alert Threshold</h4>
                  <p>Triggers visual warning when crowd count exceeds this value.</p>
                </div>
                <input
                  type="number"
                  className="premium-input"
                  value={alertThreshold}
                  min="1"
                  onChange={(e) => setAlertThreshold(Math.max(1, Number(e.target.value)))}
                />
              </div>

              <div className="setting-row">
                <div>
                  <h4>GPU Acceleration</h4>
                  <p>Uses CUDA GPU for faster model inference when available.</p>
                </div>
                <button
                  className={`btn ${gpuAcceleration ? 'primary' : ''}`}
                  onClick={() => setGpuAcceleration(!gpuAcceleration)}
                >
                  {gpuAcceleration ? 'Enabled' : 'Disabled'}
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