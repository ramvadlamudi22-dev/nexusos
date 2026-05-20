# Production Hardening

**Workflow:** Deployment Verification  
**Objective:** Reliable execution under real-world conditions

---

## Operational Failure Map

| Failure Mode | Probability | Impact | Mitigation |
|-------------|-------------|--------|-----------|
| Target URL unreachable | Medium | Blocks entire workflow | Retry 3x with 5s backoff, then fail with clear error |
| Page load timeout | Medium | Blocks page verification | 30s timeout, retry once, capture partial screenshot |
| Element not found | High | False negative | Wait up to 10s, use multiple selector strategies |
| JavaScript error on page | High | May be expected | Classify errors (critical vs. warning), configurable threshold |
| Network intermittent | Low | Flaky results | Retry individual checks, not entire workflow |
| Screenshot capture fails | Low | Missing proof | Retry once, continue workflow, flag in report |
| Video recording fails | Low | Missing proof | Continue without video, flag in report |
| API returns unexpected status | Medium | Verification failure | Distinguish between "API broken" and "wrong expectation" |
| Docker container OOM | Very Low | Workflow crash | Memory limits + graceful degradation |
| Playwright browser crash | Very Low | Workflow crash | Catch, restart browser, retry from last checkpoint |

---

## Stabilization Checklist

### Selector Stability
- [ ] Use `data-testid` attributes where available
- [ ] Fall back to role-based selectors (`getByRole`)
- [ ] Fall back to text content selectors (`getByText`)
- [ ] Never rely on CSS class names (too fragile)
- [ ] Never rely on DOM position (changes with layout)

### Timing Stability
- [ ] Always use `waitForSelector` or `waitForLoadState` before actions
- [ ] Never use fixed `delay()` as primary wait strategy
- [ ] Use `networkidle` for page load completion
- [ ] Set explicit timeouts on every operation
- [ ] Record actual timing for baseline comparison

### Retry Logic
- [ ] API checks: retry 3x with exponential backoff (1s, 2s, 4s)
- [ ] Page navigation: retry 2x with 5s delay
- [ ] Screenshot capture: retry 1x immediately
- [ ] Video recording: no retry (start fresh session)
- [ ] Element wait: built-in Playwright auto-wait (30s max)

### Artifact Verification
- [ ] Every screenshot file exists and is >0 bytes
- [ ] Every screenshot is valid PNG (check magic bytes)
- [ ] Video file exists and is >0 bytes after session close
- [ ] Trace file exists and is valid ZIP
- [ ] Report JSON is valid and contains all required fields
- [ ] All artifact checksums computed and stored

---

## Deterministic Execution Plan

### Input Contract

```typescript
interface VerificationConfig {
  // Target
  target_url: string;              // Base URL to verify
  api_base_url: string;            // API endpoint base
  
  // Pages to verify
  pages: PageCheck[];
  
  // APIs to verify
  api_checks: ApiCheck[];
  
  // Behavior
  viewport: { width: number; height: number };
  timeout_ms: number;              // Per-operation timeout
  max_retries: number;
  screenshot_on_failure: boolean;
  video_recording: boolean;
  trace_recording: boolean;
  
  // Thresholds
  max_console_errors: number;      // 0 = strict, -1 = ignore
  max_page_load_ms: number;        // Performance threshold
  required_api_status: number;     // Expected status (usually 200)
}

interface PageCheck {
  path: string;                    // URL path (appended to target_url)
  name: string;                    // Human-readable name
  expected_title: string | null;   // Page title check
  expected_elements: string[];     // Selectors that must exist
  max_load_ms: number;
}

interface ApiCheck {
  path: string;                    // API path
  method: "GET" | "POST";
  expected_status: number;
  expected_fields: string[];       // Top-level JSON fields
  max_response_ms: number;
}
```

### Output Contract

```typescript
interface VerificationResult {
  // Summary
  verdict: "PASS" | "FAIL" | "DEGRADED";
  score: number;                   // 0-100
  duration_ms: number;
  timestamp: string;
  
  // Details
  pages: PageResult[];
  apis: ApiResult[];
  console_errors: ConsoleError[];
  
  // Artifacts
  screenshots: string[];           // File paths
  video: string | null;
  trace: string | null;
  
  // Proof
  proof_manifest: ProofManifest;
  execution_id: string;
  checksum: string;
}
```

### Execution Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| Same config → same verdict (given same target state) | Deterministic selectors + fixed viewport |
| Every page produces a screenshot | Capture even on failure (error state screenshot) |
| Every API check produces a result | Timeout produces explicit TIMEOUT result |
| Video covers entire session | Start recording before first navigation |
| Report always generated | Even on partial failure, report what succeeded |
| Artifacts always checksummed | SHA-256 computed on every file |
| Execution always audited | Governance validates, audit records created |

---

## Runtime Health Verification

Before starting the verification workflow, validate NexusOS itself:

```
Pre-flight checks:
  1. Backend API responds (GET /api/health → HEALTHY)
  2. All 9 subsystems healthy
  3. Governance engine active
  4. Browser runtime available (Chromium accessible)
  5. Sufficient disk space for artifacts
  6. Target URL is DNS-resolvable
```

If pre-flight fails → abort with diagnostic report (don't produce false results).

---

## Error Classification

| Error Type | Severity | Action |
|-----------|----------|--------|
| Target unreachable | CRITICAL | Abort, report infrastructure failure |
| Page 404 | CRITICAL | Fail page check, continue others |
| Page 500 | CRITICAL | Fail page check, capture error screenshot |
| Slow page load (>threshold) | WARNING | Pass with degraded score |
| Console error (TypeError, etc.) | WARNING | Record, reduce score |
| Console error (network) | INFO | Record, don't reduce score |
| Missing expected element | FAIL | Fail page check |
| API wrong status | FAIL | Fail API check |
| API slow response | WARNING | Pass with degraded score |
| Screenshot failed | WARNING | Continue, flag in report |
