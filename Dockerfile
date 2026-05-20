# NexusOS Backend Dockerfile
# Governed runtime with deterministic execution

# Stage 1: Build frontend (for production static serving)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system dependencies (curl for healthcheck, wget as fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend static assets (for reference/production mode)
COPY --from=frontend-builder /app/frontend/.next/static ./static/frontend/

# Expose backend port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Run backend with explicit module path
ENV PYTHONPATH=/app
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
