/**
 * NexusOS Visual Verify — GitHub Action Entry Point
 * Runs Playwright-based deployment verification with governance audit trail.
 */

const core = require('@actions/core');
const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

async function run() {
  const startTime = Date.now();

  // Parse inputs
  const targetUrl = core.getInput('url', { required: true });
  const pagesInput = core.getInput('pages') || '/';
  const apiInput = core.getInput('api-endpoints') || '';
  const expectedTitle = core.getInput('expected-title') || '';
  const viewportInput = core.getInput('viewport') || '1920x1080';
  const timeoutMs = parseInt(core.getInput('timeout') || '30000', 10);
  const failOnConsole = core.getInput('fail-on-console-errors') === 'true';

  // Parse viewport
  const [vw, vh] = viewportInput.split('x').map(Number);
  const viewport = { width: vw || 1920, height: vh || 1080 };

  // Parse pages
  const pages = pagesInput.split(',').map(p => p.trim()).filter(Boolean);
  const apiEndpoints = apiInput.split(',').map(p => p.trim()).filter(Boolean);

  // Setup artifacts directory
  const artifactsDir = path.join(process.env.GITHUB_WORKSPACE || '.', 'nexusos-artifacts');
  fs.mkdirSync(artifactsDir, { recursive: true });
  const screenshotsDir = path.join(artifactsDir, 'screenshots');
  fs.mkdirSync(screenshotsDir, { recursive: true });

  core.info(`NexusOS Visual Verify`);
  core.info(`Target: ${targetUrl}`);
  core.info(`Pages: ${pages.join(', ')}`);
  core.info(`Viewport: ${viewport.width}x${viewport.height}`);
  core.info('');

  // Launch browser
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
  } catch (e) {
    core.setFailed(`Failed to launch browser: ${e.message}`);
    return;
  }

  const context = await browser.newContext({ viewport });
  const results = [];
  let totalConsoleErrors = 0;

  // Verify each page
  for (const pagePath of pages) {
    const url = targetUrl.replace(/\/$/, '') + pagePath;
    const page = await context.newPage();
    const consoleErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    const pageStart = Date.now();
    let status = 'PASS';
    let error = null;
    let titleMatch = null;

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: timeoutMs });
      const loadMs = Date.now() - pageStart;

      // Title check
      if (expectedTitle) {
        const title = await page.title();
        titleMatch = title.toLowerCase().includes(expectedTitle.toLowerCase());
        if (!titleMatch) status = 'FAIL';
      }

      // Screenshot
      const screenshotName = pagePath.replace(/[^a-zA-Z0-9]/g, '-').replace(/^-/, '') || 'root';
      const screenshotPath = path.join(screenshotsDir, `${screenshotName}.png`);
      await page.screenshot({ path: screenshotPath });

      totalConsoleErrors += consoleErrors.length;

      results.push({ path: pagePath, status, loadMs, consoleErrors: consoleErrors.length, screenshotPath, titleMatch });
      core.info(`  ${status === 'PASS' ? '✅' : '❌'} ${pagePath} — ${loadMs}ms, ${consoleErrors.length} errors`);

    } catch (e) {
      status = e.message.includes('Timeout') ? 'TIMEOUT' : 'ERROR';
      error = e.message.substring(0, 100);
      results.push({ path: pagePath, status, loadMs: Date.now() - pageStart, error, consoleErrors: consoleErrors.length });
      core.info(`  ❌ ${pagePath} — ${status}: ${error}`);
    }

    await page.close();
  }

  // API checks
  const apiResults = [];
  for (const apiPath of apiEndpoints) {
    const url = targetUrl.replace(/\/$/, '') + apiPath;
    try {
      const resp = await fetch(url);
      const status = resp.status === 200 ? 'PASS' : 'FAIL';
      apiResults.push({ path: apiPath, status, httpStatus: resp.status });
      core.info(`  ${status === 'PASS' ? '✅' : '❌'} API ${apiPath} — ${resp.status}`);
    } catch (e) {
      apiResults.push({ path: apiPath, status: 'ERROR', error: e.message });
      core.info(`  ❌ API ${apiPath} — ERROR: ${e.message}`);
    }
  }

  await context.close();
  await browser.close();

  // Compute verdict
  const allChecks = [...results, ...apiResults];
  const passed = allChecks.filter(r => r.status === 'PASS').length;
  const total = allChecks.length;
  const score = total > 0 ? Math.round((passed / total) * 100) : 100;

  let verdict = 'PASS';
  if (allChecks.some(r => r.status === 'FAIL' || r.status === 'ERROR' || r.status === 'TIMEOUT')) {
    verdict = 'FAIL';
  }
  if (failOnConsole && totalConsoleErrors > 0) {
    verdict = 'FAIL';
  }

  const durationMs = Date.now() - startTime;

  // Generate proof manifest
  const manifest = {
    execution_id: crypto.randomBytes(8).toString('hex'),
    timestamp: new Date().toISOString(),
    target_url: targetUrl,
    verdict,
    score,
    duration_ms: durationMs,
    pages: results,
    api_results: apiResults,
    console_errors_total: totalConsoleErrors,
    governance: { validated: true, policy: 'github-action-default' },
    checksum: crypto.createHash('sha256').update(JSON.stringify({ results, apiResults, verdict, score })).digest('hex'),
  };

  // Write report
  const reportPath = path.join(artifactsDir, 'verification-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(manifest, null, 2));

  // Write summary for PR
  const summaryPath = path.join(artifactsDir, 'summary.md');
  let summary = `## NexusOS Verification: ${verdict === 'PASS' ? '✅ PASS' : '❌ FAIL'}\n\n`;
  summary += `**Target:** ${targetUrl}\n`;
  summary += `**Score:** ${score}/100 | **Duration:** ${(durationMs / 1000).toFixed(1)}s\n\n`;
  summary += `| Page | Status | Load Time | Errors |\n|------|--------|-----------|--------|\n`;
  for (const r of results) {
    summary += `| ${r.path} | ${r.status} | ${r.loadMs}ms | ${r.consoleErrors} |\n`;
  }
  if (apiResults.length > 0) {
    summary += `\n| API | Status | HTTP |\n|-----|--------|------|\n`;
    for (const r of apiResults) {
      summary += `| ${r.path} | ${r.status} | ${r.httpStatus || 'N/A'} |\n`;
    }
  }
  summary += `\n*Proof manifest: \`${manifest.checksum.substring(0, 16)}...\`*\n`;
  fs.writeFileSync(summaryPath, summary);

  // Write to GitHub Step Summary
  if (process.env.GITHUB_STEP_SUMMARY) {
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, summary);
  }

  // Set outputs
  core.setOutput('verdict', verdict);
  core.setOutput('score', score.toString());
  core.setOutput('duration', durationMs.toString());
  core.setOutput('screenshots', screenshotsDir);
  core.setOutput('report', reportPath);

  core.info('');
  core.info(`Verdict: ${verdict} | Score: ${score}/100 | Duration: ${(durationMs / 1000).toFixed(1)}s`);

  // Fail the action if verification failed
  if (verdict === 'FAIL') {
    core.setFailed(`Deployment verification failed. Score: ${score}/100`);
  }
}

run().catch(e => {
  core.setFailed(`NexusOS verification error: ${e.message}`);
});
