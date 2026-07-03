# ── Stage 1: Build the React frontend ────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend + serve built frontend ───────────────────
FROM python:3.11-slim

# System dependencies for OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy the built frontend into a static directory
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# The model checkpoint should be mounted as a volume at runtime
# e.g. -v /path/to/csrnet_final.pth:/app/csrnet_final.pth

WORKDIR /app/backend

# Expose the Flask port
EXPOSE 5000

# Production server via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "wsgi:application"]
