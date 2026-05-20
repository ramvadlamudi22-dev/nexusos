# NexusOS

**Governed AI operational trust platform.** Verify deployments, audit AI agent actions, and produce tamper-evident proof — all with real browser rendering.

---

## What It Does

NexusOS verifies that your deployments work correctly by rendering pages in a real browser, capturing screenshots, checking APIs, and producing checksummed proof manifests.

```bash
npx nexusos verify https://your-app.com
```

```
╔══════════════════════════════════════════╗
║  NexusOS Verification                    ║
╚══════════════════════════════════════════╝
  Target: https://your-app.com
  Pages:  /

  ✅ / — 1286ms

  Verdict: ✅ PASS | Score: 100/100 | 1.9s
  Screenshots: ./nexusos-results/screenshots
  Report: ./nexusos-results/report.json
  Proof: 6026cdb3c660e361...
```

## Quick Start

### CLI

```bash
npx nexusos verify https://your-app.com --pages /,/dashboard,/pricing --apis /api/health
```

### GitHub Action

```yaml
- uses: nexusos/visual-verify@v1
  with:
    url: ${{ env.DEPLOY_URL }}
    pages: /,/dashboard
    api-endpoints: /api/health
```

### API

```bash
curl -X POST https://your-nexusos-instance/api/verify \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://your-app.com", "pages": [{"path": "/", "name": "Homepage"}]}'
```

## Features

- **Real browser rendering** — Chromium renders your pages with full JavaScript execution
- **Screenshot evidence** — Visual proof of page state at verification time
- **Visual regression detection** — Compares screenshots against baselines
- **API verification** — Checks endpoints return expected status codes and fields
- **Console error detection** — Catches JavaScript errors in your pages
- **Proof manifests** — SHA-256 checksummed evidence bundles
- **Governance audit trail** — Every verification action is validated and recorded
- **Retry logic** — Exponential backoff for transient failures
- **CI/CD integration** — GitHub Action with PR summaries
- **OpenTelemetry export** — Send traces to Datadog, Grafana, New Relic

## Self-Hosted

```bash
docker compose up -d
# Backend: http://localhost:8000
# Dashboard: http://localhost:3000
# Verify: POST http://localhost:8000/api/verify
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/verify` | POST | Run verification |
| `/api/verify/runs` | GET | List run history |
| `/api/verify/runs/{id}` | GET | Get run details |
| `/api/verify/runs/{id}/proof` | GET | Get proof manifest |
| `/api/verify/stats` | GET | Execution statistics |
| `/api/verify/templates` | GET | List workflow templates |
| `/api/verify/baselines` | GET | List visual baselines |
| `/api/health` | GET | System health |

## Architecture

```
Trigger → Governance → Chromium renders → Screenshots captured →
Visual diff → API checks → Score computed → Proof manifest →
Audit trail → Telemetry → Evidence persisted → Verdict returned
```

## License

MIT
