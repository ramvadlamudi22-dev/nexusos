# Zero-Config Runtime

**Objective:** A new operator executes NexusOS with one command and zero manual configuration.

---

## One-Command Startup

### Docker (Recommended)

```bash
docker compose up -d
```

That's it. Backend starts, waits for health, frontend starts, system is operational in ~25 seconds.

### Local Development

```powershell
# Windows
.\scripts\start-windows.ps1

# Linux/Mac
./scripts/start.sh
```

### Verification Workflow (the product)

```bash
npx nexusos-verify --url https://your-app.com
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://your-app.com"}'
```

---

## Automatic Dependency Validation

On startup, NexusOS validates all dependencies before accepting work:

```
┌─────────────────────────────────────────────────────────┐
│  Startup Validation Sequence                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Python runtime                                      │
│     ✓ Version >= 3.12                                   │
│     ✓ Required packages installed                       │
│                                                         │
│  2. Node.js runtime                                     │
│     ✓ Version >= 20                                     │
│     ✓ npm available                                     │
│     ✓ Frontend dependencies installed                   │
│                                                         │
│  3. Playwright browser                                  │
│     ✓ Chromium installed                                │
│     ✓ FFmpeg available (for video)                      │
│                                                         │
│  4. Network                                             │
│     ✓ Port 8000 available (backend)                     │
│     ✓ Port 3000 available (frontend)                    │
│                                                         │
│  5. Storage                                             │
│     ✓ artifacts/ directory writable                     │
│     ✓ Sufficient disk space (>100MB)                    │
│                                                         │
│  If any check fails:                                    │
│     → Print clear error message                         │
│     → Suggest fix command                               │
│     → Exit with non-zero code                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Service Health Verification

After startup, continuous health verification:

```typescript
interface HealthGate {
  // Must pass before accepting verification requests
  checks: [
    { name: "backend_api", endpoint: "/api/health", expected: "HEALTHY" },
    { name: "governance_active", endpoint: "/api/governance/status", field: "active", expected: true },
    { name: "browser_available", check: "chromium_binary_exists" },
    { name: "frontend_serving", endpoint: "http://localhost:3000", expected_status: 200 },
  ];
  
  // Retry until all pass or timeout
  max_wait_ms: 30000;
  check_interval_ms: 1000;
}
```

---

## Environment Verification

```typescript
interface EnvironmentCheck {
  // Auto-detected, no manual config needed
  python_path: string;           // Found via PATH or .codex_pydeps
  node_path: string;             // Found via PATH
  chromium_path: string;         // Found via ms-playwright or system
  ffmpeg_path: string;           // Found via ms-playwright
  
  // Defaults (override via .env only if needed)
  backend_port: 8000;
  frontend_port: 3000;
  cors_origins: "*";             // Development default
  governance_mode: "permissive"; // Development default
}
```

### Auto-Detection Logic

```
1. Check standard PATH for python/node
2. Check .codex_pydeps/bin/ for uvicorn (Codex environment)
3. Check $LOCALAPPDATA/ms-playwright/ for Chromium
4. Check node_modules/.bin/ for local Playwright
5. Fall back to Docker if nothing found locally
```

---

## Startup Diagnostics

If startup fails, produce a diagnostic report:

```
╔══════════════════════════════════════════════╗
║  NexusOS Startup Diagnostic                  ║
╚══════════════════════════════════════════════╝

  Python:     ✗ NOT FOUND
              Fix: Install Python 3.12+ or use Docker

  Node.js:    ✓ v20.11.0
  Chromium:   ✓ 148.0.7778.96
  Port 8000:  ✓ Available
  Port 3000:  ✗ IN USE (PID 1234)
              Fix: Kill process on port 3000 or set FRONTEND_PORT=3001

  Recommendation: Use 'docker compose up -d' for zero-config startup
```

---

## Configuration Hierarchy

```
1. Defaults (built into code)           ← Always present
2. .env file (project root)             ← Optional overrides
3. Environment variables                ← Runtime overrides
4. CLI arguments                        ← Per-invocation overrides
```

No configuration file is required. Everything has sensible defaults.

---

## Quick Start for New Operators

```
Step 1: Clone the repository
Step 2: docker compose up -d
Step 3: Open http://localhost:3000
Step 4: Run a verification:
        curl -X POST http://localhost:8000/api/verify \
          -d '{"target_url": "https://example.com"}'
Step 5: View results in dashboard or artifacts/ directory
```

Total time from clone to first verification: **< 2 minutes** (with Docker).
