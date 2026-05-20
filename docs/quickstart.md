# 5-Minute Quickstart

Get NexusOS running in under 5 minutes.

## Prerequisites

You need one of:
- **Docker + Docker Compose** (Option A - recommended)
- **Python 3.9+ and Node.js 18+** (Option B - manual)

## Option A: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/ramvadlamudi22-dev/NexusOS.git
cd NexusOS

# 2. Copy environment config
cp .env.example .env

# 3. Start all services
docker-compose up
```

That's it. Backend runs at `http://localhost:8000`, frontend at `http://localhost:3000`.

## Option B: Manual Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/ramvadlamudi22-dev/NexusOS.git
cd NexusOS

# 2. Copy environment config
cp .env.example .env

# 3. Install and start the backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

# 4. Install and start the frontend
cd frontend
npm ci
npm run dev &
cd ..
```

## Verify

```bash
curl http://localhost:8000/api/status
```

Expected response:

```json
{
  "status": "operational",
  "components": { ... }
}
```

## Execute a Demo Workflow

```bash
curl -X POST http://localhost:8000/api/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "quickstart-demo",
    "steps": [
      {
        "id": "step-1",
        "step_type": "SKILL",
        "config": {"skill_name": "echo", "parameters": {"message": "NexusOS is running!"}},
        "depends_on": []
      }
    ]
  }'
```

## Open the Dashboard

Navigate to [http://localhost:3000](http://localhost:3000) in your browser to see the monitoring dashboard with real-time telemetry and workflow status.

## Next Steps

- Read the [Onboarding Guide](onboarding.md) for a full developer walkthrough
- Explore the [API Reference](api.md) for all available endpoints
- Check out the [demo workflows](../demos/) for more examples
- See [Deployment Guide](deployment.md) for production setup
