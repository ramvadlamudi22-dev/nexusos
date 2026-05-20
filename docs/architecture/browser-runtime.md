# Browser Runtime

**Module:** `nexusos.browser`  
**Status:** Architecture Specification  
**Principle:** Browser-native autonomous execution with deterministic replay

---

## Overview

The Browser Runtime evolves Playwright MCP into a governed browser-native execution layer. It provides autonomous browser workflows with video recording, trace capture, accessibility snapshots, and deterministic replay. Every browser action is governed, recorded, and reproducible.

---

## Browser Execution Session

```
┌─────────────────────────────────────────────────────────┐
│                  BrowserExecutionSession                  │
├─────────────────────────────────────────────────────────┤
│  id: string (deterministic)                              │
│  state: INITIALIZING | ACTIVE | PAUSED | COMPLETED |     │
│         ERROR | REPLAYING                                │
│  url: string                                             │
│  viewport: {width, height}                               │
│  recording: BrowserRecording                             │
│  video_path: string                                      │
│  trace_path: string                                      │
│  screenshots: Screenshot[]                               │
│  dom_snapshots: DOMSnapshot[]                            │
│  network_log: NetworkEntry[]                             │
│  accessibility_tree: AccessibilitySnapshot[]             │
│  governance_decisions: Decision[]                        │
│  telemetry: SessionTelemetry                             │
└─────────────────────────────────────────────────────────┘
```

---

## Playwright Orchestration Layer

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │            NexusOS Browser Runtime                 │ │
│  │                                                   │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │ │
│  │  │Governance│  │ Replay  │  │   Telemetry     │  │ │
│  │  │  Gate   │  │Recorder │  │   Collector     │  │ │
│  │  └────┬────┘  └────┬────┘  └────────┬────────┘  │ │
│  │       │             │                │           │ │
│  │       ▼             ▼                ▼           │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │         Session Manager                     │ │ │
│  │  │  create | execute | screenshot | close      │ │ │
│  │  └──────────────────────┬──────────────────────┘ │ │
│  │                         │                         │ │
│  └─────────────────────────┼─────────────────────────┘ │
│                            │                            │
│  ┌─────────────────────────┼─────────────────────────┐ │
│  │                  Playwright API                    │ │
│  │                                                   │ │
│  │  Browser Context (video + tracing enabled)        │ │
│  │  Page (actions, screenshots, evaluate)            │ │
│  │  Network (request interception, logging)          │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │                  Chromium                          │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Browser Action Types

```
┌────────────────────────────────────────────────────────┐
│  NAVIGATE    │ Go to URL (governance-validated)         │
│  CLICK       │ Click element by selector/ref            │
│  TYPE        │ Type text into element                   │
│  SCREENSHOT  │ Capture viewport or element              │
│  EVALUATE    │ Execute JavaScript in page context       │
│  WAIT        │ Wait for selector/text/time              │
│  SCROLL      │ Scroll to element or position            │
│  SELECT      │ Select option in dropdown                │
│  UPLOAD      │ Upload file (governance-gated)           │
│  DOWNLOAD    │ Download file (governance-gated)         │
│  SNAPSHOT    │ Capture accessibility tree               │
│  NETWORK     │ Capture network requests                 │
└────────────────────────────────────────────────────────┘
```

---

## Video Recording Architecture

```
Session Start
    │
    ├── Playwright context created with recordVideo
    │   └── Video file: {session_id}.webm (VP8, 1920x1080)
    │
    ├── Tracing started (screenshots + snapshots)
    │   └── Trace file: {session_id}.zip
    │
    ├── Actions executed (each recorded)
    │   ├── Screenshot before action (optional)
    │   ├── Action execution
    │   ├── Screenshot after action (optional)
    │   └── DOM snapshot (optional)
    │
    └── Session End
        ├── Tracing stopped → trace.zip saved
        ├── Video finalized → video.webm saved
        ├── Artifacts indexed
        └── Replay manifest generated
```

---

## Browser Telemetry

```
┌─────────────────────────────────────────────────────────┐
│                  SessionTelemetry                         │
├─────────────────────────────────────────────────────────┤
│  actions_executed: number                                │
│  actions_failed: number                                  │
│  screenshots_captured: number                            │
│  navigation_count: number                                │
│  total_duration_ms: number                               │
│  network_requests: number                                │
│  network_errors: number                                  │
│  page_load_times: number[] (ms)                          │
│  dom_mutations: number                                   │
│  javascript_errors: string[]                             │
└─────────────────────────────────────────────────────────┘
```

---

## Deterministic Browser Replay

To replay a browser session:

1. Create new browser context with recorded viewport
2. Inject recorded time source into execution context
3. For each recorded action:
   - Validate governance (same policy → same decision)
   - Execute action with same parameters
   - Compare result to recorded result
   - Capture screenshot and compare (visual diff)
4. Generate replay verification report

### Visual Diff

Screenshots during replay are compared pixel-by-pixel to originals:
- Match threshold: 99.5% pixel similarity
- Allowed variance: anti-aliasing, font rendering
- Failure: structural layout changes

---

## Execution Proofs

Every browser session produces execution proofs:

```json
{
  "proof_type": "BROWSER_EXECUTION",
  "session_id": "sess-abc123",
  "timestamp": "2026-05-19T18:00:00Z",
  "actions_count": 15,
  "artifacts": {
    "video": "videos/sess-abc123.webm",
    "trace": "traces/sess-abc123.zip",
    "screenshots": ["snap-001.png", "snap-002.png"],
    "accessibility": ["a11y-001.json"]
  },
  "governance_decisions": 15,
  "all_permitted": true,
  "checksum": "SHA-256 of all artifact hashes concatenated"
}
```

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| BrowserSession | `BrowserSession` (backend/browser/models.py) |
| Session lifecycle | `BrowserRuntime` (backend/browser/runtime.py) |
| Action execution | `execute_action()` method |
| Screenshot capture | `capture_screenshot()` method |
| Recording | `session.recording` list |
| Governance validation | `ExecutionGovernanceValidator.validate_browser_action()` |
| Telemetry | `ExecutionTelemetryCollector.record_browser_trace()` |
| Replay | `ExecutionReplayManager.record_browser_session()` |
| Playwright video | `scripts/record-final.js` (Node.js Playwright API) |

Evolution extends with: real Playwright integration in Python backend, video recording per session, trace capture, accessibility snapshots, visual diff replay, and execution proofs.
