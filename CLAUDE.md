# CLAUDE.md - NexusOS Repository Operating Instructions

## NexusOS Identity

**NexusOS** is a unified governed operational runtime for AI systems.

It provides a deterministic, observable, and fully governed execution environment where every operation is controlled, traceable, and reproducible. NexusOS exists to ensure that AI system behavior is never uncontrolled, never opaque, and always verifiable.

## Governance-First Architecture Philosophy

- All system behavior is governed. There is no uncontrolled execution.
- Governance is not optional and is not layered on top of the system -- it is the foundation.
- Every component, operation, and interaction is subject to governance rules from inception.
- No code executes outside the governance boundary.
- Policy enforcement is structural, not advisory. The system cannot bypass governance by design.
- If governance cannot be applied to an operation, that operation must not proceed.

## Deterministic Operational Runtime Principles

- Every operation must produce the same result given the same inputs.
- No hidden state is permitted. All state must be explicit and inspectable.
- No non-deterministic behavior is allowed in the runtime.
- Side effects must be declared, controlled, and reproducible.
- Randomness, if required, must be seeded and recorded for replay.
- Time-dependent operations must use controlled, injectable time sources.

## Replayability

- All operations must be replayable from recorded inputs.
- Execution traces must be reproducible -- given the same trace inputs, the same outputs must result.
- Input recordings must capture all relevant context (parameters, state, configuration, environment).
- Replay must be a first-class operation, not a debugging afterthought.
- Divergence between original execution and replay constitutes a system defect.

## Observability

- Every system action must be observable, traceable, and auditable.
- No black-box execution is permitted. All internal decision paths must be inspectable.
- Structured logging is mandatory for all operations.
- Traces must link cause to effect across component boundaries.
- Metrics must be emitted for all significant operations (latency, throughput, error rates).
- Audit trails must be immutable and tamper-evident.

## Modular Infrastructure Rules

- Components must be independently deployable, testable, and replaceable.
- No monolithic coupling is permitted between system modules.
- Each module must define explicit interfaces (inputs, outputs, dependencies).
- Inter-module communication must use well-defined contracts.
- A module failure must not cascade to unrelated modules.
- Dependency injection is preferred over hard-coded dependencies.
- Module boundaries must align with governance boundaries.

## Verification Requirements

- All outputs must be verifiable. Correctness is proven, not assumed.
- Verification must be automated wherever possible.
- Tests must cover correctness, governance compliance, and determinism.
- Integration verification must confirm that composed modules maintain all guarantees.
- Verification failures block deployment -- no exceptions.
- Manual verification is acceptable only when automated verification is provably impossible.

## Proof Artifact Requirements

- Every significant operation must produce a proof artifact.
- Acceptable proof artifacts include: logs, execution traces, checksums, attestations, and signed records.
- Proof artifacts must be stored durably and associated with the operation that produced them.
- Proof artifacts must be independently verifiable without access to the producing system.
- The absence of a proof artifact for a governed operation constitutes a system defect.
- Proof artifacts must be tamper-evident (checksummed or cryptographically signed).

## Git Workflow Rules

- Only one permanent branch: `main`.
- All feature branches must be short-lived.
- Merge immediately after completion.
- Delete feature branches immediately after merge.
- Never create long-lived phase branches.
- Never create stacked dependency branches.
- Every commit to `main` must leave the system in a working state.
- Commit messages must be clear and descriptive of the change.

## Implementation Philosophy

Priorities are ordered strictly. When in conflict, higher-priority concerns override lower-priority ones:

1. **Simplicity** -- The simplest correct solution is always preferred.
2. **Operational Stability** -- The system must be reliable and predictable in operation.
3. **Governance** -- All behavior must be governed and controlled.
4. **Replayability** -- Operations must be reproducible from recorded inputs.
5. **Modular Architecture** -- Components must be independent and composable.
6. **Deterministic Execution** -- Same inputs must always produce same outputs.

## Anti-Patterns (Explicitly Avoided)

The following are explicitly rejected in NexusOS design and implementation:

- **AGI systems** -- NexusOS is not an artificial general intelligence system. It is a governed runtime.
- **Speculative autonomy** -- The system does not speculate, improvise, or act beyond its governed scope.
- **Uncontrolled execution systems** -- No component may execute without governance oversight.
- **Overengineering** -- Solutions must not be more complex than the problem requires. Abstraction for its own sake is rejected.
- **Ungoverned optimization** -- Performance improvements must not compromise governance, observability, or determinism.
- **Implicit behavior** -- All behavior must be explicit, declared, and inspectable. Magic is forbidden.
