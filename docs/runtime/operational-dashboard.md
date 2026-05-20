# Operational Dashboard

**Module:** `nexusos.runtime.dashboard`  
**Principle:** Execution visibility drives operational confidence.

---

## Dashboard Purpose

The dashboard answers three questions:
1. **Is the system healthy?** (runtime state)
2. **Are workflows succeeding?** (execution results)
3. **What happened when something failed?** (failure visibility)

---

## Primary Views

### 1. Live Workflow State

```
┌─────────────────────────────────────────────────────────────┐
│  Active Workflows                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ● deploy-verify-001  │ RUNNING │ 3/5 nodes │ 8.2s elapsed │
│    ├── ✓ check-homepage (1.2s)                              │
│    ├── ✓ check-dashboard (2.1s)                             │
│    ├── ● check-settings (running...)                        │
│    ├── ○ check-apis (pending)                               │
│    └── ○ generate-report (pending)                          │
│                                                             │
│  Recent Completed                                           │
│  ✅ deploy-verify-000  │ PASS │ 95/100 │ 12.5s │ 2m ago    │
│  ✅ health-check-015   │ PASS │ 100/100 │ 3.2s │ 5m ago    │
│  ⚠️ deploy-verify-999  │ DEGRADED │ 72/100 │ 15.1s │ 1h ago │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Failure Visibility

```
┌─────────────────────────────────────────────────────────────┐
│  Recent Failures & Recoveries                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ 15m ago │ Page load timeout │ /dashboard │ RECOVERED    │
│     Strategy: BACKOFF retry (attempt 2/3 succeeded)         │
│     Duration: 6.2s │ Root cause: Target slow response       │
│                                                             │
│  ❌ 1h ago │ Element not found │ .nav-menu │ RECOVERED      │
│     Strategy: ALTERNATE_SELECTOR (role-based worked)        │
│     Duration: 2.1s │ Root cause: CSS class renamed          │
│                                                             │
│  ❌ 3h ago │ API 500 │ /api/users │ FAILED                  │
│     Strategy: BACKOFF retry (3/3 failed)                    │
│     Duration: 14s │ Root cause: Target backend error        │
│                                                             │
│  Recovery Success Rate (24h): 87% (13/15 recovered)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Replay Viewer

```
┌─────────────────────────────────────────────────────────────┐
│  Replay: deploy-verify-000                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Timeline: [====●=========================] 3.2s / 12.5s    │
│                                                             │
│  T+3.2s │ Node: check-dashboard │ RUNNING                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Screenshot at T+3.2s]                              │   │
│  │                                                     │   │
│  │  Dashboard page loaded                              │   │
│  │  Load time: 2.1s                                    │   │
│  │  Console errors: 0                                  │   │
│  │  Elements found: 12/12                              │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [◀ Prev] [▶ Next] [⏸ Pause] [⏭ End]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Artifact Explorer

```
┌─────────────────────────────────────────────────────────────┐
│  Artifacts │ Run: deploy-verify-000                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📸 Screenshots (3)                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐                       │
│  │homepage│  │dashbrd │  │settings│                        │
│  │  ✅    │  │  ✅    │  │  ✅    │                        │
│  └────────┘  └────────┘  └────────┘                       │
│                                                             │
│  🎬 Video: walkthrough.webm (1.5 MB) [▶ Play]              │
│  📊 Trace: execution-trace.zip (5 MB) [Open in Viewer]     │
│  📄 Report: verification-report.json [View]                 │
│  🔒 Proof: manifest.json [Verify Integrity]                 │
│                                                             │
│  Integrity: ✅ All checksums valid                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. Telemetry Graphs

```
┌─────────────────────────────────────────────────────────────┐
│  Execution Metrics (Last 24h)                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Success Rate          Avg Duration         Active Sessions │
│  ┌──────────────┐     ┌──────────────┐    ┌────────────┐  │
│  │     98%      │     │    12.5s     │    │     2      │  │
│  │  ████████░░  │     │  ▁▂▃▄▅▆▇█   │    │  ██░░░░░░  │  │
│  └──────────────┘     └──────────────┘    └────────────┘  │
│                                                             │
│  Workflows/Hour        Recovery Rate       Error Rate       │
│  ┌──────────────┐     ┌──────────────┐    ┌────────────┐  │
│  │     4.2      │     │    87%       │    │    2%      │  │
│  │  ▂▃▄▅▆▇█▇▆  │     │  ████████░░  │    │  ░░░░░░░█  │  │
│  └──────────────┘     └──────────────┘    └────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6. Recovery Visibility

```
┌─────────────────────────────────────────────────────────────┐
│  Self-Healing Activity                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Recovery Strategies Used (Last 24h)                        │
│  ├── AUTO_RETRY: 8 (7 succeeded, 1 failed)                 │
│  ├── BACKOFF: 4 (3 succeeded, 1 failed)                    │
│  ├── FRESH_SESSION: 2 (2 succeeded)                        │
│  ├── ALTERNATE_SELECTOR: 1 (1 succeeded)                   │
│  └── ORCHESTRATED: 0                                       │
│                                                             │
│  Mean Time to Recovery: 4.2s                                │
│  Longest Recovery: 14s (API retry exhausted)                │
│                                                             │
│  Failure Origins                                            │
│  ├── NETWORK: 45%                                          │
│  ├── BROWSER: 30%                                          │
│  ├── API: 20%                                              │
│  └── RUNTIME: 5%                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7. Orchestration Timelines

```
┌─────────────────────────────────────────────────────────────┐
│  Execution Timeline: deploy-verify-000                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0s    2s    4s    6s    8s    10s   12s                    │
│  ├─────┼─────┼─────┼─────┼─────┼─────┤                    │
│                                                             │
│  [GOV]─┐                                                   │
│  [init]═══╗                                                 │
│           ╠══[homepage]═══╗                                 │
│           ╠══[dashboard]════════╗                           │
│           ╠══[settings]══╗     ║                            │
│           ║              ╠═════╬══[apis]═╗                  │
│           ║              ║     ║         ╠══[report]═╗      │
│  [video]══╬══════════════╬═════╬═════════╬══════════╬═╗    │
│           ║              ║     ║         ║          ║ ║    │
│  ├─────┼─────┼─────┼─────┼─────┼─────┤                    │
│  0s    2s    4s    6s    8s    10s   12s                    │
│                                                             │
│  Critical path: init → dashboard → apis → report (10.2s)   │
│  Parallelism: 65% efficiency                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dashboard Data API

```
GET /api/dashboard/summary              → System health + recent runs
GET /api/dashboard/workflows/active     → Currently executing workflows
GET /api/dashboard/workflows/recent     → Recent completed workflows
GET /api/dashboard/failures/recent      → Recent failures + recoveries
GET /api/dashboard/telemetry/charts     → Time-series data for graphs
GET /api/dashboard/recovery/stats       → Recovery success rates
```

---

## Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| 1 | Workflow run list (pass/fail/score) | Small | High |
| 2 | Run detail view (nodes + artifacts) | Medium | High |
| 3 | Screenshot gallery | Small | Medium |
| 4 | Failure list with recovery status | Medium | High |
| 5 | Telemetry summary cards | Small | Medium |
| 6 | Artifact browser with download | Medium | Medium |
| 7 | Execution timeline visualization | Large | Medium |
| 8 | Replay viewer | Large | Low (for now) |

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| System health display | ✓ RuntimeHealth component | Working |
| Governance status | ✓ GovernanceStatus component | Working |
| Workflow display | ✓ WorkflowView component | Add run history |
| Event stream | ✓ EventStream component | Working |
| Telemetry display | ✓ TelemetryOverview component | Add charts |
| Screenshot display | Not in dashboard | New: gallery component |
| Artifact browser | Not in dashboard | New: file browser component |
| Failure visibility | Not in dashboard | New: failure list component |
| Timeline visualization | Not in dashboard | New: Gantt-style component |
