# Failure Intelligence Engine

**Module:** `nexusos.runtime.failure_intelligence`  
**Principle:** Failures are data. Classify, learn, prevent.

---

## Failure Classification

Every failure is classified along three axes:

| Axis | Values | Purpose |
|------|--------|---------|
| **Origin** | BROWSER, NETWORK, API, RUNTIME, ENVIRONMENT, CONFIG | Where it happened |
| **Severity** | TRANSIENT, DEGRADED, HARD, FATAL | How bad it is |
| **Recoverability** | AUTO_RETRY, ADAPTIVE, MANUAL, UNRECOVERABLE | What to do |

### Classification Matrix

```
┌────────────────────────────────────────────────────────────────┐
│ Failure                    │ Origin      │ Severity  │ Recovery │
├────────────────────────────┼─────────────┼───────────┼──────────┤
│ Page load timeout          │ NETWORK     │ TRANSIENT │ AUTO     │
│ Element not found          │ BROWSER     │ DEGRADED  │ ADAPTIVE │
│ API 500 response           │ API         │ HARD      │ AUTO     │
│ API connection refused     │ NETWORK     │ HARD      │ AUTO     │
│ Browser crash              │ RUNTIME     │ FATAL     │ ADAPTIVE │
│ Chromium not installed     │ ENVIRONMENT │ FATAL     │ MANUAL   │
│ Port already in use        │ ENVIRONMENT │ HARD      │ MANUAL   │
│ DNS resolution failure     │ NETWORK     │ TRANSIENT │ AUTO     │
│ TLS certificate error      │ NETWORK     │ HARD      │ MANUAL   │
│ Out of memory              │ RUNTIME     │ FATAL     │ ADAPTIVE │
│ Disk full                  │ ENVIRONMENT │ HARD      │ MANUAL   │
│ Session state corrupted    │ RUNTIME     │ DEGRADED  │ ADAPTIVE │
│ Selector changed (layout)  │ BROWSER     │ DEGRADED  │ ADAPTIVE │
│ Rate limited (429)         │ API         │ TRANSIENT │ AUTO     │
│ Auth token expired         │ API         │ TRANSIENT │ AUTO     │
│ IP blocked/banned          │ NETWORK     │ HARD      │ MANUAL   │
│ Governance policy denied   │ RUNTIME     │ HARD      │ MANUAL   │
│ Timeout (operation)        │ RUNTIME     │ TRANSIENT │ AUTO     │
│ Video recording failed     │ RUNTIME     │ DEGRADED  │ ADAPTIVE │
│ Screenshot capture failed  │ BROWSER     │ TRANSIENT │ AUTO     │
└────────────────────────────┴─────────────┴───────────┴──────────┘
```

---

## Retry Intelligence

Not all failures should be retried the same way:

```typescript
interface RetryDecision {
  should_retry: boolean;
  strategy: RetryStrategy;
  delay_ms: number;
  max_attempts: number;
  context_change: ContextChange | null;  // Modify something before retry
}

type RetryStrategy = 
  | "IMMEDIATE"          // Retry now (transient glitch)
  | "BACKOFF"            // Exponential backoff (rate limit, load)
  | "FRESH_SESSION"      // New browser context (session corruption)
  | "ALTERNATE_SELECTOR" // Try different selector (layout change)
  | "REDUCED_SCOPE"      // Skip non-critical parts (partial degradation)
  | "DEFERRED"           // Queue for later (environment issue)
  | "ABORT"              // Don't retry (unrecoverable)
```

### Decision Tree

```
Failure detected
    │
    ├── Is it TRANSIENT?
    │   ├── Yes → IMMEDIATE retry (max 3, 1s backoff)
    │   └── No ↓
    │
    ├── Is it NETWORK-origin?
    │   ├── DNS/timeout → BACKOFF retry (max 3, exponential 2s/4s/8s)
    │   ├── Rate limited → BACKOFF retry (respect Retry-After header)
    │   ├── Connection refused → BACKOFF retry (max 5, 5s/10s/20s/40s/60s)
    │   └── IP blocked → ABORT (manual intervention)
    │
    ├── Is it BROWSER-origin?
    │   ├── Element not found → ALTERNATE_SELECTOR (try 3 strategies)
    │   ├── Browser crash → FRESH_SESSION (restart browser)
    │   └── Screenshot failed → IMMEDIATE retry (max 1)
    │
    ├── Is it API-origin?
    │   ├── 500 → BACKOFF retry (max 3, 2s/4s/8s)
    │   ├── 401/403 → ABORT (auth issue, manual)
    │   ├── 404 → ABORT (endpoint doesn't exist)
    │   └── 429 → BACKOFF (respect rate limit)
    │
    └── Is it RUNTIME/ENVIRONMENT?
        ├── OOM → FRESH_SESSION (reduced scope)
        ├── Disk full → ABORT (manual)
        ├── Port conflict → ABORT (manual)
        └── Session corrupt → FRESH_SESSION
```

---

## Environment Diagnostics

Before execution, diagnose the environment:

```typescript
interface EnvironmentDiagnostic {
  timestamp: string;
  
  // System resources
  memory_available_mb: number;
  disk_available_mb: number;
  cpu_load_percent: number;
  
  // Network
  dns_resolution_ms: number;       // Time to resolve target hostname
  target_reachable: boolean;       // TCP connect to target
  target_latency_ms: number;       // Round-trip time
  
  // Runtime
  chromium_available: boolean;
  chromium_version: string;
  ffmpeg_available: boolean;
  backend_healthy: boolean;
  frontend_healthy: boolean;
  
  // Ports
  port_8000_available: boolean;
  port_3000_available: boolean;
  
  // Verdict
  ready: boolean;
  blockers: string[];              // What prevents execution
  warnings: string[];              // What might cause issues
}
```

---

## Runtime Anomaly Detection

Detect anomalies by comparing current execution to baseline:

```typescript
interface AnomalyDetector {
  // Baseline (computed from successful runs)
  baseline: {
    avg_page_load_ms: number;
    avg_api_response_ms: number;
    avg_screenshot_size_bytes: number;
    expected_element_count: number;
    expected_console_errors: number;
  };
  
  // Thresholds
  thresholds: {
    page_load_slow: 3.0;           // 3x baseline = anomaly
    api_response_slow: 5.0;        // 5x baseline = anomaly
    screenshot_size_drift: 0.5;    // 50% size change = anomaly
    unexpected_errors: 1;          // Any new error type = anomaly
  };
  
  // Detection
  detect(current: ExecutionMetrics): Anomaly[];
}

interface Anomaly {
  type: "PERFORMANCE" | "CONTENT" | "ERROR" | "BEHAVIOR";
  metric: string;
  expected: number;
  actual: number;
  deviation_factor: number;
  severity: "INFO" | "WARNING" | "CRITICAL";
}
```

---

## Session Corruption Detection

Detect when browser session state becomes unreliable:

| Signal | Indicates | Action |
|--------|-----------|--------|
| Page URL doesn't match expected | Navigation failed silently | Retry navigation |
| DOM empty after load | Page didn't render | Fresh session |
| Cookie count = 0 unexpectedly | Session cleared | Restore session |
| localStorage inaccessible | Context corrupted | Fresh session |
| Network requests hanging | Connection pool exhausted | Fresh session |
| JavaScript errors spike | Page in bad state | Fresh session |
| Screenshots are blank/black | Renderer crashed | Restart browser |

---

## IP/Runtime Instability Detection

```typescript
interface StabilityMonitor {
  // Track consecutive failures from same origin
  failure_streak: Map<FailureOrigin, number>;
  
  // Detect patterns
  patterns: {
    rate_limit_detected: boolean;    // Multiple 429s
    ip_block_suspected: boolean;     // Consistent connection refused
    dns_instability: boolean;        // Intermittent resolution failures
    target_degraded: boolean;        // Elevated error rates from target
  };
  
  // Adaptive response
  adaptations: {
    increase_delays: boolean;        // Slow down requests
    rotate_user_agent: boolean;      // Change browser fingerprint
    reduce_parallelism: boolean;     // Fewer concurrent operations
    defer_execution: boolean;        // Wait and retry later
  };
}
```

---

## Failure Intelligence API

```
GET  /api/failures/recent              → Recent failures with classification
GET  /api/failures/patterns            → Detected failure patterns
GET  /api/failures/environment         → Current environment diagnostic
GET  /api/failures/anomalies           → Active anomalies
GET  /api/failures/stats               → Failure statistics (rates, types)
POST /api/failures/diagnose            → Run full diagnostic suite
```

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Error detection | Try/catch in route handlers | Add classification |
| Retry | Not implemented per-operation | New: RetryDecision engine |
| Environment check | Docker healthcheck | Add pre-flight diagnostics |
| Anomaly detection | Not implemented | New: baseline comparison |
| Session management | BrowserRuntime.start_session() | Add corruption detection |
| Health monitoring | RuntimeHealthMonitor | Extend with failure patterns |
