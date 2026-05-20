# Demo Execution Platform

**Objective:** Transform demos into reusable, deterministic operational demonstrations.

---

## Demo Runner Architecture

```typescript
interface DemoRunner {
  // Load a demo scenario
  load(scenario: DemoScenario): void;
  
  // Execute with recording
  execute(): Promise<DemoResult>;
  
  // Replay a previous execution
  replay(executionId: string): Promise<DemoResult>;
  
  // List available scenarios
  listScenarios(): DemoScenario[];
}

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  target_url: string;
  scenes: Scene[];
  quality: "CINEMATIC" | "STANDARD" | "FAST";
  expected_duration_ms: number;
}

interface Scene {
  id: string;
  name: string;
  actions: Action[];
  screenshot_at_end: boolean;
  narration: string;              // Description of what's shown
}
```

---

## Built-in Demo Scenarios

### 1. Full Dashboard Walkthrough
```yaml
id: full-walkthrough
name: NexusOS Dashboard Tour
duration: ~25s
scenes:
  - System banner (HEALTHY status)
  - Runtime health (9 subsystems)
  - Governance (active policies)
  - Telemetry (execution metrics)
  - Workflows (orchestration)
  - Replay (inspection interface)
  - Demo workflows (execution)
```

### 2. Governance Showcase
```yaml
id: governance-showcase
name: Governed Execution Demo
duration: ~15s
scenes:
  - Governance status (active engine)
  - Audit trail (checksummed records)
  - Policy enforcement (deny-by-default)
  - System banner (governance active)
```

### 3. Deployment Verification Demo
```yaml
id: deployment-verification
name: Post-Deploy Verification
duration: ~20s
scenes:
  - Target application loads
  - Pages verified with screenshots
  - APIs checked with status codes
  - Report generated with verdict
  - Proof manifest produced
```

### 4. Workflow Orchestration
```yaml
id: workflow-orchestration
name: DAG Workflow Execution
duration: ~15s
scenes:
  - Available workflows listed
  - Diamond workflow executed
  - Steps complete in dependency order
  - Results displayed
  - Telemetry updated
```

### 5. 30-Second Teaser
```yaml
id: teaser
name: NexusOS in 30 Seconds
duration: ~30s
scenes:
  - Quick dashboard scroll
  - Highlight: HEALTHY status
  - Highlight: Governance active
  - Highlight: Workflows executing
  - End on system banner
```

---

## Stable Browser Walkthroughs

### Stability Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| Same viewport every time | Fixed 1920x1080 |
| Same scroll positions | scrollIntoView with block:'start' |
| Same timing | Fixed delays between scenes |
| Same content | Seed data before recording |
| No flicker | Wait for networkidle + font load |
| No cursor artifacts | Headless mode |
| Clean state | Fresh browser context per demo |

### Anti-Flake Measures

```typescript
async function stableNavigation(page: Page, url: string): Promise<void> {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForLoadState('domcontentloaded');
  // Wait for any animations to settle
  await page.waitForTimeout(500);
  // Wait for fonts
  await page.evaluate(() => document.fonts.ready);
}

async function stableScroll(page: Page, selector: string, text: string): Promise<void> {
  await page.evaluate(({ s, t }) => {
    for (const el of document.querySelectorAll(s)) {
      if (el.textContent?.includes(t)) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }
  }, { s: selector, t: text });
  // Wait for scroll to complete
  await page.waitForTimeout(800);
}
```

---

## Reusable Scenario Playback

Scenarios are defined as JSON configuration, not code:

```json
{
  "id": "custom-verification",
  "name": "My App Verification",
  "target_url": "https://my-app.com",
  "quality": "STANDARD",
  "scenes": [
    {
      "id": "homepage",
      "actions": [
        { "type": "navigate", "url": "/" },
        { "type": "wait", "ms": 1500 },
        { "type": "screenshot", "name": "homepage" }
      ]
    },
    {
      "id": "login",
      "actions": [
        { "type": "navigate", "url": "/login" },
        { "type": "wait", "ms": 1000 },
        { "type": "screenshot", "name": "login-page" }
      ]
    }
  ]
}
```

Operators define scenarios once, execute them repeatedly.

---

## Auto-Generated Demo Reports

After every demo execution:

```markdown
# Demo Execution Report

**Scenario:** Full Dashboard Walkthrough
**Executed:** 2026-05-20 10:00 UTC
**Duration:** 24.8s
**Status:** ✅ COMPLETE

## Scenes Executed
| # | Scene | Duration | Screenshot |
|---|-------|----------|-----------|
| 1 | System Banner | 1.5s | ✓ |
| 2 | Runtime Health | 1.2s | ✓ |
| 3 | Governance | 1.2s | ✓ |
| 4 | Telemetry | 1.0s | ✓ |
| 5 | Workflows | 1.2s | ✓ |
| 6 | Replay | 1.0s | ✓ |
| 7 | Demo Execution | 2.5s | ✓ |

## Artifacts Produced
- Video: full-walkthrough.webm (1.6 MB)
- Trace: full-walkthrough.zip (4.5 MB)
- Screenshots: 7 files (680 KB total)

## Runtime State
- Backend: HEALTHY
- Frontend: 200 OK
- Console errors: 0
- APIs: 10/10 returning 200
```

---

## Guided Execution Flows

For interactive demonstrations:

```typescript
interface GuidedDemo {
  // Step-by-step execution with pauses
  steps: GuidedStep[];
  
  // Operator can advance manually or auto-advance
  auto_advance: boolean;
  advance_delay_ms: number;
}

interface GuidedStep {
  instruction: string;           // What to show/explain
  action: Action;                // What to execute
  highlight: string | null;      // Element to highlight
  screenshot: boolean;
  pause_after: boolean;          // Wait for operator to continue
}
```

---

## Integration with Current System

| Component | Status | Notes |
|-----------|--------|-------|
| Playwright video recording | ✅ Working | `scripts/record-final.js` |
| Screenshot pipeline | ✅ Working | 38 snapshots generated |
| Trace capture | ✅ Working | 10 trace files |
| Demo data seeding | ✅ Working | API calls to generate state |
| Report generation | ✅ Working | Markdown reports |
| Docker execution | ✅ Working | Containers healthy |
| Chromium + FFmpeg | ✅ Installed | ms-playwright directory |
