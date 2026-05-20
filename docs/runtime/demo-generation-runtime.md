# Demo Generation Runtime

**Module:** `nexusos.runtime.demo`  
**Version:** 2.0  
**Principle:** Demos are governed workflows that produce verifiable proof artifacts

---

## Design Intent

The Demo Generation Runtime treats demonstration as a first-class operational workflow. Demos are not ad-hoc scripts — they are execution graphs that produce screenshots, videos, traces, and proof manifests through governed browser automation. Every demo is reproducible, verifiable, and linked to the runtime state that produced it.

---

## Demo as Execution Graph

```typescript
interface DemoWorkflow extends ExecutionGraph {
  demo_metadata: {
    title: string;
    description: string;
    target_audience: string;
    expected_duration_ms: number;
    visual_quality: VisualQualityConfig;
  };
  
  // Demo-specific node types
  scenes: DemoScene[];
  transitions: SceneTransition[];
  
  // Output configuration
  output: {
    video: VideoConfig;
    screenshots: ScreenshotConfig;
    trace: boolean;
    proof_manifest: boolean;
  };
}

interface DemoScene {
  id: string;
  name: string;
  description: string;
  actions: DemoAction[];
  duration_ms: number;
  screenshot_points: string[];     // Action IDs to screenshot at
  narration: string | null;        // For future audio overlay
}

interface DemoAction {
  id: string;
  type: "NAVIGATE" | "SCROLL_TO" | "CLICK" | "WAIT" | 
        "SCREENSHOT" | "HIGHLIGHT" | "ANNOTATE";
  target: string;
  params: Record<string, unknown>;
  timing: {
    delay_before_ms: number;
    duration_ms: number;
    delay_after_ms: number;
  };
}
```

---

## Demo Orchestration Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Define  │───→│ Validate │───→│ Execute  │───→│ Produce  │
│          │    │          │    │          │    │          │
│ scenes   │    │ governance│   │ browser  │    │ video    │
│ actions  │    │ resources │   │ actions  │    │ screens  │
│ outputs  │    │ timing   │    │ capture  │    │ traces   │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                                      ▼
                                                ┌──────────┐
                                                │  Index   │
                                                │          │
                                                │ manifest │
                                                │ lineage  │
                                                │ proof    │
                                                └──────────┘
```

---

## Visual Quality Configuration

```typescript
interface VisualQualityConfig {
  viewport: { width: number; height: number };
  video_codec: "VP8" | "VP9" | "H264";
  video_format: "webm" | "mp4";
  screenshot_format: "png" | "jpeg";
  screenshot_quality: number;        // 0-100 for jpeg
  
  // Cinematic settings
  scroll_behavior: "smooth" | "instant";
  transition_delay_ms: number;       // Between scenes
  action_pacing_ms: number;          // Between actions
  page_load_wait: "networkidle" | "domcontentloaded" | "load";
  
  // Stability
  wait_for_animations: boolean;
  wait_for_fonts: boolean;
  disable_cursor_blink: boolean;
}
```

### Presets

| Preset | Viewport | Pacing | Use Case |
|--------|----------|--------|----------|
| CINEMATIC | 1920x1080 | 1200ms | YouTube-quality walkthroughs |
| STANDARD | 1440x900 | 800ms | Documentation screenshots |
| FAST | 1280x720 | 400ms | CI/CD validation |
| TEASER | 1920x1080 | 2000ms | Marketing teasers |

---

## Demo Catalog

```typescript
interface DemoCatalog {
  demos: DemoDefinition[];
  
  // Standard demos
  full_walkthrough: DemoWorkflow;      // Complete dashboard tour
  governance_showcase: DemoWorkflow;   // Policy engine demonstration
  telemetry_overview: DemoWorkflow;    // Observability features
  workflow_execution: DemoWorkflow;    // Orchestration demo
  replay_inspection: DemoWorkflow;     // Replay system demo
  runtime_health: DemoWorkflow;        // Health monitoring
  architecture_overview: DemoWorkflow; // Landing page tour
  short_teaser: DemoWorkflow;          // 30-second highlight
}
```

---

## Browser Automation Layer

```typescript
interface DemoBrowserSession {
  // Playwright context with recording
  context: BrowserContext;
  page: Page;
  
  // Recording state
  video_recording: boolean;
  trace_recording: boolean;
  screenshot_buffer: Screenshot[];
  
  // Demo execution
  async executeScene(scene: DemoScene): Promise<SceneResult>;
  async captureScreenshot(name: string): Promise<Artifact>;
  async scrollToSection(selector: string, text: string): Promise<void>;
  async waitForStability(): Promise<void>;
  
  // Lifecycle
  async start(config: VisualQualityConfig): Promise<void>;
  async finish(): Promise<DemoArtifactSet>;
}
```

---

## Artifact Production

Each demo execution produces:

```typescript
interface DemoArtifactSet {
  demo_id: string;
  execution_id: string;
  timestamp: string;
  
  video: {
    path: string;
    duration_ms: number;
    size_bytes: number;
    format: string;
    resolution: { width: number; height: number };
  } | null;
  
  trace: {
    path: string;
    size_bytes: number;
    spans_count: number;
    screenshots_in_trace: number;
  } | null;
  
  screenshots: {
    name: string;
    path: string;
    size_bytes: number;
    scene_id: string;
    action_id: string;
  }[];
  
  proof_manifest: ProofManifest;
  
  // Validation
  runtime_health_at_capture: HealthState;
  api_validation: { endpoint: string; status: number }[];
  console_errors: number;
}
```

---

## Demo Validation

After every demo execution:

```typescript
interface DemoValidation {
  // File existence
  video_exists: boolean;
  screenshots_exist: boolean;
  trace_exists: boolean;
  
  // Runtime health
  backend_healthy: boolean;
  frontend_healthy: boolean;
  apis_all_200: boolean;
  
  // Quality
  console_errors: number;
  video_duration_within_tolerance: boolean;
  all_scenes_completed: boolean;
  
  // Integrity
  artifact_checksums_valid: boolean;
  proof_manifest_valid: boolean;
  
  verdict: "PASS" | "FAIL" | "DEGRADED";
}
```

---

## Autonomous Demo Generation

The demo runtime can generate demos autonomously:

1. **Trigger:** Schedule, API call, or post-deployment hook
2. **Seed:** Generate runtime data (workflows, sessions, events)
3. **Execute:** Run demo workflow graph through browser
4. **Capture:** Record video, screenshots, traces
5. **Validate:** Verify all artifacts and runtime health
6. **Index:** Store artifacts with lineage and proof manifests
7. **Report:** Generate demo execution report

---

## Integration with Current Pipeline

| Component | Current Implementation | Role |
|-----------|----------------------|------|
| Playwright Node.js | `scripts/record-final.js` | Browser automation engine |
| Chromium | Installed at `ms-playwright/chromium-1223` | Browser binary |
| FFmpeg | Installed at `ms-playwright/ffmpeg-1011` | Video encoding |
| Video output | `artifacts/videos/*.webm` | Demo videos |
| Trace output | `artifacts/traces/*.zip` | Playwright traces |
| Screenshot output | `artifacts/snapshots/*.png` | Demo screenshots |
| Validation | API health checks + console error check | Post-demo verification |

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Demo execution | `scripts/record-final.js` | Formalize as execution graph |
| Video recording | Playwright recordVideo | Already working |
| Trace capture | Playwright tracing | Already working |
| Screenshots | page.screenshot() | Already working |
| Data seeding | fetch() to API endpoints | Already working |
| Validation | Health check + console check | Already working |
| Proof manifests | Markdown reports | Formalize as structured JSON |
| Demo catalog | Hardcoded in script | Extract as configuration |
