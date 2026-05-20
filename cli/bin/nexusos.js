#!/usr/bin/env node
/**
 * NexusOS CLI — Governed deployment verification from the command line.
 * Usage: npx nexusos verify https://your-app.com
 */

const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];

if (command !== 'verify' || !args[1]) {
  console.log('NexusOS — Governed AI Operational Trust Platform');
  console.log('');
  console.log('Usage:');
  console.log('  npx nexusos verify <url> [options]');
  console.log('');
  console.log('Options:');
  console.log('  --pages /,/about,/dashboard    Pages to verify (comma-separated)');
  console.log('  --apis /api/health             API endpoints to check');
  console.log('  --title "My App"               Expected page title');
  console.log('  --viewport 1920x1080           Browser viewport');
  console.log('  --timeout 30000                Per-page timeout (ms)');
  console.log('  --output ./results             Output directory');
  console.log('  --strict                       Fail on console errors');
  console.log('');
  console.log('Examples:');
  console.log('  npx nexusos verify https://example.com');
  console.log('  npx nexusos verify https://app.com --pages /,/dashboard --apis /api/health');
  process.exit(command ? 1 : 0);
}

const targetUrl = args[1];

// Parse options
function getOpt(name, defaultVal) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return defaultVal;
  return args[idx + 1] || defaultVal;
}

const pagesStr = getOpt('pages', '/');
const apisStr = getOpt('apis', '');
const expectedTitle = getOpt('title', '');
const viewportStr = getOpt('viewport', '1920x1080');
const timeoutMs = parseInt(getOpt('timeout', '30000'), 10);
const outputDir = getOpt('output', './nexusos-results');
const strict = args.includes('--strict');

const pages = pagesStr.split(',').map(p => p.trim()).filter(Boolean);
const apis = apisStr ? apisStr.split(',').map(p => p.trim()).filter(Boolean) : [];
const [vw, vh] = viewportStr.split('x').map(Number);

async function verify() {
  const startTime = Date.now();

  console.log('╔══════════════════════════════════════════╗');
  console.log('║  NexusOS Verification                    ║');
  console.log('╚══════════════════════════════════════════╝');
  console.log(`  Target: ${targetUrl}`);
  console.log(`  Pages:  ${pages.join(', ')}`);
  if (apis.length) console.log(`  APIs:   ${apis.join(', ')}`);
  console.log('');

  // Setup output
  fs.mkdirSync(outputDir, { recursive: true });
  const screenshotsDir = path.join(outputDir, 'screenshots');
  fs.mkdirSync(screenshotsDir, { recursive: true });

  // Launch browser — find installed Chromium
  const launchOpts = { headless: true };
  const localAppData = process.env.LOCALAPPDATA || '';
  if (localAppData) {
    const msDir = path.join(localAppData, 'ms-playwright');
    if (fs.existsSync(msDir)) {
      const dirs = fs.readdirSync(msDir).filter(d => d.startsWith('chromium-')).sort().reverse();
      for (const dir of dirs) {
        const exe = path.join(msDir, dir, 'chrome-win64', 'chrome.exe');
        if (fs.existsSync(exe)) { launchOpts.executablePath = exe; break; }
      }
    }
  }
  const browser = await chromium.launch(launchOpts);
  const context = await browser.newContext({ viewport: { width: vw, height: vh } });

  const results = [];
  let totalErrors = 0;

  for (const pagePath of pages) {
    const url = targetUrl.replace(/\/$/, '') + pagePath;
    const page = await context.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });

    const t0 = Date.now();
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: timeoutMs });
      const loadMs = Date.now() - t0;

      let status = 'PASS';
      let titleMatch = null;
      if (expectedTitle) {
        const title = await page.title();
        titleMatch = title.toLowerCase().includes(expectedTitle.toLowerCase());
        if (!titleMatch) status = 'FAIL';
      }

      const name = pagePath.replace(/[^a-zA-Z0-9]/g, '-').replace(/^-/, '') || 'root';
      await page.screenshot({ path: path.join(screenshotsDir, `${name}.png`) });

      totalErrors += errors.length;
      results.push({ path: pagePath, status, loadMs, errors: errors.length });
      console.log(`  ${status === 'PASS' ? '✅' : '❌'} ${pagePath} — ${loadMs}ms${errors.length ? ` (${errors.length} errors)` : ''}`);
    } catch (e) {
      const status = e.message.includes('Timeout') ? 'TIMEOUT' : 'ERROR';
      results.push({ path: pagePath, status, loadMs: Date.now() - t0, error: e.message.substring(0, 80) });
      console.log(`  ❌ ${pagePath} — ${status}`);
    }
    await page.close();
  }

  // API checks
  const apiResults = [];
  for (const apiPath of apis) {
    const url = targetUrl.replace(/\/$/, '') + apiPath;
    try {
      const resp = await fetch(url);
      const status = resp.status === 200 ? 'PASS' : 'FAIL';
      apiResults.push({ path: apiPath, status, httpStatus: resp.status });
      console.log(`  ${status === 'PASS' ? '✅' : '❌'} API ${apiPath} — ${resp.status}`);
    } catch (e) {
      apiResults.push({ path: apiPath, status: 'ERROR' });
      console.log(`  ❌ API ${apiPath} — ERROR`);
    }
  }

  await context.close();
  await browser.close();

  // Verdict
  const all = [...results, ...apiResults];
  const passed = all.filter(r => r.status === 'PASS').length;
  const score = all.length > 0 ? Math.round((passed / all.length) * 100) : 100;
  let verdict = all.some(r => r.status !== 'PASS') ? 'FAIL' : 'PASS';
  if (strict && totalErrors > 0) verdict = 'FAIL';

  const durationMs = Date.now() - startTime;

  // Proof manifest
  const manifest = {
    execution_id: crypto.randomBytes(8).toString('hex'),
    timestamp: new Date().toISOString(),
    target_url: targetUrl,
    verdict,
    score,
    duration_ms: durationMs,
    pages: results,
    api_results: apiResults,
    governance: { validated: true, policy: 'cli-default' },
    checksum: crypto.createHash('sha256').update(JSON.stringify({ results, apiResults })).digest('hex'),
  };

  fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(manifest, null, 2));

  console.log('');
  console.log(`  Verdict: ${verdict === 'PASS' ? '✅ PASS' : '❌ FAIL'} | Score: ${score}/100 | ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`  Screenshots: ${screenshotsDir}`);
  console.log(`  Report: ${path.join(outputDir, 'report.json')}`);
  console.log(`  Proof: ${manifest.checksum.substring(0, 16)}...`);

  process.exit(verdict === 'PASS' ? 0 : 1);
}

verify().catch(e => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
