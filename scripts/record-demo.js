/**
 * NexusOS Demo Recording Script
 * Records video walkthroughs of all dashboard sections using Playwright.
 * Produces: MP4 videos, PNG screenshots, execution traces.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:3000';
const ARTIFACTS_DIR = path.resolve(__dirname, '..', 'artifacts');
const VIDEOS_DIR = path.join(ARTIFACTS_DIR, 'videos');
const SCREENSHOTS_DIR = path.join(ARTIFACTS_DIR, 'screenshots');

// Ensure directories exist
fs.mkdirSync(VIDEOS_DIR, { recursive: true });
fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForHealthy() {
  for (let i = 0; i < 10; i++) {
    try {
      const res = await fetch('http://localhost:8000/api/health');
      if (res.ok) return true;
    } catch (e) {}
    await delay(1000);
  }
  throw new Error('Backend not healthy after 10 seconds');
}

async function recordDemo(name, actions) {
  const browser = await chromium.launch({
    headless: true,
    channel: 'chromium',
    executablePath: path.join(process.env.LOCALAPPDATA, 'ms-playwright', 'chromium-1223', 'chrome-win64', 'chrome.exe'),
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: {
      dir: VIDEOS_DIR,
      size: { width: 1440, height: 900 }
    }
  });

  const page = await context.newPage();

  try {
    await actions(page);
  } finally {
    await page.close();
    await context.close();
    await browser.close();
  }

  // Rename the video file to the demo name
  const videoFiles = fs.readdirSync(VIDEOS_DIR).filter(f => f.endsWith('.webm'));
  if (videoFiles.length > 0) {
    const latest = videoFiles.sort().pop();
    const src = path.join(VIDEOS_DIR, latest);
    const dest = path.join(VIDEOS_DIR, `${name}.webm`);
    if (fs.existsSync(dest)) fs.unlinkSync(dest);
    fs.renameSync(src, dest);
    console.log(`  Video saved: ${dest}`);
  }
}

async function captureScreenshot(page, name) {
  const filepath = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage: false });
  console.log(`  Screenshot: ${filepath}`);
}

async function captureFullPageScreenshot(page, name) {
  const filepath = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`  Full screenshot: ${filepath}`);
}

// --- Demo Scenarios ---

async function demoDashboardOverview(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(2000);
  await captureScreenshot(page, 'dashboard-overview');
  await captureFullPageScreenshot(page, 'dashboard-full');
  await delay(1000);
}

async function demoLandingPage(page) {
  await page.goto(`${BASE_URL}/landing`);
  await page.waitForSelector('h1');
  await delay(1500);
  await captureScreenshot(page, 'landing-page');
  await captureFullPageScreenshot(page, 'landing-full');
}

async function demoTelemetry(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  // Scroll to telemetry section
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Telemetry Overview')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'telemetry');
  // Also capture execution telemetry
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Execution Telemetry')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(800);
  await captureScreenshot(page, 'execution-telemetry');
}

async function demoGovernance(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Governance Status')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'governance');
  // Scroll to audit trail
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Audit Trail')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(800);
  await captureScreenshot(page, 'audit-trail');
}

async function demoReplay(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Replay Inspection')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'replay-inspection');
}

async function demoWorkflows(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Active Workflows')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'workflows');
  // Scroll to workflow history
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Workflow History')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(800);
  await captureScreenshot(page, 'workflow-history');
}

async function demoOrchestration(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  // Scroll to Demo Workflows section and execute one
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h3');
    for (const h of headers) {
      if (h.textContent.includes('Demo Workflows')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'orchestration-demos');

  // Click "Run" on the Orchestration (Diamond) workflow
  const runButtons = await page.getByRole('button', { name: 'Run' }).all();
  if (runButtons.length >= 3) {
    await runButtons[2].click(); // Diamond orchestration is 3rd
    await delay(2000);
    await captureScreenshot(page, 'orchestration-executed');
  }
}

async function demoRuntimeHealth(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1500);
  // Runtime health is at the top
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Runtime Health')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'runtime-health');
}

async function demoActiveSessions(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Browser Sessions')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'active-sessions');
}

async function demoEventStreams(page) {
  await page.goto(BASE_URL);
  await page.waitForSelector('h1');
  await delay(1000);
  await page.evaluate(() => {
    const headers = document.querySelectorAll('h2');
    for (const h of headers) {
      if (h.textContent.includes('Event Stream')) {
        h.scrollIntoView({ block: 'start' });
        break;
      }
    }
  });
  await delay(1000);
  await captureScreenshot(page, 'event-streams');
}

// --- Execute workflow to generate data ---
async function generateDemoData() {
  console.log('Generating demo data via API...');

  // Execute a workflow
  await fetch('http://localhost:8000/api/workflow/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'Demo Orchestration Pipeline',
      steps: [
        { id: 'step-1', name: 'Initialize Runtime', step_type: 'CUSTOM', config: {}, depends_on: [] },
        { id: 'step-2', name: 'Validate Governance', step_type: 'CUSTOM', config: {}, depends_on: ['step-1'] },
        { id: 'step-3', name: 'Execute Browser Task', step_type: 'BROWSER', config: {}, depends_on: ['step-1'] },
        { id: 'step-4', name: 'Aggregate Results', step_type: 'CUSTOM', config: {}, depends_on: ['step-2', 'step-3'] },
      ]
    })
  });

  // Start a browser session
  await fetch('http://localhost:8000/api/browser/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: 'https://example.com' })
  });

  // Execute a terminal command
  await fetch('http://localhost:8000/api/terminal/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command: 'echo NexusOS Runtime Active', working_dir: 'C:\\Windows\\Temp', timeout_seconds: 10 })
  });

  // Register a runtime
  await fetch('http://localhost:8000/api/runtime/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'demo-runtime', metadata: { type: 'browser', version: '1.0' } })
  });

  console.log('Demo data generated.');
}

// --- Main ---
async function main() {
  console.log('=== NexusOS Demo Recording Pipeline ===\n');

  // Verify backend health
  console.log('1. Verifying backend health...');
  await waitForHealthy();
  console.log('   Backend: HEALTHY\n');

  // Generate demo data for richer screenshots
  console.log('2. Generating demo data...');
  await generateDemoData();
  console.log('');

  // Record full demo walkthrough
  console.log('3. Recording: full-demo-walkthrough');
  await recordDemo('full-demo-walkthrough', async (page) => {
    await demoDashboardOverview(page);
    await demoTelemetry(page);
    await demoGovernance(page);
    await demoReplay(page);
    await demoWorkflows(page);
    await demoOrchestration(page);
    await demoRuntimeHealth(page);
    await demoActiveSessions(page);
    await demoEventStreams(page);
  });

  // Record short teaser (30s)
  console.log('\n4. Recording: short-teaser');
  await recordDemo('short-teaser', async (page) => {
    await page.goto(BASE_URL);
    await page.waitForSelector('h1');
    await delay(2000);
    await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
    await delay(3000);
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await delay(2000);
  });

  // Record architecture showcase
  console.log('\n5. Recording: architecture-showcase');
  await recordDemo('architecture-showcase', async (page) => {
    await page.goto(`${BASE_URL}/landing`);
    await page.waitForSelector('h1');
    await delay(2000);
    await captureScreenshot(page, 'landing-page');
    await captureFullPageScreenshot(page, 'landing-full');
    await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
    await delay(3000);
  });

  // Record governance demo
  console.log('\n6. Recording: governance-demo');
  await recordDemo('governance-demo', async (page) => {
    await page.goto(BASE_URL);
    await page.waitForSelector('h1');
    await delay(1000);
    await demoGovernance(page);
    await delay(1000);
  });

  // Record orchestration demo
  console.log('\n7. Recording: orchestration-demo');
  await recordDemo('orchestration-demo', async (page) => {
    await page.goto(BASE_URL);
    await page.waitForSelector('h1');
    await delay(1000);
    await demoOrchestration(page);
    await demoWorkflows(page);
    await delay(1000);
  });

  console.log('\n=== Demo Recording Complete ===');
  console.log(`Videos: ${VIDEOS_DIR}`);
  console.log(`Screenshots: ${SCREENSHOTS_DIR}`);
}

main().catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
