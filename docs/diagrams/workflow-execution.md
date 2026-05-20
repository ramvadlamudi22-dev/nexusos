# NexusOS Workflow Execution

## Workflow Execution Lifecycle

A workflow moves through parsing, DAG resolution, and step-by-step governed execution.

```
Workflow Definition (YAML/JSON)
    |
    v
+------------------------+
| Workflow Parser        |
| - Validate structure   |
| - Extract steps        |
| - Extract dependencies |
+----------+-------------+
           |
           v
+------------------------+
| DAG Resolution         |
| - Build dependency     |
|   graph                |
| - Topological sort     |
| - Detect cycles        |
| - Determine execution  |
|   order                |
+----------+-------------+
           |
           v
+------------------------+
| Execution Planning     |
| - Identify parallel    |
|   steps (no deps)      |
| - Queue steps in       |
|   resolved order       |
+----------+-------------+
           |
           v
    +------+------+
    | For each    |
    | step in DAG |
    | order:      |
    +------+------+
           |
           v
+------------------------+
| Governance Check       |
| - Evaluate step action |
| - Check permissions    |
| - ALLOW or DENY        |
+----+----------+--------+
     |          |
  ALLOW       DENY
     |          |
     v          v
+--------+  +------------------+
| Execute|  | Mark step FAILED |
| Step   |  | Record denial    |
+---+----+  | Halt workflow    |
    |       +------------------+
    v
+------------------------+
| Runtime Dispatch       |
| - Route to correct     |
|   runtime:             |
|   - BrowserRuntime     |
|   - TerminalRuntime    |
|   - SkillRuntime       |
+----------+-------------+
           |
           v
+------------------------+
| Step Telemetry         |
| - Record duration      |
| - Record outcome       |
| - Record resource use  |
+----------+-------------+
           |
           v
+------------------------+
| Replay Recording       |
| - Capture step inputs  |
| - Capture step output  |
| - Capture context      |
+----------+-------------+
           |
           v
+------------------------+
| Step Complete          |
| - Update workflow      |
|   state                |
| - Unlock dependent     |
|   steps                |
| - Continue to next     |
+------------------------+
           |
           v
    (next step or done)
           |
           v
+------------------------+
| Workflow Complete       |
| - Final status         |
| - Aggregate telemetry  |
| - Full replay record   |
+------------------------+
```

## DAG Resolution Example

```
Workflow Definition:
  Step A: no dependencies
  Step B: depends on A
  Step C: depends on A
  Step D: depends on B, C

Resolution:
  Layer 0: [A]        (no dependencies, execute first)
  Layer 1: [B, C]     (depend only on A, can run in parallel)
  Layer 2: [D]        (depends on B and C, runs after both)

Execution Order:
  1. Execute A
  2. Execute B and C (parallel)
  3. Execute D
```

## Governance at Each Step

Every individual step in a workflow passes through governance independently:

```
+----------+    +----------+    +----------+    +----------+
| Step A   |    | Step B   |    | Step C   |    | Step D   |
+----+-----+    +----+-----+    +----+-----+    +----+-----+
     |               |               |               |
     v               v               v               v
+----+-----+    +----+-----+    +----+-----+    +----+-----+
| Govern   |    | Govern   |    | Govern   |    | Govern   |
| Check A  |    | Check B  |    | Check C  |    | Check D  |
+----+-----+    +----+-----+    +----+-----+    +----+-----+
     |               |               |               |
     v               v               v               v
  ALLOW           ALLOW           ALLOW           ALLOW
     |               |               |               |
     v               v               v               v
  Execute         Execute         Execute         Execute
```

If any step is denied by governance, the workflow halts at that point. Dependent steps do not execute.

## Workflow States

| State | Description |
|-------|-------------|
| `PENDING` | Workflow created, not yet started |
| `RUNNING` | Execution in progress |
| `COMPLETED` | All steps finished successfully |
| `FAILED` | A step failed or was denied by governance |
| `CANCELLED` | Workflow was manually cancelled |
