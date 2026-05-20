# NexusOS Deployment Topology

## Single-Container Deployment (Docker)

The production Docker image packages everything into a single container:

```
+-------------------------------------------------------+
|                Docker Container                        |
|                (nexusos:latest)                        |
+-------------------------------------------------------+
|                                                       |
|  +------------------+    +------------------------+   |
|  | Frontend Assets  |    | Backend (FastAPI)      |   |
|  | (Next.js static  |    |                        |   |
|  |  build output)   |    | - Uvicorn ASGI server  |   |
|  +------------------+    | - API routes           |   |
|                          | - Governance engine    |   |
|                          | - Runtime manager      |   |
|                          | - Telemetry collector  |   |
|                          | - Replay recorder      |   |
|                          | - Event bus            |   |
|                          | - Workflow engine      |   |
|                          +------------------------+   |
|                                                       |
|  +------------------------------------------------+   |
|  | Playwright (Chromium)                           |   |
|  | - Headless browser for BrowserRuntime           |   |
|  +------------------------------------------------+   |
|                                                       |
+-------------------------------------------------------+
                    |
                    | Port 8000 (HTTP)
                    v
            External Access
```

## Docker Compose (Development)

```
+-----------------------------------------------------------+
|                    Docker Compose                          |
+-----------------------------------------------------------+
|                                                           |
|  +-------------------------+   +-----------------------+  |
|  | backend                 |   | frontend              |  |
|  | (Dockerfile)            |   | (Dockerfile.dev)      |  |
|  |                         |   |                       |  |
|  | - FastAPI + Uvicorn     |   | - Next.js dev server  |  |
|  | - Playwright/Chromium   |   | - Hot reload          |  |
|  | - Port 8000             |   | - Port 3000           |  |
|  |                         |   |                       |  |
|  | Health check:           |   | Depends on: backend   |  |
|  |  GET /api/status        |   |  (service_healthy)    |  |
|  |                         |   |                       |  |
|  | Restart: unless-stopped |   | Restart: unless-stop  |  |
|  +-------------------------+   +-----------------------+  |
|                                                           |
+-----------------------------------------------------------+
        |                               |
        | Port 8000                     | Port 3000
        v                               v
   API Access                     Dashboard Access
```

## Multi-Stage Build Process

```
Stage 1: frontend-builder (node:20-alpine)
+------------------------------------------+
| - npm ci (install dependencies)          |
| - npm run build (Next.js static build)   |
| - Output: .next/static/                  |
+------------------------------------------+
         |
         | COPY static assets
         v
Stage 2: runtime (python:3.9-slim)
+------------------------------------------+
| - pip install requirements.txt           |
| - pip install playwright                 |
| - playwright install chromium            |
| - COPY backend/                          |
| - COPY static frontend assets           |
| - EXPOSE 8000                            |
| - CMD: uvicorn backend.main:app          |
+------------------------------------------+
```

## Port Mapping

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Backend API | 8000 | 8000 | REST API + static frontend |
| Frontend Dev | 3000 | 3000 | Development dashboard (dev only) |

## Scaling Topology (Production)

```
                 +------------------+
                 | Load Balancer    |
                 | (nginx/ALB/etc)  |
                 +--------+---------+
                          |
            +-------------+-------------+
            |             |             |
            v             v             v
     +------+------+ +---+---+ +-------+-----+
     | NexusOS     | | NexusOS | | NexusOS     |
     | Instance 1  | | Instance 2| | Instance N  |
     | (port 8000) | | (port 8000)| | (port 8000) |
     +------+------+ +---+---+ +-------+-----+
            |             |             |
            +-------------+-------------+
                          |
                          v
                 +--------+---------+
                 | Persistent Store |
                 | (audit, replay,  |
                 |  telemetry)      |
                 +------------------+
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXUSOS_HOST` | 0.0.0.0 | Bind address |
| `NEXUSOS_PORT` | 8000 | API port |
| `NEXUSOS_LOG_LEVEL` | info | Logging verbosity |
| `NEXUSOS_CORS_ORIGINS` | http://localhost:3000 | Allowed CORS origins |
| `NEXUSOS_GOVERNANCE_MODE` | strict | Governance enforcement level |
