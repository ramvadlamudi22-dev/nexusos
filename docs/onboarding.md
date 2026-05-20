# Developer Onboarding Guide

Welcome to NexusOS! This guide walks you through setting up the project and making your first contribution.

## Prerequisites

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** (for the frontend)
- **Docker and Docker Compose** (for containerized development)
- **Git**

## Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ramvadlamudi22-dev/NexusOS.git
cd NexusOS

# Copy environment configuration
cp .env.example .env

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm ci
cd ..
```

## Understanding the Architecture

NexusOS uses a layered architecture built around the `RuntimeExecutionContext`, which provides deterministic timestamps and shared state to all modules.

Key components:
- **GovernanceEngine** - Validates every action before execution
- **EventBus** - Dispatches events across the system
- **TelemetryCollector** - Aggregates metrics and health data
- **ReplayRecorder** - Captures all operations for deterministic replay
- **WorkflowEngine** - Orchestrates multi-step operations

For detailed architecture diagrams and component descriptions, see [docs/architecture.md](architecture.md).

## Running the Backend

```bash
# Start the FastAPI backend with hot-reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/api/status
```

## Running the Frontend

```bash
# In a separate terminal
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

## Your First Workflow

Execute a simple two-step workflow using the API:

```bash
curl -X POST http://localhost:8000/api/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-workflow",
    "steps": [
      {
        "id": "step-1",
        "step_type": "SKILL",
        "config": {"skill_name": "echo", "parameters": {"message": "Hello from step 1"}},
        "depends_on": []
      },
      {
        "id": "step-2",
        "step_type": "SKILL",
        "config": {"skill_name": "echo", "parameters": {"message": "Hello from step 2"}},
        "depends_on": ["step-1"]
      }
    ]
  }'
```

## Viewing Results

Check workflow execution status:

```bash
# Replace {workflow_id} with the ID returned from the execute call
curl http://localhost:8000/api/workflow/{workflow_id}/status
```

You can also view execution results in the dashboard at `http://localhost:3000`.

## Running Tests

```bash
# Run the full test suite
python -m pytest backend/tests/ -q

# Run tests with verbose output
python -m pytest backend/tests/ -v

# Run a specific test file
python -m pytest backend/tests/test_workflow.py -v
```

## Making Your First Change

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes following the patterns in CLAUDE.md
3. Ensure governance validation is preserved for any new operations
4. Add tests for new functionality
5. Run the test suite to confirm nothing breaks

## Submitting a PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution workflow, including:
- Commit message conventions
- Code review process
- CI/CD checks that must pass
