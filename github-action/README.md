# NexusOS Visual Verify

Governed deployment verification with visual proof. Renders your pages in a real browser, captures screenshots, checks APIs, and produces a pass/fail verdict with audit trail.

## Usage

```yaml
- name: Verify Deployment
  uses: nexusos/visual-verify@v1
  with:
    url: ${{ env.DEPLOY_URL }}
    pages: /,/dashboard,/pricing
    api-endpoints: /api/health
    expected-title: My App
```

## What It Does

After your deployment completes, this action:

1. Launches Chromium and navigates to each page
2. Captures screenshots as visual proof
3. Checks for JavaScript console errors
4. Validates page titles and content
5. Checks API endpoints for expected responses
6. Produces a checksummed proof manifest
7. Posts results as a PR summary
8. Fails the workflow if verification fails

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | Yes | — | Target URL to verify |
| `pages` | No | `/` | Comma-separated paths to check |
| `api-endpoints` | No | — | Comma-separated API paths |
| `expected-title` | No | — | Expected page title substring |
| `viewport` | No | `1920x1080` | Browser viewport size |
| `timeout` | No | `30000` | Per-page timeout (ms) |
| `fail-on-console-errors` | No | `false` | Fail if JS errors detected |

## Outputs

| Output | Description |
|--------|-------------|
| `verdict` | PASS, FAIL, or DEGRADED |
| `score` | Verification score (0-100) |
| `duration` | Execution time in ms |
| `screenshots` | Path to screenshots directory |
| `report` | Path to JSON report |

## Example: Post-Deploy Verification

```yaml
name: Deploy and Verify
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        id: deploy
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}

      - name: Verify Deployment
        uses: nexusos/visual-verify@v1
        with:
          url: ${{ steps.deploy.outputs.preview-url }}
          pages: /,/dashboard
          api-endpoints: /api/health
          expected-title: My App

      - name: Upload Screenshots
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: verification-screenshots
          path: nexusos-artifacts/screenshots/
```

## Evidence & Audit

Every run produces:
- Screenshots of each verified page
- JSON report with timing, errors, and verdict
- SHA-256 checksummed proof manifest
- Governance validation record

The proof manifest can be independently verified — any modification to artifacts after generation is detectable.

## Local Development

Test locally with the CLI:

```bash
npx nexusos verify https://your-app.com --pages /,/dashboard
```
