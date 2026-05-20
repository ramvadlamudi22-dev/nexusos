export default function LandingPage() {
  const features = [
    {
      title: "Governance",
      description: "Every action validated against policies before execution. Strict enforcement with full audit trails.",
    },
    {
      title: "Replay",
      description: "All operations recorded for deterministic replay. Reproduce any execution exactly as it happened.",
    },
    {
      title: "Observability",
      description: "Full telemetry, event streaming, and health monitoring across all runtime components.",
    },
    {
      title: "Orchestration",
      description: "DAG-based workflow engine with state machines, dependency resolution, and governed step execution.",
    },
  ];

  const cardStyle: React.CSSProperties = {
    background: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "20px",
  };

  return (
    <div style={{ padding: "48px 24px", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: "48px" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "12px", color: "#e6edf3" }}>
          Governed AI Execution Runtime
        </h1>
        <p style={{ fontSize: "1.1rem", color: "#8b949e", maxWidth: "600px", margin: "0 auto" }}>
          Governance-first, deterministic, and replayable execution for AI agents.
          Every action validated, every operation recorded.
        </p>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "16px" }}>Key Features</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
          }}
        >
          {features.map((f) => (
            <div key={f.title} style={cardStyle}>
              <h3 style={{ fontSize: "1rem", marginBottom: "8px", color: "#58a6ff" }}>
                {f.title}
              </h3>
              <p style={{ fontSize: "0.85rem", color: "#8b949e" }}>{f.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "12px" }}>Architecture</h2>
        <div style={cardStyle}>
          <p style={{ fontSize: "0.9rem", color: "#c9d1d9", lineHeight: 1.6 }}>
            NexusOS uses a layered architecture: the RuntimeExecutionContext provides deterministic
            timestamps and context to all modules. The GovernanceEngine validates every action
            before execution. The EventBus dispatches events across the system. The
            TelemetryCollector aggregates metrics, and the ReplayRecorder captures all operations
            for deterministic replay. Runtimes (browser, terminal, skills) execute within governed
            contexts while the WorkflowEngine orchestrates multi-step operations.
          </p>
        </div>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "12px" }}>Quickstart</h2>
        <div style={{ ...cardStyle, fontFamily: "monospace" }}>
          <pre style={{ fontSize: "0.85rem", color: "#c9d1d9", overflow: "auto" }}>
{`# Clone and start
git clone <repository-url>
cd NexusOS
docker-compose up`}
          </pre>
        </div>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "16px" }}>Why NexusOS</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
          }}
        >
          <div style={cardStyle}>
            <h3 style={{ fontSize: "1rem", marginBottom: "8px", color: "#58a6ff" }}>
              Governance-First
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#8b949e" }}>
              Every action is validated by a policy engine before execution. No uncontrolled operations ever reach the runtime.
            </p>
          </div>
          <div style={cardStyle}>
            <h3 style={{ fontSize: "1rem", marginBottom: "8px", color: "#58a6ff" }}>
              Deterministic Replay
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#8b949e" }}>
              All operations are recorded and can be replayed exactly. Reproduce any execution to verify behavior.
            </p>
          </div>
          <div style={cardStyle}>
            <h3 style={{ fontSize: "1rem", marginBottom: "8px", color: "#58a6ff" }}>
              Full Observability
            </h3>
            <p style={{ fontSize: "0.85rem", color: "#8b949e" }}>
              Every operation is traceable and auditable. Integrated telemetry provides real-time metrics and health monitoring.
            </p>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "12px" }}>Deployment</h2>
        <div style={{ ...cardStyle, fontFamily: "monospace" }}>
          <pre style={{ fontSize: "0.85rem", color: "#c9d1d9", overflow: "auto" }}>
{`git clone https://github.com/ramvadlamudi22-dev/NexusOS.git
cd NexusOS
docker-compose up`}
          </pre>
        </div>
      </div>

      <div style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "1.2rem", marginBottom: "12px" }}>API Examples</h2>
        <div style={{ ...cardStyle, fontFamily: "monospace" }}>
          <pre style={{ fontSize: "0.85rem", color: "#c9d1d9", overflow: "auto" }}>
{`# Check system status
curl http://localhost:8000/api/status

# Execute a workflow
curl -X POST http://localhost:8000/api/workflow/execute \\
  -H "Content-Type: application/json" \\
  -d '{"name": "demo", "steps": [{"id": "s1", "step_type": "SKILL", "config": {"skill_name": "echo", "parameters": {"message": "hello"}}, "depends_on": []}]}'

# View telemetry metrics
curl http://localhost:8000/api/telemetry/metrics`}
          </pre>
        </div>
      </div>

      <div style={{ textAlign: "center", display: "flex", gap: "16px", justifyContent: "center" }}>
        <a
          href="/docs"
          style={{
            display: "inline-block",
            padding: "12px 24px",
            background: "#1f6feb",
            color: "#ffffff",
            borderRadius: "6px",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: "0.95rem",
          }}
        >
          Get Started
        </a>
        <a
          href="/"
          style={{
            display: "inline-block",
            padding: "12px 24px",
            background: "#238636",
            color: "#ffffff",
            borderRadius: "6px",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: "0.95rem",
          }}
        >
          Open Dashboard
        </a>
      </div>
    </div>
  );
}
