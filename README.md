# 👁️ CrowdVision AI — Crowd Density Estimator

> Feed a CCTV-style image or video → the model estimates how many people are in the frame and outputs a density heatmap.

**Fully functional** — React frontend integrated with Flask backend and CSRNet deep learning model.

---

## 🏗️ Architecture

```
┌──────────────────┐       REST API        ┌──────────────────────┐
│  React Frontend  │ ◄──────/api/──────►   │   Flask Backend      │
│  (Vite + React)  │                       │                      │
│  localhost:5173   │                       │  ┌────────────────┐  │
│                   │                       │  │  CSRNet Model  │  │
│  • Upload Image   │   POST /api/predict   │  │  (PyTorch)     │  │
│  • View Heatmap   │ ──────────────────►   │  └────────────────┘  │
│  • Analytics      │                       │  ┌────────────────┐  │
│                   │   ◄── JSON + URLs ──  │  │  SQLite DB     │  │
└──────────────────┘                       │  └────────────────┘  │
                                           │  localhost:5000      │
                                           └──────────────────────┘
```

## 👥 Team Roles (5 Members)

| # | Role | Focus |
|---|------|-------|
| 1 | **AI/ML Engineer** | CSRNet training, density map regression, occlusion handling |
| 2 | **Backend Engineer** | Flask API, model serving, database, integration |
| 3 | **Frontend Engineer** | React dashboard, heatmap visualisation, UX |
| 4 | **DevOps** | Docker, CI/CD, deployment, monitoring |
| 5 | **QA / Documentation** | Testing, API docs, benchmarks |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- `csrnet_final.pth` model file in the project root

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

The Flask server starts at **http://localhost:5000**.

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

The Vite dev server starts at **http://localhost:5173** with API proxy to Flask.

### 3. Docker (Alternative)

```bash
# Build and run with Docker Compose
docker compose up --build

# The model checkpoint must exist at the project root:
# ./csrnet_final.pth
```

The application is served at **http://localhost:5000**.

---

## 📡 API Endpoints

### Core Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict` | Upload image → get crowd count + heatmap |

**Request:** `multipart/form-data` with `image` field

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "a1b2c3d4",
    "estimated_count": 142.3,
    "density_status": "High Density",
    "inference_time": "38 ms",
    "heatmap_url": "/api/outputs/heatmap_xxx.png",
    "overlay_url": "/api/outputs/overlay_xxx.png",
    "original_url": "/api/uploads/upload_xxx.jpg",
    "density_map_stats": { "max_density": 0.847, "mean_density": 0.123 },
    "image_dimensions": { "width": 1920, "height": 1080 }
  }
}
```

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Server & model health check |
| `GET` | `/api/health/model` | Detailed model diagnostics |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics/history` | Paginated analysis history |
| `GET` | `/api/analytics/stats` | Aggregate statistics |
| `GET` | `/api/analytics/:id` | Single analysis detail |
| `DELETE` | `/api/analytics/:id` | Delete analysis + files |

### Video Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/video/extract-frames` | Upload video → extract frames |
| `POST` | `/api/video/analyze-batch` | Batch analyse extracted frames |

---

## 📂 Project Structure

```
crownd-density-estimator/
├── csrnet_final.pth          # Pretrained CSRNet model (65 MB)
├── Crowd_Density_Estimator.ipynb  # ML training notebook
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Container orchestration
│
├── backend/                   # Flask API server
│   ├── app.py                 # Application factory
│   ├── config.py              # Environment configs
│   ├── wsgi.py                # Production WSGI entry
│   ├── requirements.txt       # Python dependencies (pinned)
│   ├── api/                   # Route blueprints
│   │   ├── routes_predict.py  # POST /api/predict
│   │   ├── routes_health.py   # GET /api/health
│   │   ├── routes_analytics.py # Analytics CRUD
│   │   └── routes_video.py    # Video processing
│   ├── core/                  # ML serving layer
│   │   ├── model_loader.py    # CSRNet + singleton manager
│   │   ├── inference.py       # Preprocessing + inference
│   │   ├── heatmap.py         # Density → heatmap images
│   │   └── video_processor.py # Frame extraction
│   ├── database/              # SQLAlchemy ORM
│   │   ├── db.py              # DB init
│   │   └── models.py          # Analysis model
│   ├── middleware/            # Cross-cutting concerns
│   │   ├── error_handlers.py  # Custom exceptions
│   │   ├── validators.py      # File validation
│   │   └── rate_limiter.py    # Rate limiting
│   └── utils/                 # Shared utilities
│       ├── logger.py          # Structured logging
│       ├── file_manager.py    # Upload/output management
│       └── helpers.py         # Response wrappers, timing
│
└── frontend/                  # React UI (Vite)
    ├── index.html             # HTML entry with SEO meta
    ├── vite.config.js         # Dev proxy to Flask backend
    ├── src/App.jsx            # Main dashboard (API-integrated)
    └── src/App.css            # Design system (responsive)
```

---

## ⚙️ Configuration

Set the `APP_ENV` environment variable:

| Value | Description |
|-------|-------------|
| `development` | Debug mode, verbose logging (default) |
| `production` | No debug, minimal logging |
| `testing` | In-memory SQLite, debug on |

---

## 🧠 Model Details

- **Architecture:** CSRNet (Congested Scene Recognition Network)
- **Backbone:** VGG-16 (first 13 conv layers)
- **Backend:** Dilated convolutions (rate=2) for density map regression
- **Output:** Density map whose sum = estimated crowd count
- **Paper:** [arXiv:1802.10062](https://arxiv.org/abs/1802.10062)

---

## 📜 License

This project is for educational purposes.