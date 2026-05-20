/**
 * NexusOS Demo Recording Pipeline v2
 * Cinematic-quality video recordings with traces and snapshots.
 * Uses Playwright's recordVideo, tracing, and screenshot APIs.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';
const ROOT = path.resolve(__dirname, '..');
const VIDEOS_DIR = path.join(ROOT, 'artifacts', 'videos');
const TRACES_DIR = path.join(ROOT, 'artifacts', 'traces');
const SNAPSHOTS_DIR = path.join(ROOT, 'artifacts', 'snapshots');
const SCREENSHOTS_DIR = path.join(ROOT, 'artifacts', 'screenshots');

// Cinematic viewport - 16:9 widescreen
const VIEWPORT = { width: 1920, height: 1080 };

// Ensure directories
[VIDEOS_DIR, TRACES_DIR, SNAPSHOTS_DIR, SCREENSHOTS_DIR].forEach(d =>
  fs.mkdirSync(d, { recursive: true })
);

const CHROME_PATH = path.join(
  process.env.LOCALAPPDATA,
  'ms-playwright', 'chromium-1223', 'chrome-win64', 'chrome.exe'
);

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function verifyBackend() {
  const res = await fetch(`${BACKEND_URL}/api/health`);
  if (!res.ok) throw new Error(`Backend unhealthy: ${res.status}`);
  const data = await res.json();
  console.log(`  Backend: ${data.overall} (${Object.keys(data.subsystems).length} subsystems)`);
  return data;
}

async function generateFreshData() {
  // Execute diamond workflow
  await fetch(`${BACKEND_URL}/api/workflow/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Diamond Orchestration',
      steps: [
        { id: 'init', name: 'Initialize', step_type: 'CUSTOM', config: {}, depends_on: [] },
        { id: 'validate', name: 'Governance Check', step_type: 'CUSTOM', config: {}, depends_on: ['init'] },
        { id: 'execute', name: 'Execute Task', step_type: 'BROWSER', config: {}, depends_on: ['init'] },
        { id: 'aggregate', name: 'Aggregate', step_type: 'CUSTOM', config: {}, depends_on: ['validate', 'execute'] },
      ]
    })
  });

  // Start browser session
  await fetch(`${BACKEND_URL}/api/browser/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: 'https://nexusos.dev' })
  });

  // Terminal command
  await fetch(`${BACKEND_URL}/api/terminal/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: 'echo NexusOS Governed Runtime v0.2.0', working_dir: 'C:\\Windows\\Temp', timeout_seconds: 10 })
  });

  // Register runtime
  await fetch(`${BACKEND_URL}/api/runtime/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'proof-runtime', metadata: { purpose: 'demo-proof', version: '0.2.0' } })
  });

  // Second workflow - linear pipeline
  await fetch(`${BACKEND_URL}/api/workflow/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Linear Pipeline',
      steps: [
        { id: 'step-a', name: 'Fetch Data', step_type: 'BROWSER', config: {}, depends_on: [] },
        { id: 'step-b', name: 'Process', step_type: 'TERMINAL', config: {}, depends_on: ['step-a'] },
        { id: 'step-c', name: 'Store Results', step_type: 'CUSTOM', config: {}, depends_on: ['step-b'] },
      ]
    })
  });
}

async function recordWithTrace(name, actions) {
  console.log(`\n  Recording: ${name}`);
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME_PATH,
  });

  const context = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: {
      dir: VIDEOS_DIR,
      size: VIEWPORT,
    }
  });

  // Start tracing
  await context.tracing.start({
    screenshots: true,
    snapshots: true,
    sources: false,
  });

  const page = await context.newPage();

  try {
    await actions(page, name);
  } catch (err) {
    console.log(`    WARNING: ${err.message}`);
  }

  // Save trace
  const tracePath = path.join(TRACES_DIR, `${name}.zip`);
  await context.tracing.stop({ path: tracePath });
  console.log(`    Trace: ${tracePath}`);

  // Get video path before closing
  const video = page.video();

  await page.close();
  await context.close();
  await browser.close();

  // Rename video
  if (video) {
    try {
      const videoPath = await video.path();
      const dest = path.join(VIDEOS_DIR, `${name}.webm`);
      if (fs.existsSync(dest)) fs.unlinkSync(dest);
      // Wait for file to be written
      await delay(500);
      if (fs.existsSync(videoPath)) {
        fs.renameSync(videoPath, dest);
        const size = fs.statSync(dest).size;
        console.log(`    Video: ${dest} (${(size / 1024).toFixed(0)} KB)`);
      }
    } catch (e) {
      console.log(`    Video rename: ${e.message}`);
    }
  }
}

async function snapshot(page, name) {
  const filepath = path.join(SNAPSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filepath });
  console.log(`    Snapshot: ${name}.png`);
}

async function fullSnapshot(page, name) {
  const filepath = path.join(SNAPSHOTS_DIR, `${name}-full.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`    Full snapshot: ${name}-full.png`);
}

// Smooth scroll helper
async function smoothScrollTo(page, selector, text) {
  await page.evaluate(({ sel, txt }) => {
    const elements = document.querySelectorAll(sel);
    for (const el of elements) {
      if (el.textContent.includes(txt)) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    }
  }, { sel: selector, txt: text });
  await delay(800);
}

// ============ DEMO SCENARIOS ============

async function fullDashboardDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1500);
  await snapshot(page, 'dashboard-hero');

  // Pan through each section smoothly
  const sections = [
    'System Health', 'Execution Runtime', 'Orchestration & Replay', 'Demo Workflows'
  ];
  for (const section of sections) {
    await smoothScrollTo(page, 'h3', section);
    await delay(1200);
  }

  // Scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await delay(1000);
  await fullSnapshot(page, 'dashboard');
}

async function telemetryDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1000);

  await smoothScrollTo(page, 'h2', 'Telemetry Overview');
  await delay(1000);
  await snapshot(page, 'telemetry-overview');

  await smoothScrollTo(page, 'h2', 'Execution Telemetry');
  await delay(1000);
  await snapshot(page, 'telemetry-execution');

  // Show the metrics data
  await smoothScrollTo(page, 'h3', 'System Health');
  await delay(800);
  await snapshot(page, 'telemetry-health');
}

async function governanceDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1000);

  await smoothScrollTo(page, 'h2', 'Governance Status');
  await delay(1200);
  await snapshot(page, 'governance-status');

  await smoothScrollTo(page, 'h2', 'Audit Trail');
  await delay(1200);
  await snapshot(page, 'governance-audit');

  // Show the system banner with governance active
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await delay(1000);
  await snapshot(page, 'governance-banner');
}

async function orchestrationDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1000);

  await smoothScrollTo(page, 'h3', 'Demo Workflows');
  await delay(1000);
  await snapshot(page, 'orchestration-available');

  // Execute the Orchestration (Diamond) workflow
  const buttons = await page.getByRole('button', { name: 'Run' }).all();
  if (buttons.length >= 3) {
    await buttons[2].click();
    await delay(2000);
    await snapshot(page, 'orchestration-running');
  }

  // Show workflow executions
  await smoothScrollTo(page, 'h2', 'Active Workflows');
  await delay(1000);
  await snapshot(page, 'orchestration-results');

  await smoothScrollTo(page, 'h2', 'Workflow History');
  await delay(800);
  await snapshot(page, 'orchestration-history');
}

async function replayDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1000);

  await smoothScrollTo(page, 'h2', 'Replay Inspection');
  await delay(1200);
  await snapshot(page, 'replay-interface');

  // Show event stream (related to replay)
  await smoothScrollTo(page, 'h2', 'Event Stream');
  await delay(1000);
  await snapshot(page, 'replay-events');
}

async function workflowExecutionDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1000);

  // Click Run All to execute all demo workflows
  const runAll = page.getByRole('button', { name: 'Run All' });
  if (await runAll.isVisible()) {
    await smoothScrollTo(page, 'h3', 'Demo Workflows');
    await delay(500);
    await snapshot(page, 'workflow-before-execution');
    await runAll.click();
    await delay(3000);
    await snapshot(page, 'workflow-after-execution');
  }

  // Show results
  await smoothScrollTo(page, 'h2', 'Active Workflows');
  await delay(1000);
  await snapshot(page, 'workflow-results');

  await smoothScrollTo(page, 'h2', 'Event Stream');
  await delay(800);
  await snapshot(page, 'workflow-events');
}

async function runtimeHealthDemo(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  await delay(1500);

  // System banner
  await snapshot(page, 'health-banner');

  // Runtime health panel
  await smoothScrollTo(page, 'h2', 'Runtime Health');
  await delay(1200);
  await snapshot(page, 'health-subsystems');

  // Browser sessions
  await smoothScrollTo(page, 'h2', 'Browser Sessions');
  await delay(800);
  await snapshot(page, 'health-browser');

  // Terminal
  await smoothScrollTo(page, 'h2', 'Terminal Sessions');
  await delay(800);
  await snapshot(page, 'health-terminal');

  // Landing page for architecture view
  await page.goto(`${BASE_URL}/landing`, { waitUntil: 'networkidle' });
  await delay(1500);
  await snapshot(page, 'health-architecture');
  await fullSnapshot(page, 'health-landing');
}

// ============ MAIN ============

async function main() {
  console.log('╔══════════════════════════════════════════════╗');
  console.log('║  NexusOS Demo Recording Pipeline v2         ║');
  console.log('║  Cinematic Quality • Traces • Snapshots     ║');
  console.log('╚══════════════════════════════════════════════╝');

  // Phase 1: Verify
  console.log('\n[Phase 1] Verifying runtime...');
  await verifyBackend();
  console.log('  Frontend: http://localhost:3000');

  // Phase 2: Generate data
  console.log('\n[Phase 2] Generating demo data...');
  await generateFreshData();
  console.log('  Data generated (workflows, sessions, events)');

  // Phase 3: Record demos
  console.log('\n[Phase 3] Recording demos...');

  await recordWithTrace('full-dashboard-demo', fullDashboardDemo);
  await recordWithTrace('telemetry-demo', telemetryDemo);
  await recordWithTrace('governance-demo', governanceDemo);
  await recordWithTrace('orchestration-demo', orchestrationDemo);
  await recordWithTrace('replay-demo', replayDemo);
  await recordWithTrace('workflow-execution-demo', workflowExecutionDemo);
  await recordWithTrace('runtime-health-demo', runtimeHealthDemo);

  // Phase 4: Validate
  console.log('\n[Phase 4] Validating artifacts...');

  const videos = fs.readdirSync(VIDEOS_DIR).filter(f => f.endsWith('.webm'));
  const traces = fs.readdirSync(TRACES_DIR).filter(f => f.endsWith('.zip'));
  const snapshots = fs.readdirSync(SNAPSHOTS_DIR).filter(f => f.endsWith('.png'));

  console.log(`  Videos: ${videos.length} files`);
  console.log(`  Traces: ${traces.length} files`);
  console.log(`  Snapshots: ${snapshots.length} files`);

  // Verify backend still healthy
  const health = await verifyBackend();
  console.log(`  Backend post-recording: ${health.overall}`);

  // Verify frontend
  const frontendRes = await fetch(BASE_URL);
  console.log(`  Frontend post-recording: ${frontendRes.status === 200 ? 'OK' : 'FAILED'}`);

  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║  ✅ Pipeline Complete                        ║');
  console.log(`║  Videos: ${videos.length} | Traces: ${traces.length} | Snapshots: ${snapshots.length}       ║`);
  console.log('╚══════════════════════════════════════════════╝');
}

main().catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
