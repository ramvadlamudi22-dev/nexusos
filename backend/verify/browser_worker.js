/**
 * NexusOS Browser Verification Worker
 * Runs in Node.js subprocess, uses Playwright to render pages and capture evidence.
 * Input: JSON task file path as CLI argument
 * Output: JSON results to stdout
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function main() {
  const taskFile = process.argv[2];
  if (!taskFile) {
    process.stderr.write('Usage: node browser_worker.js <task.json>\n');
    process.exit(1);
  }

  const task = JSON.parse(fs.readFileSync(taskFile, 'utf-8'));
  const { target_url, execution_id, artifacts_dir, viewport, timeout_ms, pages } = task;

  // Ensure artifacts directory exists
  fs.mkdirSync(artifacts_dir, { recursive: true });

  // Find Chromium
  const chromePath = findChromium();

  const launchOptions = { headless: true };
  if (chromePath) {
    launchOptions.executablePath = chromePath;
  }

  let browser;
  try {
    browser = await chromium.launch(launchOptions);
  } catch (e) {
    // If launch fails, output empty results
    console.log(JSON.stringify({ pages: pages.map(p => ({
      path: p.path, name: p.name, status: 'ERROR', error: `Browser launch failed: ${e.message}`
    })) }));
    process.exit(0);
  }

  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
  });

  const results = [];

  for (const pageConfig of pages) {
    const url = target_url.replace(/\/$/, '') + pageConfig.path;
    const page = await context.newPage();

    // Collect console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    const startTime = Date.now();
    let status = 'PASS';
    let error = null;
    let titleMatch = null;
    let elementsFound = 0;
    let screenshotPath = null;

    try {
      await page.goto(url, {
        waitUntil: 'networkidle',
        timeout: timeout_ms,
      });

      const loadTimeMs = Date.now() - startTime;

      // Check title
      if (pageConfig.expected_title) {
        const title = await page.title();
        titleMatch = title.toLowerCase().includes(pageConfig.expected_title.toLowerCase());
        if (!titleMatch) {
          status = 'FAIL';
        }
      }

      // Check elements
      if (pageConfig.expected_elements && pageConfig.expected_elements.length > 0) {
        for (const selector of pageConfig.expected_elements) {
          try {
            const el = await page.$(selector);
            if (el) elementsFound++;
          } catch (e) {
            // Try as text content
            const found = await page.evaluate(
              (text) => document.body.innerText.toLowerCase().includes(text.toLowerCase()),
              selector
            );
            if (found) elementsFound++;
          }
        }
        if (elementsFound < pageConfig.expected_elements.length) {
          if (status === 'PASS') status = 'DEGRADED';
        }
      }

      // Capture screenshot
      const screenshotName = `${pageConfig.name.replace(/[^a-zA-Z0-9]/g, '-')}.png`;
      screenshotPath = path.join(artifacts_dir, screenshotName);
      await page.screenshot({ path: screenshotPath, fullPage: false });

      results.push({
        path: pageConfig.path,
        name: pageConfig.name,
        status,
        load_time_ms: loadTimeMs,
        console_errors: consoleErrors.length,
        console_error_messages: consoleErrors.slice(0, 10),
        elements_found: elementsFound,
        elements_expected: (pageConfig.expected_elements || []).length,
        title_match: titleMatch,
        screenshot_path: screenshotPath,
        error: null,
      });

    } catch (e) {
      // Timeout or navigation error
      const loadTimeMs = Date.now() - startTime;

      // Try to capture screenshot even on error
      try {
        const screenshotName = `${pageConfig.name.replace(/[^a-zA-Z0-9]/g, '-')}-error.png`;
        screenshotPath = path.join(artifacts_dir, screenshotName);
        await page.screenshot({ path: screenshotPath });
      } catch (_) {
        screenshotPath = null;
      }

      results.push({
        path: pageConfig.path,
        name: pageConfig.name,
        status: e.message.includes('Timeout') ? 'TIMEOUT' : 'ERROR',
        load_time_ms: loadTimeMs,
        console_errors: consoleErrors.length,
        console_error_messages: consoleErrors.slice(0, 10),
        elements_found: 0,
        elements_expected: (pageConfig.expected_elements || []).length,
        title_match: null,
        screenshot_path: screenshotPath,
        error: e.message.substring(0, 200),
      });
    }

    await page.close();
  }

  await context.close();
  await browser.close();

  // Output results as JSON to stdout
  console.log(JSON.stringify({ pages: results }));
}

function findChromium() {
  // Check common Playwright Chromium locations
  const localAppData = process.env.LOCALAPPDATA || '';
  const candidates = [
    path.join(localAppData, 'ms-playwright', 'chromium-1223', 'chrome-win64', 'chrome.exe'),
    path.join(localAppData, 'ms-playwright', 'chromium-1148', 'chrome-win64', 'chrome.exe'),
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/usr/bin/google-chrome',
  ];

  // Also check via glob for any chromium version
  if (localAppData) {
    try {
      const msPlaywright = path.join(localAppData, 'ms-playwright');
      if (fs.existsSync(msPlaywright)) {
        const dirs = fs.readdirSync(msPlaywright).filter(d => d.startsWith('chromium-'));
        for (const dir of dirs.sort().reverse()) {
          const exe = path.join(msPlaywright, dir, 'chrome-win64', 'chrome.exe');
          if (fs.existsSync(exe)) return exe;
          const exeLinux = path.join(msPlaywright, dir, 'chrome-linux', 'chrome');
          if (fs.existsSync(exeLinux)) return exeLinux;
        }
      }
    } catch (_) {}
  }

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }

  return null; // Let Playwright find its own
}

main().catch(e => {
  process.stderr.write(`Worker error: ${e.message}\n`);
  process.exit(1);
});
