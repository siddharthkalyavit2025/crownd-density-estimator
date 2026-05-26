import React from 'react';

function Visualizer({ cameraName, showHeatmap, heatmapColors, occlusion }) {
  return (
    <div className="panel visualizer-panel">
      <div className="panel-header-row">
        <h2>LIVE CAMERA FEED</h2>
        <span className="cam-label">{cameraName}</span>
      </div>
      <div className="video-container">
        <div className="mock-video">
          <div className="grid-overlay"></div>
          {showHeatmap && (
            <div className="heatmap-overlay-container">
              {heatmapColors.map((color, idx) => (
                <div 
                  key={idx}
                  className="heatmap-blob" 
                  style={{
                    backgroundColor: color,
                    top: `${20 + idx * 25}%`,
                    left: `${15 + idx * 30}%`,
                    width: `${120 + idx * 40}px`,
                    height: `${120 + idx * 40}px`,
                    filter: `blur(${20 + occlusion / 2}px)`
                  }}
                />
              ))}
            </div>
          )}
          <div className="telemetry-overlay">
            <div>FPS: 30.00</div>
            <div>LATENCY: 12ms</div>
            <div>RESOLUTION: 1920x1080</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Visualizer;