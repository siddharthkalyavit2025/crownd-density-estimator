import React from 'react';

function Metrics({ adjustedCount, baseCount, status, statusColor, confidence }) {
  return (
    <div className="panel metrics-panel">
      <h2>REAL-TIME METRICS</h2>
      <div className="metric-box">
        <div className="metric-label">ESTIMATED CROWD COUNT</div>
        <div className="metric-value">{adjustedCount}</div>
        <div className="metric-sub">Base Count: {baseCount} + Occlusion Adjustment</div>
      </div>
      <div className="metric-box">
        <div className="metric-label">DENSITY RISK LEVEL</div>
        <div className="metric-value" style={{ color: statusColor }}>
          {status.toUpperCase()}
        </div>
      </div>
      <div className="metric-box">
        <div className="metric-label">MODEL CONFIDENCE</div>
        <div className="metric-value">{confidence}%</div>
      </div>
    </div>
  );
}

export default Metrics;