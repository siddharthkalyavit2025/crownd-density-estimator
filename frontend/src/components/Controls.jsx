import React from 'react';

function Controls({ selectedCam, setSelectedCam, cameraIds, showHeatmap, setShowHeatmap, occlusion, setOcclusion, triggerInference, isInferenceRunning }) {
  return (
    <div className="panel control-panel">
      <h2>SYSTEM CONTROLS</h2>
      <div className="control-group">
        <label>SELECT CCTV SOURCE</label>
        <select value={selectedCam} onChange={(e) => setSelectedCam(e.target.value)}>
          {cameraIds.map((key) => (
            <option key={key} value={key}>
              {key.toUpperCase().replace('-', ' ')}
            </option>
          ))}
        </select>
      </div>
      <div className="control-group">
        <label>HEATMAP REGRESSION OVERLAY</label>
        <button className={`toggle-btn ${showHeatmap ? 'active' : ''}`} onClick={() => setShowHeatmap(!showHeatmap)}>
          {showHeatmap ? 'DISABLING OVERLAY' : 'ENABLING OVERLAY'}
        </button>
      </div>
      <div className="control-group">
        <label>OCCLUSION CORRECTION: {occlusion}%</label>
        <input type="range" min="0" max="100" value={occlusion} onChange={(e) => setOcclusion(Number(e.target.value))} />
      </div>
      <button className="inference-btn" disabled={isInferenceRunning} onClick={triggerInference}>
        {isInferenceRunning ? 'RUNNING INFERENCE...' : 'FORCE RE-INFERENCE'}
      </button>
    </div>
  );
}

export default Controls;