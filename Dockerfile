# =========================================================
# NexusOS Production Runtime
# Railway + FastAPI + Frontend Runtime
# =========================================================

# ---------------------------------------------------------
# Stage 1 — Frontend Build
# ---------------------------------------------------------

FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ .

RUN npm run build

# Ensure public directory exists (create if missing)
RUN mkdir -p /app/frontend/public

# ---------------------------------------------------------
# Stage 2 — Backend Runtime
# ---------------------------------------------------------

FROM python:3.11-slim

WORKDIR /app

# ---------------------------------------------------------
# Runtime Environment
# ---------------------------------------------------------

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# ---------------------------------------------------------
# System Dependencies
# ---------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Python Dependencies
# ---------------------------------------------------------

COPY backend/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Copy Backend
# ---------------------------------------------------------

COPY backend ./backend

# ---------------------------------------------------------
# Copy Frontend Build
# ---------------------------------------------------------

COPY --from=frontend-builder /app/frontend/.next ./frontend/.next

# ---------------------------------------------------------
# Railway Port
# ---------------------------------------------------------

EXPOSE 8000

# ---------------------------------------------------------
# Railway Healthcheck
# ---------------------------------------------------------

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# ---------------------------------------------------------
# Runtime Start
# ---------------------------------------------------------

CMD ["sh", "-c", "python -m backend.main"]