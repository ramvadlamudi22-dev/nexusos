# Execution Dashboard

**Objective:** Clear operational visibility for verification workflows.

---

## Dashboard Redesign Priorities

The current dashboard shows system internals (subsystem health, event bus state). For productization, the dashboard should show **workflow results** — what operators care about.

### Current State (Developer-Focused)
- 9 subsystem health indicators
- Raw telemetry counters
- Event stream (internal events)
- Governance policy list

### Target State (Operator-Focused)
- Recent verification runs (pass/fail/score)
- Screenshot gallery from latest run
- API health summary
- Quick-start verification button
- Artifact access (download reports, videos)

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  NexusOS │ Verifications │ Artifacts │ Settings              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  System Status: ● HEALTHY    Last run: 2m ago ✅     │   │
│  │  Runs today: 12    Pass rate: 100%    Avg: 45s      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Recent Verifications                                │   │
│  │                                                     │   │
│  │  ✅ app.example.com    2m ago     95/100   [View]   │   │
│  │  ✅ api.example.com    15m ago    100/100  [View]   │   │
│  │  ⚠️ staging.example.com 1h ago    72/100   [View]   │   │
│  │  ✅ app.example.com    2h ago     98/100   [View]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────┐   │
│  │  Latest Screenshots  │  │  Quick Actions           │   │
│  │                      │  │                          │   │
│  │  [thumb] [thumb]     │  │  [▶ Run Verification]    │   │
│  │  [thumb] [thumb]     │  │  [📋 View Last Report]   │   │
│  │                      │  │  [🎬 Watch Last Video]   │   │
│  └──────────────────────┘  │  [📦 Download Artifacts] │   │
│                             └──────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Runtime Health (collapsed by default)               │   │
│  │  ▸ 9/9 subsystems healthy                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Views

### 1. Verification Run Detail

```
┌─────────────────────────────────────────────────────────────┐
│  Verification: app.example.com                               │
│  Date: 2026-05-20 10:00 UTC │ Score: 95/100 │ ✅ PASS       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pages (3/3 passed)                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /          │ ✅ 1.2s │ 0 errors │ [Screenshot]   │    │
│  │  /dashboard │ ✅ 2.1s │ 0 errors │ [Screenshot]   │    │
│  │  /settings  │ ✅ 0.8s │ 0 errors │ [Screenshot]   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  APIs (2/2 passed)                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /api/health │ 200 │ 45ms                          │    │
│  │  /api/users  │ 200 │ 120ms                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Artifacts                                                  │
│  [📸 Screenshots (3)] [🎬 Video] [📊 Trace] [📄 Report]   │
│                                                             │
│  Proof Manifest: verify-2026-05-20-001.json [Download]      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Screenshot Gallery

```
┌─────────────────────────────────────────────────────────────┐
│  Screenshots: app.example.com (2026-05-20)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │              │  │              │  │              │     │
│  │  Homepage    │  │  Dashboard   │  │  Settings    │     │
│  │              │  │              │  │              │     │
│  │  1.2s ✅    │  │  2.1s ✅    │  │  0.8s ✅    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  Compare with previous run: [Select run ▾]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Artifact Browser

```
┌─────────────────────────────────────────────────────────────┐
│  Artifacts │ Filter: [All types ▾] [Last 7 days ▾]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📁 verify-2026-05-20-001/                                  │
│     📸 homepage.png (87 KB)              [View] [Download]  │
│     📸 dashboard.png (125 KB)            [View] [Download]  │
│     🎬 walkthrough.webm (1.5 MB)         [Play] [Download]  │
│     📊 execution-trace.zip (5 MB)        [Open] [Download]  │
│     📄 report.json                       [View] [Download]  │
│     🔒 manifest.json                     [Verify] [Download]│
│                                                             │
│  📁 verify-2026-05-19-003/                                  │
│     ...                                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Usability Improvements

| Current Issue | Fix |
|--------------|-----|
| Dashboard shows raw subsystem names | Show human-readable labels |
| No clear call-to-action | Add "Run Verification" button |
| Artifacts scattered in file system | Add artifact browser in dashboard |
| No run history | Add verification run list with status |
| Telemetry is raw counters | Show meaningful summaries (pass rate, avg time) |
| No screenshot preview | Add thumbnail gallery |
| Video requires file download | Add in-browser video player |
| Report is JSON | Add formatted report view |

---

## Implementation Priority

| Priority | Change | Effort |
|----------|--------|--------|
| 1 | Add verification run list to dashboard | Small |
| 2 | Add "Run Verification" button with config form | Medium |
| 3 | Add screenshot gallery view | Small |
| 4 | Add artifact browser | Medium |
| 5 | Add run detail view (pages + APIs + score) | Medium |
| 6 | Collapse system internals (health, events) | Small |
| 7 | Add video player | Small |
| 8 | Add proof manifest verification UI | Small |
