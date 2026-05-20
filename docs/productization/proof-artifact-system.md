# Proof Artifact System

**Objective:** Every verification run produces tamper-evident, auditable proof artifacts.

---

## Proof Manifest

Every execution produces a single manifest that links all evidence:

```json
{
  "manifest_version": "1.0.0",
  "execution_id": "verify-2026-05-20-001",
  "timestamp": "2026-05-20T10:00:00Z",
  "target": "https://app.example.com",
  "verdict": "PASS",
  "score": 95,
  "duration_ms": 12500,
  
  "artifacts": [
    {
      "type": "screenshot",
      "name": "homepage.png",
      "path": "screenshots/homepage.png",
      "hash": "sha256:ab3f7c...",
      "size_bytes": 87000,
      "context": { "page": "/", "load_time_ms": 1200 }
    },
    {
      "type": "screenshot",
      "name": "dashboard.png",
      "path": "screenshots/dashboard.png",
      "hash": "sha256:cd91e2...",
      "size_bytes": 125000,
      "context": { "page": "/dashboard", "load_time_ms": 2100 }
    },
    {
      "type": "video",
      "name": "walkthrough.webm",
      "path": "videos/walkthrough.webm",
      "hash": "sha256:ef45a1...",
      "size_bytes": 1500000,
      "context": { "duration_ms": 12000, "resolution": "1920x1080" }
    },
    {
      "type": "trace",
      "name": "execution-trace.zip",
      "path": "traces/execution-trace.zip",
      "hash": "sha256:12bc34...",
      "size_bytes": 5000000,
      "context": { "spans": 45, "screenshots_in_trace": 8 }
    }
  ],
  
  "checks": {
    "pages": [
      { "path": "/", "status": "PASS", "load_ms": 1200, "errors": 0 },
      { "path": "/dashboard", "status": "PASS", "load_ms": 2100, "errors": 0 },
      { "path": "/settings", "status": "PASS", "load_ms": 800, "errors": 0 }
    ],
    "apis": [
      { "path": "/api/health", "status": 200, "response_ms": 45 },
      { "path": "/api/users", "status": 200, "response_ms": 120 }
    ],
    "console_errors": 0,
    "performance": { "avg_load_ms": 1367, "max_load_ms": 2100 }
  },
  
  "governance": {
    "decisions": 8,
    "all_permitted": true,
    "policy_id": "default-allow-all"
  },
  
  "integrity": {
    "manifest_hash": "sha256:combined-hash-of-all-artifact-hashes",
    "execution_checksum": "sha256:hash-of-execution-inputs"
  }
}
```

---

## Artifact Types

| Type | Format | Retention | Purpose |
|------|--------|-----------|---------|
| Screenshot | PNG | 90 days | Visual proof of page state |
| Video | WebM | 30 days | Walkthrough proof |
| Trace | ZIP | 14 days | Detailed execution replay |
| Report | JSON | 1 year | Structured verification result |
| Manifest | JSON | Forever | Proof chain anchor |
| Telemetry | JSON | 30 days | Performance evidence |
| Audit log | JSON | Forever | Governance decisions |

---

## Execution Evidence Pipeline

```
Verification Run
    │
    ├── 1. Pre-flight (health check)
    │       └── Artifact: preflight-report.json
    │
    ├── 2. Page checks (per page)
    │       ├── Artifact: screenshot-{page}.png
    │       ├── Artifact: page-result-{page}.json
    │       └── Artifact: console-log-{page}.json
    │
    ├── 3. API checks (per endpoint)
    │       └── Artifact: api-results.json
    │
    ├── 4. Video recording
    │       └── Artifact: walkthrough.webm
    │
    ├── 5. Trace capture
    │       └── Artifact: execution-trace.zip
    │
    ├── 6. Report compilation
    │       ├── Artifact: verification-report.json
    │       └── Artifact: proof-manifest.json
    │
    └── 7. Indexing
            └── All artifacts registered with hashes and lineage
```

---

## Reproducible Execution Records

Every run is reproducible:

```json
{
  "execution_record": {
    "id": "verify-2026-05-20-001",
    "config": { /* full VerificationConfig */ },
    "environment": {
      "nexusos_version": "0.2.0",
      "chromium_version": "148.0.7778.96",
      "viewport": { "width": 1920, "height": 1080 },
      "timestamp": "2026-05-20T10:00:00Z"
    },
    "inputs_hash": "sha256:config+environment hash",
    "outputs_hash": "sha256:all artifact hashes combined",
    "replay_available": true
  }
}
```

To reproduce: provide the same config + same target state → same results.

---

## Run Summaries

Human-readable summary for each run:

```markdown
# Verification Report: app.example.com
**Date:** 2026-05-20 10:00 UTC | **Verdict:** ✅ PASS | **Score:** 95/100

## Pages Verified (3/3 passed)
| Page | Status | Load Time | Errors |
|------|--------|-----------|--------|
| / | ✅ PASS | 1.2s | 0 |
| /dashboard | ✅ PASS | 2.1s | 0 |
| /settings | ✅ PASS | 0.8s | 0 |

## APIs Verified (2/2 passed)
| Endpoint | Status | Response Time |
|----------|--------|---------------|
| /api/health | 200 ✅ | 45ms |
| /api/users | 200 ✅ | 120ms |

## Artifacts
- 3 screenshots
- 1 video walkthrough (12s)
- 1 execution trace
- Proof manifest: verify-2026-05-20-001.json

## Integrity
All artifacts checksummed. Manifest hash: sha256:ab3f...
```

---

## Artifact Indexing

```
artifacts/
├── runs/
│   └── verify-2026-05-20-001/
│       ├── manifest.json              (proof manifest)
│       ├── report.json                (structured results)
│       ├── report.md                  (human-readable summary)
│       ├── screenshots/
│       │   ├── homepage.png
│       │   ├── dashboard.png
│       │   └── settings.png
│       ├── videos/
│       │   └── walkthrough.webm
│       ├── traces/
│       │   └── execution-trace.zip
│       └── telemetry/
│           └── metrics.json
└── index.json                         (all runs indexed)
```

---

## Integrity Verification

Anyone can verify a proof manifest:

```bash
# Verify all artifact hashes match
nexusos verify-proof ./artifacts/runs/verify-2026-05-20-001/manifest.json

# Output:
# ✓ homepage.png: hash matches (sha256:ab3f7c...)
# ✓ dashboard.png: hash matches (sha256:cd91e2...)
# ✓ walkthrough.webm: hash matches (sha256:ef45a1...)
# ✓ execution-trace.zip: hash matches (sha256:12bc34...)
# ✓ Manifest integrity: VALID
```

If any file has been modified after generation, verification fails.
