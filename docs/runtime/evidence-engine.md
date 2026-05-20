# Evidence & Proof Engine

**Module:** `nexusos.runtime.evidence`  
**Principle:** Every execution produces verifiable proof. No claim without evidence.

---

## Evidence Types

| Type | Format | Content | Retention |
|------|--------|---------|-----------|
| Screenshot | PNG | Visual state of page at moment | 90 days |
| Trace | ZIP | DOM snapshots + network + actions | 14 days |
| Video | WebM | Full session recording | 30 days |
| Telemetry snapshot | JSON | Metrics at execution time | 30 days |
| Replay manifest | JSON | Complete replay recipe | 1 year |
| Runtime evidence bundle | ZIP | All artifacts for one run | 90 days |
| Workflow audit report | JSON | Governance decisions + results | Forever |

---

## Evidence Production Pipeline

```
Execution Start
    │
    ├── [Continuous] Video recording (if enabled)
    ├── [Continuous] Trace capture (DOM + network)
    ├── [Continuous] Telemetry emission
    │
    ├── Per-Node Execution
    │   ├── Pre-execution screenshot (optional)
    │   ├── Node execution
    │   ├── Post-execution screenshot
    │   ├── Node result artifact
    │   └── Governance decision record
    │
    ├── Execution Complete
    │   ├── Stop video recording → video artifact
    │   ├── Stop trace → trace artifact
    │   ├── Compile telemetry snapshot
    │   ├── Generate workflow audit report
    │   ├── Generate replay manifest
    │   └── Bundle all into evidence package
    │
    └── Evidence Finalization
        ├── Compute content hashes for all artifacts
        ├── Generate proof manifest (links all hashes)
        ├── Compute manifest hash (integrity seal)
        └── Store with lineage metadata
```

---

## Proof Manifest Structure

The proof manifest is the anchor document that proves an execution occurred and produced specific results:

```typescript
interface ProofManifest {
  // Identity
  manifest_id: string;
  manifest_version: "1.0.0";
  
  // Execution context
  execution_id: string;
  workflow_name: string;
  target: string;                    // What was verified
  timestamp: string;
  duration_ms: number;
  
  // Verdict
  verdict: "PASS" | "FAIL" | "DEGRADED";
  score: number;                     // 0-100
  
  // Evidence chain (ordered)
  evidence: EvidenceItem[];
  
  // Integrity
  evidence_hashes: string[];         // All artifact hashes in order
  combined_hash: string;             // SHA-256 of all hashes concatenated
  
  // Governance proof
  governance_decisions: number;
  all_permitted: boolean;
  audit_chain_valid: boolean;
  
  // Reproducibility
  replay_manifest_ref: string;       // Reference to replay manifest
  determinism_score: number;         // 0-1
}

interface EvidenceItem {
  sequence: number;
  type: EvidenceType;
  name: string;
  path: string;
  content_hash: string;              // SHA-256 of file content
  size_bytes: number;
  produced_by: string;               // Node ID or component
  timestamp: string;
  metadata: Record<string, unknown>;
}
```

---

## Runtime Evidence Bundles

A complete evidence bundle for one execution:

```
evidence-bundle-{execution_id}/
├── manifest.json                    # Proof manifest (integrity anchor)
├── report.json                      # Structured verification results
├── report.md                        # Human-readable summary
├── screenshots/
│   ├── 001-homepage.png
│   ├── 002-dashboard.png
│   └── 003-settings.png
├── video/
│   └── walkthrough.webm
├── traces/
│   └── execution-trace.zip
├── telemetry/
│   └── metrics-snapshot.json
├── governance/
│   └── audit-records.json
├── replay/
│   └── replay-manifest.json
└── checksums.sha256                 # All file hashes for verification
```

---

## Verification Command

```bash
# Verify evidence bundle integrity
nexusos verify-evidence ./evidence-bundle-exec-001/

# Output:
# Verifying evidence bundle: exec-001
# ✓ manifest.json: valid structure
# ✓ 001-homepage.png: hash matches (sha256:ab3f7c...)
# ✓ 002-dashboard.png: hash matches (sha256:cd91e2...)
# ✓ 003-settings.png: hash matches (sha256:ef45a1...)
# ✓ walkthrough.webm: hash matches (sha256:12bc34...)
# ✓ execution-trace.zip: hash matches (sha256:56de78...)
# ✓ Combined hash: valid
# ✓ Governance chain: intact
#
# Verdict: EVIDENCE INTEGRITY CONFIRMED
# All 7 artifacts verified. No tampering detected.
```

---

## Workflow Audit Reports

```typescript
interface WorkflowAuditReport {
  execution_id: string;
  workflow_name: string;
  timestamp: string;
  
  // Execution summary
  nodes_executed: number;
  nodes_succeeded: number;
  nodes_failed: number;
  nodes_retried: number;
  total_duration_ms: number;
  
  // Governance summary
  governance_checks: number;
  governance_permits: number;
  governance_denials: number;
  policies_evaluated: string[];
  
  // Evidence summary
  artifacts_produced: number;
  screenshots: number;
  videos: number;
  traces: number;
  
  // Integrity
  audit_chain_length: number;
  audit_chain_valid: boolean;
  all_checksums_valid: boolean;
  
  // Compliance
  execution_governed: boolean;       // All ops passed governance
  execution_audited: boolean;        // All decisions recorded
  execution_replayable: boolean;     // Replay manifest exists
  evidence_complete: boolean;        // All expected artifacts present
}
```

---

## Evidence API

```
GET  /api/evidence/runs                          → List evidence bundles
GET  /api/evidence/runs/{id}                     → Get bundle metadata
GET  /api/evidence/runs/{id}/manifest            → Get proof manifest
GET  /api/evidence/runs/{id}/artifacts           → List artifacts
GET  /api/evidence/runs/{id}/artifacts/{name}    → Download artifact
GET  /api/evidence/runs/{id}/report              → Get audit report
POST /api/evidence/runs/{id}/verify              → Verify bundle integrity
GET  /api/evidence/runs/{id}/replay-manifest     → Get replay recipe
```

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Screenshots | Playwright page.screenshot() | ✓ Working |
| Videos | Playwright recordVideo | ✓ Working |
| Traces | Playwright tracing | ✓ Working |
| Audit records | `AuditLogger` with checksums | ✓ Working |
| Telemetry | `TelemetryCollector` | Add snapshot export |
| Proof manifests | Markdown reports | Formalize as JSON |
| Evidence bundles | artifacts/ directory | Add structure + manifest |
| Verification | Not implemented | New: hash verification CLI |
| Replay manifests | Not implemented | New: replay recipe generation |
| Bundle API | Not implemented | New: evidence access endpoints |
