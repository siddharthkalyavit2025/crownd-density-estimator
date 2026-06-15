import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE = '/api';

/* ────────────────────────────────────────────────────────────
   Utility: density-status → colour
   ──────────────────────────────────────────────────────────── */
const getStatusColor = (status) => {
  switch (status) {
    case 'Low Density':      return '#10b981';
    case 'Moderate Density':  return '#f59e0b';
    case 'High Density':      return '#f97316';
    case 'Critical Density':  return '#ef4444';
    case 'Error':             return '#ef4444';
    default:                  return '#f8fafc';
  }
};

/* ════════════════════════════════════════════════════════════
   PAGE 1 — DASHBOARD  (predict)
   ════════════════════════════════════════════════════════════ */
function DashboardPage({ serverOnline }) {
  const [isHeatmapView, setIsHeatmapView] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [estimatedCount, setEstimatedCount] = useState(0);
  const [densityStatus, setDensityStatus] = useState('No Input');
  const [inferenceTime, setInferenceTime] = useState('0 ms');
  const [originalUrl, setOriginalUrl] = useState(null);
  const [heatmapUrl, setHeatmapUrl] = useState(null);
  const [overlayUrl, setOverlayUrl] = useState(null);
  const [analysisId, setAnalysisId] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setIsProcessing(true);
    setDensityStatus('Analyzing...');
    setErrorMsg(null);
    setUploadedFileName(file.name);
    const formData = new FormData();
    formData.append('image', file);
    try {
      const res = await fetch(`${API_BASE}/predict`, { method: 'POST', body: formData });
      const result = await res.json();
      if (result.success) {
        const d = result.data;
        setEstimatedCount(d.estimated_count);
        setDensityStatus(d.density_status);
        setInferenceTime(d.inference_time);
        setOriginalUrl(d.original_url);
        setHeatmapUrl(d.heatmap_url);
        setOverlayUrl(d.overlay_url);
        setAnalysisId(d.analysis_id);
        setIsHeatmapView(false);
      } else {
        setErrorMsg(result.error?.message || 'Prediction failed');
        setDensityStatus('Error');
      }
    } catch {
      setErrorMsg('Cannot reach backend. Is Flask running on port 5000?');
      setDensityStatus('Error');
    } finally {
      setIsProcessing(false);
    }
  };

  const onFileChange = (e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); };
  const onDrop = (e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) handleFileUpload(f); };

  return (
    <>
      {/* METRICS */}
      <section className="stats-grid">
        <div className="stat-card">
          <h3>Estimated Crowd Count</h3>
          <div className="stat-value" style={{ color: estimatedCount > 100 ? '#ef4444' : estimatedCount > 50 ? '#f59e0b' : '#f8fafc' }}>
            {isProcessing ? '...' : estimatedCount}
          </div>
        </div>
        <div className="stat-card">
          <h3>Density Status</h3>
          <div className="stat-value" style={{ color: getStatusColor(densityStatus) }}>{densityStatus}</div>
        </div>
        <div className="stat-card">
          <h3>Latency / Inference Time</h3>
          <div className="stat-value" style={{ color: '#10b981' }}>{isProcessing ? 'Running...' : inferenceTime}</div>
        </div>
      </section>

      {errorMsg && (
        <div className="error-banner">⚠️ {errorMsg}</div>
      )}

      {/* WORKSPACE */}
      <section className="workspace">
        <div className="viewer-card">
          <div className="view-toggle">
            <button className={`btn ${!isHeatmapView ? 'primary' : ''}`} onClick={() => setIsHeatmapView(false)}>Raw Feed</button>
            <button className={`btn ${isHeatmapView ? 'primary' : ''}`} onClick={() => setIsHeatmapView(true)} disabled={!overlayUrl}>Density Heatmap</button>
          </div>
          <div className="video-display"
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            style={{ borderColor: dragOver ? '#6366f1' : undefined }}
          >
            {isProcessing ? (
              <div style={{ textAlign: 'center' }}>
                <div className="pulse-dot" style={{ margin: '0 auto 1rem', width: 20, height: 20 }} />
                <p>Running CSRNet Density Map Regression...</p>
                <p className="text-muted" style={{ fontSize: '0.8rem' }}>Analyzing: {uploadedFileName}</p>
              </div>
            ) : !originalUrl ? (
              <div style={{ textAlign: 'center' }} className="text-muted">
                <p style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📁</p>
                <p>Drag & drop a CCTV image here</p>
                <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>or use the Upload panel →</p>
              </div>
            ) : (
              <img src={isHeatmapView ? overlayUrl : originalUrl} alt={isHeatmapView ? 'Heatmap' : 'Original'} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            )}
          </div>
        </div>

        <div className="controls-card">
          <h3>Model Input Panel</h3>
          <hr className="divider" />
          <label className="field-label">Upload Image:</label>
          <input ref={fileInputRef} type="file" accept="image/*" onChange={onFileChange} style={{ display: 'none' }} id="file-upload" />
          <label htmlFor="file-upload" className="btn primary upload-btn">
            {isProcessing ? '⏳ Analyzing...' : '📤 Upload & Analyze'}
          </label>
          {uploadedFileName && <div className="text-muted" style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>📄 {uploadedFileName}</div>}

          {analysisId && (
            <div className="result-box">
              <strong>Analysis Result:</strong>
              <div style={{ marginTop: '0.5rem', lineHeight: 1.8 }}>
                🆔 ID: <code>{analysisId}</code><br />
                👥 Count: <strong style={{ color: '#f8fafc' }}>{estimatedCount}</strong><br />
                📊 Status: <strong style={{ color: getStatusColor(densityStatus) }}>{densityStatus}</strong><br />
                ⚡ Speed: <strong style={{ color: '#10b981' }}>{inferenceTime}</strong>
              </div>
            </div>
          )}
          {heatmapUrl && (
            <a href={heatmapUrl} target="_blank" rel="noreferrer" className="link-accent" style={{ display: 'block', marginTop: '0.75rem' }}>
              🔗 View Standalone Heatmap
            </a>
          )}
        </div>
      </section>
    </>
  );
}

/* ════════════════════════════════════════════════════════════
   PAGE 2 — CAMERA FEEDS  (video upload + batch)
   ════════════════════════════════════════════════════════════ */
function CameraFeedsPage() {
  const [frames, setFrames] = useState([]);
  const [videoInfo, setVideoInfo] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [batchResults, setBatchResults] = useState(null);
  const [error, setError] = useState(null);

  const handleVideoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsExtracting(true);
    setError(null);
    setBatchResults(null);
    setFrames([]);
    const formData = new FormData();
    formData.append('video', file);
    try {
      const res = await fetch(`${API_BASE}/video/extract-frames?frame_interval=30&max_frames=20`, { method: 'POST', body: formData });
      const result = await res.json();
      if (result.success) {
        setFrames(result.data.frame_urls);
        setVideoInfo(result.data.video_info);
      } else {
        setError(result.error?.message || 'Frame extraction failed');
      }
    } catch {
      setError('Cannot reach backend server.');
    } finally {
      setIsExtracting(false);
    }
  };

  const analyzeBatch = async () => {
    if (frames.length === 0) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/video/analyze-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame_urls: frames }),
      });
      const result = await res.json();
      if (result.success) {
        setBatchResults(result.data);
      } else {
        setError(result.error?.message || 'Batch analysis failed');
      }
    } catch {
      setError('Cannot reach backend server.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <>
      <section className="stats-grid">
        <div className="stat-card">
          <h3>Frames Extracted</h3>
          <div className="stat-value">{frames.length}</div>
        </div>
        <div className="stat-card">
          <h3>Video FPS</h3>
          <div className="stat-value" style={{ color: '#10b981' }}>{videoInfo?.fps ?? '—'}</div>
        </div>
        <div className="stat-card">
          <h3>Duration</h3>
          <div className="stat-value" style={{ color: '#6366f1' }}>{videoInfo ? `${videoInfo.duration_seconds}s` : '—'}</div>
        </div>
      </section>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <section className="workspace" style={{ gridTemplateColumns: '1fr' }}>
        <div className="controls-card">
          <h3>📹 Video Upload & Frame Analysis</h3>
          <hr className="divider" />

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
            <div>
              <input type="file" accept="video/*" onChange={handleVideoUpload} style={{ display: 'none' }} id="video-upload" />
              <label htmlFor="video-upload" className="btn primary" style={{ cursor: 'pointer', padding: '0.75rem 1.5rem' }}>
                {isExtracting ? '⏳ Extracting Frames...' : '📤 Upload Video'}
              </label>
            </div>
            {frames.length > 0 && (
              <button className="btn primary" onClick={analyzeBatch} disabled={isAnalyzing} style={{ padding: '0.75rem 1.5rem' }}>
                {isAnalyzing ? '⏳ Analyzing Batch...' : `🔍 Analyze ${frames.length} Frames`}
              </button>
            )}
          </div>

          {/* Frame grid */}
          {frames.length > 0 && (
            <div className="frame-grid">
              {frames.map((url, i) => {
                const batchItem = batchResults?.results?.find(r => r.frame_index === i);
                return (
                  <div key={i} className="frame-card">
                    <img src={url} alt={`Frame ${i + 1}`} />
                    <div className="frame-info">
                      <span>Frame {i + 1}</span>
                      {batchItem && !batchItem.error && (
                        <span style={{ color: getStatusColor(batchItem.density_status), fontWeight: 600 }}>
                          👥 {batchItem.estimated_count}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Batch summary */}
          {batchResults?.summary && (
            <div className="result-box" style={{ marginTop: '1.5rem' }}>
              <strong>📊 Batch Analysis Summary</strong>
              <div style={{ marginTop: '0.5rem', lineHeight: 1.8 }}>
                🎬 Frames Analyzed: <strong>{batchResults.summary.total_frames_analyzed}</strong><br />
                📈 Average Count: <strong style={{ color: '#f8fafc' }}>{batchResults.summary.average_count}</strong><br />
                🔺 Peak Count: <strong style={{ color: '#ef4444' }}>{batchResults.summary.max_count}</strong><br />
                🔻 Min Count: <strong style={{ color: '#10b981' }}>{batchResults.summary.min_count}</strong><br />
                ❌ Errors: <strong>{batchResults.summary.total_errors}</strong>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  );
}

/* ════════════════════════════════════════════════════════════
   PAGE 3 — ANALYTICS HISTORY
   ════════════════════════════════════════════════════════════ */
function AnalyticsPage() {
  const [analyses, setAnalyses] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [histRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/history?page=${page}&per_page=10`),
        fetch(`${API_BASE}/analytics/stats`),
      ]);
      const hist = await histRes.json();
      const st = await statsRes.json();
      if (hist.success) { setAnalyses(hist.data.analyses); setPagination(hist.data.pagination); }
      if (st.success) setStats(st.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, [page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const deleteAnalysis = async (id) => {
    if (!confirm(`Delete analysis ${id}?`)) return;
    try {
      await fetch(`${API_BASE}/analytics/${id}`, { method: 'DELETE' });
      fetchData();
    } catch { /* ignore */ }
  };

  return (
    <>
      {/* Summary stats */}
      <section className="stats-grid">
        <div className="stat-card">
          <h3>Total Analyses</h3>
          <div className="stat-value">{stats?.total_analyses ?? 0}</div>
        </div>
        <div className="stat-card">
          <h3>Average Count</h3>
          <div className="stat-value" style={{ color: '#f59e0b' }}>{stats?.average_count ?? 0}</div>
        </div>
        <div className="stat-card">
          <h3>Peak Count</h3>
          <div className="stat-value" style={{ color: '#ef4444' }}>{stats?.peak_count ?? 0}</div>
        </div>
        <div className="stat-card">
          <h3>Avg Inference</h3>
          <div className="stat-value" style={{ color: '#10b981' }}>{stats?.average_inference_ms ? `${Math.round(stats.average_inference_ms)} ms` : '—'}</div>
        </div>
      </section>

      {/* Density distribution */}
      {stats?.density_distribution && Object.keys(stats.density_distribution).length > 0 && (
        <div className="controls-card" style={{ marginBottom: '1.5rem' }}>
          <h3>📊 Density Distribution</h3>
          <hr className="divider" />
          <div className="dist-bars">
            {Object.entries(stats.density_distribution).map(([label, count]) => (
              <div key={label} className="dist-row">
                <span className="dist-label" style={{ color: getStatusColor(label) }}>{label}</span>
                <div className="dist-bar-bg">
                  <div className="dist-bar-fill" style={{ width: `${Math.min(100, (count / stats.total_analyses) * 100)}%`, background: getStatusColor(label) }} />
                </div>
                <span className="dist-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History table */}
      <div className="controls-card">
        <h3>📋 Analysis History</h3>
        <hr className="divider" />

        {loading ? (
          <p className="text-muted">Loading...</p>
        ) : analyses.length === 0 ? (
          <p className="text-muted">No analyses yet. Go to Dashboard and upload an image!</p>
        ) : (
          <>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Count</th>
                    <th>Status</th>
                    <th>Inference</th>
                    <th>Size</th>
                    <th>Date</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((a) => (
                    <tr key={a.analysis_id}>
                      <td><code>{a.analysis_id}</code></td>
                      <td style={{ fontWeight: 700 }}>{a.estimated_count}</td>
                      <td style={{ color: getStatusColor(a.density_status) }}>{a.density_status}</td>
                      <td>{Math.round(a.inference_time_ms)} ms</td>
                      <td>{a.image_width}×{a.image_height}</td>
                      <td>{a.created_at ? new Date(a.created_at).toLocaleString() : '—'}</td>
                      <td>
                        <button className="btn-delete" onClick={() => deleteAnalysis(a.analysis_id)} title="Delete">🗑️</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {pagination && pagination.total_pages > 1 && (
              <div className="pagination">
                <button className="btn" disabled={!pagination.has_prev} onClick={() => setPage(p => p - 1)}>← Prev</button>
                <span className="text-muted">Page {pagination.page} of {pagination.total_pages}</span>
                <button className="btn" disabled={!pagination.has_next} onClick={() => setPage(p => p + 1)}>Next →</button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

/* ════════════════════════════════════════════════════════════
   PAGE 4 — MODEL SETTINGS
   ════════════════════════════════════════════════════════════ */
function ModelSettingsPage() {
  const [modelInfo, setModelInfo] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const [mRes, hRes] = await Promise.all([
          fetch(`${API_BASE}/health/model`),
          fetch(`${API_BASE}/health`),
        ]);
        const m = await mRes.json();
        const h = await hRes.json();
        if (m.success) setModelInfo(m.data);
        if (h.success) setHealthInfo(h.data);
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchInfo();
  }, []);

  if (loading) return <p className="text-muted" style={{ padding: '2rem' }}>Loading model info...</p>;

  return (
    <>
      <section className="stats-grid">
        <div className="stat-card">
          <h3>Architecture</h3>
          <div className="stat-value" style={{ fontSize: '1.5rem', color: '#6366f1' }}>{modelInfo?.architecture ?? '—'}</div>
        </div>
        <div className="stat-card">
          <h3>Parameters</h3>
          <div className="stat-value" style={{ fontSize: '1.5rem' }}>{modelInfo?.total_parameters ? `${(modelInfo.total_parameters / 1e6).toFixed(1)}M` : '—'}</div>
        </div>
        <div className="stat-card">
          <h3>Device</h3>
          <div className="stat-value" style={{ fontSize: '1.5rem', color: modelInfo?.device === 'cuda' ? '#10b981' : '#f59e0b' }}>
            {modelInfo?.device?.toUpperCase() ?? '—'}
          </div>
        </div>
        <div className="stat-card">
          <h3>Warmup Latency</h3>
          <div className="stat-value" style={{ fontSize: '1.5rem', color: '#10b981' }}>
            {modelInfo?.warmup_latency_ms ? `${Math.round(modelInfo.warmup_latency_ms)} ms` : '—'}
          </div>
        </div>
      </section>

      <section className="workspace" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {/* Model details */}
        <div className="controls-card">
          <h3>🧠 Model Details</h3>
          <hr className="divider" />
          <div className="settings-list">
            <div className="setting-row"><span className="text-muted">Architecture</span><span>{modelInfo?.architecture ?? 'Unknown'}</span></div>
            <div className="setting-row"><span className="text-muted">Total Parameters</span><span>{modelInfo?.total_parameters?.toLocaleString() ?? '—'}</span></div>
            <div className="setting-row"><span className="text-muted">Device</span><span>{modelInfo?.device ?? '—'}</span></div>
            <div className="setting-row"><span className="text-muted">Model Loaded</span><span style={{ color: modelInfo?.model_loaded ? '#10b981' : '#ef4444' }}>{modelInfo?.model_loaded ? '✅ Yes' : '❌ No'}</span></div>
            <div className="setting-row"><span className="text-muted">Warmup Success</span><span style={{ color: modelInfo?.warmup_success ? '#10b981' : '#ef4444' }}>{modelInfo?.warmup_success ? '✅ Yes' : '❌ No'}</span></div>
            {modelInfo?.gpu_memory && (
              <>
                <div className="setting-row"><span className="text-muted">GPU Allocated</span><span>{modelInfo.gpu_memory.allocated_mb} MB</span></div>
                <div className="setting-row"><span className="text-muted">GPU Reserved</span><span>{modelInfo.gpu_memory.reserved_mb} MB</span></div>
              </>
            )}
          </div>
        </div>

        {/* Server info */}
        <div className="controls-card">
          <h3>🖥️ Server Info</h3>
          <hr className="divider" />
          <div className="settings-list">
            <div className="setting-row"><span className="text-muted">Status</span><span style={{ color: '#10b981' }}>{healthInfo?.status ?? '—'}</span></div>
            <div className="setting-row"><span className="text-muted">Version</span><span>{healthInfo?.version ?? '—'}</span></div>
            <div className="setting-row"><span className="text-muted">Uptime</span><span>{healthInfo?.uptime_seconds ? `${Math.round(healthInfo.uptime_seconds / 60)} min` : '—'}</span></div>
            <div className="setting-row"><span className="text-muted">Total Predictions</span><span>{healthInfo?.total_predictions ?? 0}</span></div>
            <div className="setting-row"><span className="text-muted">Server Time</span><span>{healthInfo?.server_time ? new Date(healthInfo.server_time).toLocaleString() : '—'}</span></div>
          </div>

          <div className="result-box" style={{ marginTop: '1.5rem' }}>
            <strong>⚙️ Density Thresholds</strong>
            <div style={{ marginTop: '0.5rem', lineHeight: 1.8, fontSize: '0.85rem' }}>
              <span style={{ color: '#10b981' }}>Low Density:</span> 0 – 20 people<br />
              <span style={{ color: '#f59e0b' }}>Moderate:</span> 20 – 50 people<br />
              <span style={{ color: '#f97316' }}>High:</span> 50 – 150 people<br />
              <span style={{ color: '#ef4444' }}>Critical:</span> 150+ people
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

/* ════════════════════════════════════════════════════════════
   MAIN APP — Router + Sidebar
   ════════════════════════════════════════════════════════════ */
const PAGES = [
  { id: 'dashboard',  label: 'Dashboard',        icon: '📊' },
  { id: 'camera',     label: 'Camera Feeds',      icon: '📹' },
  { id: 'analytics',  label: 'Analytics History',  icon: '📈' },
  { id: 'settings',   label: 'Model Settings',     icon: '⚙️' },
];

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [serverOnline, setServerOnline] = useState(false);

  // Health poll
  useEffect(() => {
    const check = () => {
      fetch(`${API_BASE}/health`)
        .then(r => r.json())
        .then(d => setServerOnline(d.success && d.data.model_loaded))
        .catch(() => setServerOnline(false));
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const pageTitle = {
    dashboard: 'Crowd Density Estimator',
    camera:    'Camera Feeds',
    analytics: 'Analytics History',
    settings:  'Model Settings',
  };

  return (
    <div className="dashboard-container">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <h2>👁️ CrowdVision AI</h2>
        <nav>
          {PAGES.map(p => (
            <div
              key={p.id}
              className={`menu-item ${activePage === p.id ? 'active' : ''}`}
              onClick={() => setActivePage(p.id)}
            >
              {p.icon} {p.label}
            </div>
          ))}
        </nav>
      </aside>

      {/* MAIN */}
      <main className="main-content">
        <header className="header">
          <h1 className="main-title">{pageTitle[activePage]}</h1>
          <div className="status-indicator">
            <span className="pulse-dot" style={{ background: serverOnline ? '#10b981' : '#ef4444' }} />
            <span>{serverOnline ? 'Model Server: Operational' : 'Server: Offline'}</span>
          </div>
        </header>

        {activePage === 'dashboard' && <DashboardPage serverOnline={serverOnline} />}
        {activePage === 'camera' && <CameraFeedsPage />}
        {activePage === 'analytics' && <AnalyticsPage />}
        {activePage === 'settings' && <ModelSettingsPage />}
      </main>
    </div>
  );
}

export default App;