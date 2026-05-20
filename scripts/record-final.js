/**
 * NexusOS Final Demo Recording Pipeline
 * Produces: videos, traces, snapshots, replay artifacts
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'http://localhost:3000';
const API = 'http://localhost:8000';
const ROOT = path.resolve(__dirname, '..');
const VIDEOS = path.join(ROOT, 'artifacts', 'videos');
const TRACES = path.join(ROOT, 'artifacts', 'traces');
const SNAPS = path.join(ROOT, 'artifacts', 'snapshots');
const REPLAY = path.join(ROOT, 'artifacts', 'replay');
const CHROME = path.join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium-1223', 'chrome-win64', 'chrome.exe');
const VP = { width: 1920, height: 1080 };

[VIDEOS, TRACES, SNAPS, REPLAY].forEach(d => fs.mkdirSync(d, { recursive: true }));

const delay = ms => new Promise(r => setTimeout(r, ms));

async function scrollTo(page, sel, text) {
  await page.evaluate(({ s, t }) => {
    for (const el of document.querySelectorAll(s)) {
      if (el.textContent.includes(t)) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    }
  }, { s: sel, t: text });
  await delay(800);
}

async function snap(page, name) {
  await page.screenshot({ path: path.join(SNAPS, `${name}.png`) });
}

async function record(name, fn) {
  console.log(`  [REC] ${name}`);
  const browser = await chromium.launch({ headless: true, executablePath: CHROME });
  const ctx = await browser.newContext({ viewport: VP, recordVideo: { dir: VIDEOS, size: VP } });
  await ctx.tracing.start({ screenshots: true, snapshots: true });
  const page = await ctx.newPage();
  try { await fn(page); } catch (e) { console.log(`    WARN: ${e.message}`); }
  await ctx.tracing.stop({ path: path.join(TRACES, `${name}.zip`) });
  const video = page.video();
  await page.close();
  await ctx.close();
  await browser.close();
  if (video) {
    await delay(500);
    try {
      const vp = await video.path();
      const dest = path.join(VIDEOS, `${name}.webm`);
      if (fs.existsSync(dest)) fs.unlinkSync(dest);
      if (fs.existsSync(vp)) fs.renameSync(vp, dest);
      console.log(`    Video: ${(fs.statSync(dest).size / 1024).toFixed(0)} KB`);
    } catch (e) { console.log(`    Video err: ${e.message}`); }
  }
}

// Generate runtime data for richer demos
async function seedData() {
  const post = (ep, body) => fetch(`${API}${ep}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  await post('/api/workflow/execute', { name: 'Diamond Pipeline', steps: [
    { id: 'init', name: 'Initialize', step_type: 'CUSTOM', depends_on: [] },
    { id: 'gov', name: 'Governance Gate', step_type: 'CUSTOM', depends_on: ['init'] },
    { id: 'exec', name: 'Execute', step_type: 'BROWSER', depends_on: ['init'] },
    { id: 'join', name: 'Aggregate', step_type: 'CUSTOM', depends_on: ['gov', 'exec'] }
  ]});
  await post('/api/workflow/execute', { name: 'Sequential ETL', steps: [
    { id: 'extract', name: 'Extract', step_type: 'BROWSER', depends_on: [] },
    { id: 'transform', name: 'Transform', step_type: 'TERMINAL', depends_on: ['extract'] },
    { id: 'load', name: 'Load', step_type: 'CUSTOM', depends_on: ['transform'] }
  ]});
  await post('/api/browser/start', { url: 'https://nexusos.dev/dashboard' });
  await post('/api/terminal/execute', { command: 'echo governed-runtime-proof', working_dir: 'C:\\Windows\\Temp', timeout_seconds: 5 });
  await post('/api/runtime/register', { name: 'replay-proof-runtime', metadata: { version: '0.2.0', mode: 'governed' } });
}

// Capture replay artifacts from API
async function captureReplay() {
  const get = ep => fetch(`${API}${ep}`).then(r => r.json());
  const data = {
    timestamp: new Date().toISOString(),
    health: await get('/api/health'),
    status: await get('/api/status'),
    workflows: await get('/api/workflow/executions'),
    events: await get('/api/events'),
    audit: await get('/api/governance/audit'),
    telemetry: await get('/api/telemetry/executions'),
    sessions: await get('/api/browser/sessions'),
    governance: await get('/api/governance/status'),
  };
  fs.writeFileSync(path.join(REPLAY, 'runtime-state.json'), JSON.stringify(data, null, 2));
  fs.writeFileSync(path.join(REPLAY, 'workflow-executions.json'), JSON.stringify(data.workflows, null, 2));
  fs.writeFileSync(path.join(REPLAY, 'event-stream.json'), JSON.stringify(data.events, null, 2));
  fs.writeFileSync(path.join(REPLAY, 'audit-trail.json'), JSON.stringify(data.audit, null, 2));
  fs.writeFileSync(path.join(REPLAY, 'governance-state.json'), JSON.stringify(data.governance, null, 2));
  fs.writeFileSync(path.join(REPLAY, 'telemetry-state.json'), JSON.stringify(data.telemetry, null, 2));
  console.log(`  Replay artifacts: ${fs.readdirSync(REPLAY).length} files`);
}

// === DEMOS ===

async function fullDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1500);
  await snap(page, 'full-dashboard-top');
  for (const s of ['System Health', 'Execution Runtime', 'Orchestration & Replay', 'Demo Workflows']) {
    await scrollTo(page, 'h3', s);
    await delay(1200);
  }
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await delay(1000);
  await snap(page, 'full-dashboard-bottom');
}

async function governanceDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1000);
  await scrollTo(page, 'h2', 'Governance Status');
  await delay(1200);
  await snap(page, 'gov-status');
  await scrollTo(page, 'h2', 'Audit Trail');
  await delay(1000);
  await snap(page, 'gov-audit');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await delay(800);
  await snap(page, 'gov-banner');
}

async function telemetryDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1000);
  await scrollTo(page, 'h2', 'Telemetry Overview');
  await delay(1200);
  await snap(page, 'tel-overview');
  await scrollTo(page, 'h2', 'Execution Telemetry');
  await delay(1000);
  await snap(page, 'tel-execution');
  await scrollTo(page, 'h2', 'Runtime Health');
  await delay(800);
  await snap(page, 'tel-health');
}

async function replayDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1000);
  await scrollTo(page, 'h2', 'Replay Inspection');
  await delay(1200);
  await snap(page, 'replay-panel');
  await scrollTo(page, 'h2', 'Event Stream');
  await delay(1000);
  await snap(page, 'replay-events');
}

async function workflowsDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1000);
  await scrollTo(page, 'h2', 'Active Workflows');
  await delay(1200);
  await snap(page, 'wf-active');
  await scrollTo(page, 'h2', 'Workflow History');
  await delay(800);
  await snap(page, 'wf-history');
  await scrollTo(page, 'h3', 'Demo Workflows');
  await delay(800);
  const btn = page.getByRole('button', { name: 'Run All' });
  if (await btn.isVisible()) { await btn.click(); await delay(2500); }
  await snap(page, 'wf-executed');
}

async function healthDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1500);
  await snap(page, 'health-top');
  await scrollTo(page, 'h2', 'Runtime Health');
  await delay(1200);
  await snap(page, 'health-subsystems');
  await scrollTo(page, 'h2', 'Browser Sessions');
  await delay(800);
  await snap(page, 'health-sessions');
  await page.goto(`${BASE}/landing`, { waitUntil: 'networkidle' });
  await delay(1500);
  await snap(page, 'health-architecture');
}

async function teaserDemo(page) {
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await delay(1500);
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight / 2, behavior: 'smooth' }));
  await delay(2000);
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
  await delay(2000);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await delay(1500);
}

// === MAIN ===
async function main() {
  console.log('╔═══════════════════════════════════════════════════╗');
  console.log('║  NexusOS Final Proof Generation Pipeline          ║');
  console.log('╚═══════════════════════════════════════════════════╝\n');

  console.log('[1/5] Seeding runtime data...');
  await seedData();
  console.log('  Done\n');

  console.log('[2/5] Recording videos + traces + snapshots...');
  await record('full-demo', fullDemo);
  await record('governance-demo', governanceDemo);
  await record('telemetry-demo', telemetryDemo);
  await record('replay-demo', replayDemo);
  await record('workflows-demo', workflowsDemo);
  await record('runtime-health-demo', healthDemo);
  await record('30-second-teaser', teaserDemo);
  console.log('');

  console.log('[3/5] Capturing replay artifacts...');
  await captureReplay();
  console.log('');

  console.log('[4/5] Validating...');
  const videos = fs.readdirSync(VIDEOS).filter(f => f.endsWith('.webm'));
  const traces = fs.readdirSync(TRACES).filter(f => f.endsWith('.zip'));
  const snaps = fs.readdirSync(SNAPS).filter(f => f.endsWith('.png'));
  const replays = fs.readdirSync(REPLAY).filter(f => f.endsWith('.json'));
  const health = await fetch(`${API}/api/health`).then(r => r.json());
  const frontend = await fetch(BASE).then(r => r.status);
  console.log(`  Videos: ${videos.length}`);
  console.log(`  Traces: ${traces.length}`);
  console.log(`  Snapshots: ${snaps.length}`);
  console.log(`  Replay files: ${replays.length}`);
  console.log(`  Backend: ${health.overall}`);
  console.log(`  Frontend: ${frontend}`);
  console.log('');

  console.log('[5/5] Summary');
  console.log('╔═══════════════════════════════════════════════════╗');
  console.log(`║  Videos: ${videos.length} | Traces: ${traces.length} | Snaps: ${snaps.length} | Replay: ${replays.length}    ║`);
  console.log(`║  Backend: ${health.overall} | Frontend: ${frontend}              ║`);
  console.log('║  Status: COMPLETE                                 ║');
  console.log('╚═══════════════════════════════════════════════════╝');
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
