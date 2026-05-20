# Contributing to NexusOS

Thank you for your interest in contributing to NexusOS. This guide covers the essentials.

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (optional, for full-stack testing)

### Getting Started

```bash
git clone https://github.com/ramvadlamudi22-dev/NexusOS.git
cd NexusOS
pip install -r backend/requirements.txt
cd frontend && npm ci && cd ..
```

### Running Locally

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
```

## Branch Naming

Use prefixed branch names:

- `feat/description` - new features
- `fix/description` - bug fixes
- `chore/description` - maintenance, tooling, docs

## Commit Messages

Use conventional commit format:

```
feat: add workflow retry logic
fix: correct governance check ordering
chore: update dependencies
docs: clarify deployment steps
refactor: simplify event bus internals
```

## Testing Requirements

All tests must pass before submitting a PR:

```bash
python -m pytest backend/tests/ -q
cd frontend && npm run build
```

Do not submit code that breaks existing tests.

## Governance-First Philosophy

NexusOS follows a governance-first approach:

- Every operation must be validated before execution
- All actions produce audit trails
- Deterministic, replayable, observable behavior
- No speculative autonomy or overengineering

When adding features, ensure they integrate with the governance engine.

## Pull Request Process

1. Create a branch from `main` using the naming convention above
2. Make focused, minimal changes
3. Ensure all tests pass locally
4. Write a clear PR description explaining what and why
5. Request review from a maintainer

## Code Style

- Follow existing patterns in the codebase
- Keep modules small and focused
- Prefer simplicity over abstraction
- Match the naming and formatting conventions already in use

## Questions?

Open an issue for discussion before starting large changes.
