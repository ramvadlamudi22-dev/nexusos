# Artifact Intelligence

**Module:** `nexusos.runtime.artifacts`  
**Version:** 2.0  
**Principle:** Every operation produces verifiable evidence. Artifacts are structured operational memory.

---

## Design Intent

Artifact Intelligence transforms raw execution outputs into structured, searchable, lineage-tracked operational evidence. Every screenshot, video, trace, log, and report is a first-class entity with provenance, integrity verification, and execution context. Artifacts are not files — they are evidence.

---

## Artifact Model

```typescript
interface Artifact {
  id: string;                        // SHA-256 of content bytes
  type: ArtifactType;
  name: string;
  mime_type: string;
  size_bytes: number;
  content_hash: string;              // SHA-256 (same as id for content-addressed)
  storage_path: string;
  created_at: string;
  
  // Provenance
  execution_id: string;              // Which execution produced this
  graph_id: string | null;           // Which graph
  node_id: string | null;            // Which node
  agent_id: string | null;           // Which agent
  
  // Lineage
  lineage: ArtifactLineage;
  
  // Metadata
  metadata: ArtifactMetadata;
  tags: string[];
  
  // Lifecycle
  retention: RetentionPolicy;
  verified: boolean;                 // Integrity verified
  archived: boolean;
}

enum ArtifactType {
  SCREENSHOT       = "SCREENSHOT",
  VIDEO            = "VIDEO",
  TRACE            = "TRACE",
  LOG              = "LOG",
  REPORT           = "REPORT",
  SNAPSHOT         = "SNAPSHOT",
  MANIFEST         = "MANIFEST",
  TELEMETRY_EXPORT = "TELEMETRY_EXPORT",
  AUDIT_EXPORT     = "AUDIT_EXPORT",
  REPLAY_SESSION   = "REPLAY_SESSION",
  CHECKPOINT       = "CHECKPOINT",
  DIAGNOSTIC       = "DIAGNOSTIC",
  PROOF            = "PROOF",
}
```

---

## Lineage Tracking

```typescript
interface ArtifactLineage {
  // What produced this artifact
  producer: {
    component: string;             // e.g., "browser_runtime"
    operation: string;             // e.g., "screenshot"
    execution_id: string;
    node_id: string | null;
  };
  
  // Input artifacts (what was consumed to produce this)
  inputs: string[];                // Artifact IDs
  
  // Causal chain (ordered operations leading to this artifact)
  causal_chain: {
    operation_id: string;
    operation: string;
    timestamp: string;
  }[];
  
  // Derived artifacts (what was produced from this)
  derived_from_this: string[];     // Populated over time
}
```

### Lineage Graph

```
[Workflow Definition] ──produces──→ [Execution Manifest]
        │                                    │
        └──triggers──→ [Browser Session] ────┤
                            │                │
                            ├──→ [Screenshot 1]
                            ├──→ [Screenshot 2]
                            ├──→ [Video Recording]
                            └──→ [Trace File]
                                      │
                                      └──→ [Replay Session]
                                                │
                                                └──→ [Verification Report]
```

---

## Evidence Storage Architecture

```
artifacts/
├── store/                           # Content-addressed storage
│   ├── ab/                          # First 2 chars of hash
│   │   └── ab3f7c...               # Full content hash as filename
│   ├── cd/
│   │   └── cd91e2...
│   └── ...
│
├── index/                           # Metadata index
│   ├── by-execution/                # Execution → artifacts mapping
│   │   └── {execution_id}.json
│   ├── by-type/                     # Type → artifacts mapping
│   │   ├── screenshots.json
│   │   ├── videos.json
│   │   └── traces.json
│   ├── by-time/                     # Time-bucketed index
│   │   └── 2026-05-19.json
│   └── lineage/                     # Lineage graph
│       └── {artifact_id}.json
│
├── manifests/                       # Run manifests
│   └── {run_id}.json
│
└── proofs/                          # Execution proofs (permanent)
    └── {proof_id}.json
```

---

## Proof Manifests

Every significant execution produces a proof manifest:

```typescript
interface ProofManifest {
  id: string;
  type: "EXECUTION_PROOF" | "GOVERNANCE_PROOF" | "REPLAY_PROOF";
  execution_id: string;
  timestamp: string;
  
  // Evidence chain
  artifacts: {
    id: string;
    type: ArtifactType;
    content_hash: string;
    role: string;                   // e.g., "primary_evidence", "supporting"
  }[];
  
  // Verification
  governance_decisions: string[];   // Decision IDs
  audit_records: string[];          // Audit record IDs
  
  // Integrity
  manifest_hash: string;            // SHA-256 of all artifact hashes concatenated
  signature: string | null;         // Optional cryptographic signature
  
  // Reproducibility
  replay_session_id: string | null; // Can be replayed
  graph_checksum: string;           // Graph that produced this
}
```

---

## Searchable Runtime Memory

```typescript
interface ArtifactQuery {
  // Filter by provenance
  execution_id?: string;
  graph_id?: string;
  node_id?: string;
  agent_id?: string;
  
  // Filter by type
  types?: ArtifactType[];
  
  // Filter by time
  created_after?: string;
  created_before?: string;
  
  // Filter by metadata
  tags?: string[];
  metadata_match?: Record<string, string>;
  
  // Lineage queries
  produced_by?: string;            // Artifact ID (find derivatives)
  consumed_by?: string;            // Artifact ID (find inputs)
  
  // Pagination
  limit?: number;
  offset?: number;
  sort_by?: "created_at" | "size" | "type";
}
```

### Query Examples

```
// All screenshots from a specific workflow execution
{ execution_id: "exec-001", types: ["SCREENSHOT"] }

// All artifacts produced in the last hour
{ created_after: "2026-05-19T17:00:00Z" }

// Lineage: what was this screenshot derived from?
{ produced_by: "art-screenshot-001" }  // Returns workflow, browser session

// All proof manifests for governance decisions
{ types: ["PROOF"], tags: ["governance"] }
```

---

## Retention Policies

```typescript
interface RetentionPolicy {
  id: string;
  name: string;
  applies_to: ArtifactType[];
  strategy: RetentionStrategy;
  archive_before_delete: boolean;
  governance_override: boolean;    // Governance artifacts exempt from deletion
}

type RetentionStrategy = 
  | { type: "KEEP_FOREVER" }
  | { type: "TTL"; days: number }
  | { type: "COUNT_LIMIT"; max_per_execution: number }
  | { type: "SIZE_LIMIT"; max_total_bytes: number }
  | { type: "CONDITIONAL"; condition: string };  // Expression-based
```

### Default Retention

| Artifact Type | Retention | Rationale |
|--------------|-----------|-----------|
| PROOF | Forever | Legal/compliance evidence |
| AUDIT_EXPORT | Forever | Governance integrity |
| MANIFEST | 1 year | Execution history |
| VIDEO | 30 days | Storage-intensive |
| TRACE | 14 days | Large files |
| SCREENSHOT | 30 days | Moderate size |
| LOG | 7 days | High volume |
| CHECKPOINT | 3 days | Transient state |
| DIAGNOSTIC | 14 days | Debugging context |

---

## Artifact API

```
POST /api/artifacts                              → Store new artifact
GET  /api/artifacts                              → Query artifacts
GET  /api/artifacts/{id}                         → Get artifact metadata
GET  /api/artifacts/{id}/content                 → Download artifact content
GET  /api/artifacts/{id}/lineage                 → Get lineage graph
GET  /api/artifacts/by-execution/{execution_id}  → All artifacts for execution
GET  /api/artifacts/proofs                       → List proof manifests
GET  /api/artifacts/proofs/{id}                  → Get proof manifest
POST /api/artifacts/verify/{id}                  → Verify artifact integrity
DELETE /api/artifacts/{id}                        → Delete (governance-gated)
```

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Artifact storage | File system (artifacts/ directory) | Add content-addressing, index |
| Screenshots | Playwright page.screenshot() | Add metadata, lineage |
| Videos | Playwright recordVideo | Add execution linking |
| Traces | Playwright tracing | Add artifact registration |
| Proof manifests | runtime-proof-report.md | Formalize as structured data |
| Lineage | Not implemented | New: provenance tracking |
| Search | Not implemented | New: query engine |
| Retention | Not implemented | New: lifecycle management |
| Integrity | SHA-256 in audit records | Extend to all artifacts |
