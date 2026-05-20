# NexusOS Deployment Guide

This guide covers deploying NexusOS in various configurations, from local development to production.

---

## Prerequisites

### Required

- Docker 20.10+ and Docker Compose 2.0+
- OR Python 3.9+ and Node.js 18+ (for manual deployment)

### Recommended

- 2 CPU cores minimum (4 recommended)
- 2 GB RAM minimum (4 GB recommended)
- curl (for health checks)

---

## Docker Deployment (Recommended)

### Quick Start

```bash
# Copy environment configuration
cp .env.example .env

# Build and start all services
docker-compose up --build
```

This starts:
- **Backend** on port 8000 with health checks and auto-restart
- **Frontend** on port 3000 (depends on backend being healthy)

### Production Build

The Dockerfile uses a multi-stage build:

1. **Stage 1 (frontend-builder):** Builds the Next.js frontend using `node:20-alpine`
2. **Stage 2 (runtime):** Installs Python dependencies, copies the backend and built frontend assets

```bash
# Build the production image
docker build -t nexusos:latest .

# Run the production container
docker run -d \
  --name nexusos \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  nexusos:latest
```

### Health Check Verification

```bash
# Check if the service is healthy
curl -f http://localhost:8000/api/status

# Or use the provided script
./scripts/healthcheck.sh
```

---

## Docker Compose Deployment

The `docker-compose.yml` provides a complete multi-service setup:

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

### Commands

```bash
# Start all services (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

---

## Manual Deployment

### Backend Setup

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Start the backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm ci

# Development mode
npm run dev

# OR build for production
npm run build
npm start
```

### Combined Development Mode

Use the provided start script for local development:

```bash
./scripts/start.sh
```

This starts both backend and frontend with colored output and graceful shutdown on Ctrl+C.

---

## Production Configuration

### Environment Variables

Configure via `.env` file or system environment:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXUSOS_HOST` | `0.0.0.0` | Server bind address |
| `NEXUSOS_PORT` | `8000` | Server port |
| `NEXUSOS_LOG_LEVEL` | `info` | Log level (debug, info, warning, error) |
| `NEXUSOS_CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `NEXUSOS_GOVERNANCE_MODE` | `strict` | Governance mode (strict, permissive) |

### Production Checklist

1. **CORS Origins** - Restrict `NEXUSOS_CORS_ORIGINS` to your actual frontend domain
2. **Governance Policies** - Replace the default allow-all policy with restrictive policies
3. **TLS Termination** - Place behind a reverse proxy (nginx, Caddy, Traefik) with TLS
4. **Log Level** - Set to `warning` or `error` for production
5. **Resource Limits** - Configure Docker memory and CPU limits
6. **Secrets Management** - Use Docker secrets or environment variable injection

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 443 ssl;
    server_name nexusos.example.com;

    ssl_certificate /etc/ssl/certs/nexusos.crt;
    ssl_certificate_key /etc/ssl/private/nexusos.key;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring

### Health Endpoint

The primary health endpoint is `GET /api/status` which returns component-level health:

```bash
curl http://localhost:8000/api/status | python3 -m json.tool
```

### Telemetry Endpoints

- `GET /api/telemetry/health` - Component health states
- `GET /api/telemetry/metrics` - Collected metrics
- `GET /api/telemetry/status` - Telemetry collector status
- `GET /api/telemetry/executions` - Execution metrics

### Docker Health Checks

The docker-compose configuration includes built-in health checks:

```bash
# Check service health via Docker
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' nexusos-backend-1
```

### Automated Health Monitoring

Use the provided health check script in cron or monitoring systems:

```bash
# Add to crontab for periodic checks
*/5 * * * * /path/to/nexusos/scripts/healthcheck.sh >> /var/log/nexusos-health.log 2>&1
```

---

## Troubleshooting

### Backend fails to start

- Verify Python dependencies: `pip install -r backend/requirements.txt`
- Check port availability: `lsof -i :8000`
- Review logs: `docker-compose logs backend`

### Frontend cannot connect to backend

- Ensure backend is healthy: `curl http://localhost:8000/api/status`
- Check CORS configuration in `.env`
- Verify network connectivity between containers

### Health check fails

- Check if the backend process is running
- Verify the port mapping is correct
- Ensure curl is available in the container (included in the Docker image)

### Governance denying all requests

- Review active policies: `curl http://localhost:8000/api/governance/status`
- Ensure at least one permissive policy is active for your use case
- Check `NEXUSOS_GOVERNANCE_MODE` environment variable
