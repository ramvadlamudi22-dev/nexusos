# Artifact Intelligence

**Module:** `nexusos.artifacts`  
**Status:** Architecture Specification  
**Principle:** Every operation produces verifiable proof artifacts with full lineage

---

## Overview

Artifact Intelligence transforms raw execution outputs (screenshots, videos, traces, logs) into structured operational intelligence. Every artifact is indexed, linked to its producing execution, and searchable by execution context.

---

## Artifact Schema

```
┌─────────────────────────────────────────────────────────┐
│                      Artifact                            │
├─────────────────────────────────────────────────────────┤
│  id: string (SHA-256 of content)                         │
│  type: SCREENSHOT | VIDEO | TRACE | LOG | REPORT |       │
│        SNAPSHOT | MANIFEST | TELEMETRY | PROOF           │
│  execution_id: string                                    │
│  workflow_id: string (optional)                           │
│  node_id: string (optional)                              │
│  timestamp: ISO string                                   │
│  content_hash: string (SHA-256)                          │
│  size_bytes: number                                      │
│  mime_type: string                                        │
│  storage_path: string                                    │
│  metadata: ArtifactMetadata                              │
│  lineage: ArtifactLineage                                │
│  retention: RetentionPolicy                              │
└─────────────────────────────────────────────────────────┘
```

### Artifact Metadata

```
┌─────────────────────────────────────────────────────────┐
│                  ArtifactMetadata                         │
├─────────────────────────────────────────────────────────┤
│  producer: string (component that created it)            │
│  context: Record<string, string>                         │
│  tags: string[]                                          │
│  resolution: {width, height} (for visual artifacts)      │
│  duration_ms: number (for temporal artifacts)            │
│  format: string (webm, png, json, zip, etc.)            │
│  compression: string (none, gzip, zstd)                  │
└─────────────────────────────────────────────────────────┘
```

### Artifact Lineage

```
┌─────────────────────────────────────────────────────────┐
│                  ArtifactLineage                          │
├─────────────────────────────────────────────────────────┤
│  parent_artifacts: string[] (input artifact IDs)         │
│  producing_operation: string                             │
│  execution_graph_id: string                              │
│  node_id: string                                         │
│  step_index: number                                      │
│  causal_chain: string[] (ordered operation IDs)          │
└─────────────────────────────────────────────────────────┘
```

---

## Artifact Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Produce  │───→│  Index   │───→│  Store   │───→│  Link    │
│          │    │          │    │          │    │          │
│ Runtime  │    │ Metadata │    │ Content  │    │ Lineage  │
│ creates  │    │ extracted│    │ persisted│    │ connected│
│ artifact │    │ hash calc│    │ path set │    │ to exec  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
                                                ┌──────────┐
                                                │  Query   │
                                                │          │
                                                │ Search   │
                                                │ by exec  │
                                                │ by type  │
                                                │ by time  │
                                                └──────────┘
```

---

## Execution Memory

Artifacts form a searchable execution memory:

```
Query: "All screenshots from workflow exec-abc123"
→ Returns: [screenshot-001.png, screenshot-002.png, ...]

Query: "All artifacts produced between T1 and T2"
→ Returns: [video.webm, trace.zip, report.md, ...]

Query: "Lineage of artifact art-xyz"
→ Returns: execution graph → node → inputs → parent artifacts

Query: "All failed workflow artifacts"
→ Returns: artifacts linked to FAILED execution states
```

---

## Run Manifests

Every execution run produces a manifest linking all artifacts:

```json
{
  "run_id": "run-2026-05-19-001",
  "execution_id": "exec-abc123",
  "workflow_id": "wf-diamond",
  "start_time": "2026-05-19T18:00:00Z",
  "end_time": "2026-05-19T18:00:05Z",
  "state": "COMPLETED",
  "artifacts": [
    {"id": "art-001", "type": "SCREENSHOT", "node": "init"},
    {"id": "art-002", "type": "TRACE", "node": "execute"},
    {"id": "art-003", "type": "VIDEO", "node": null},
    {"id": "art-004", "type": "REPORT", "node": null}
  ],
  "telemetry_summary": {...},
  "governance_summary": {...}
}
```

---

## Retention Policies

```
┌─────────────────────────────────────────────────────────┐
│                  RetentionPolicy                          │
├─────────────────────────────────────────────────────────┤
│  type: KEEP_FOREVER | TTL | COUNT_LIMIT | SIZE_LIMIT     │
│  ttl_days: number (for TTL type)                         │
│  max_count: number (for COUNT_LIMIT)                     │
│  max_size_bytes: number (for SIZE_LIMIT)                 │
│  priority: number (higher = kept longer in eviction)     │
│  archive_before_delete: boolean                          │
└─────────────────────────────────────────────────────────┘
```

Default policies:
- Governance audit artifacts: KEEP_FOREVER
- Execution proofs: TTL 90 days
- Screenshots: TTL 30 days
- Videos: TTL 14 days
- Traces: TTL 7 days
- Logs: TTL 3 days

---

## Storage Topology

```
artifacts/
├── index.json                    (global artifact index)
├── runs/
│   └── {run_id}/
│       ├── manifest.json         (run manifest)
│       └── artifacts/            (run-scoped artifacts)
├── by-type/
│   ├── screenshots/
│   ├── videos/
│   ├── traces/
│   ├── logs/
│   ├── reports/
│   └── proofs/
├── by-execution/
│   └── {execution_id}/          (symlinks to artifacts)
└── governance/
    └── audit/                    (permanent audit artifacts)
```

---

## Integration Points

| System | Role |
|--------|------|
| Execution Graph | Produces artifacts at each node completion |
| Replay Engine | Links replay sessions to source artifacts |
| Governance | Audit records stored as permanent artifacts |
| Telemetry | Metrics/traces stored as temporal artifacts |
| Self-Healing | Diagnostic artifacts produced during recovery |
| Browser Runtime | Screenshots, videos, DOM snapshots |
