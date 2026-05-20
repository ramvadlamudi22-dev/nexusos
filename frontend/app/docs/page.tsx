export default function DocsPage() {
  const cardStyle: React.CSSProperties = {
    background: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "24px",
  };

  const badgeStyle = (method: string): React.CSSProperties => ({
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: "4px",
    fontSize: "0.75rem",
    fontWeight: 700,
    marginRight: "8px",
    color: "#ffffff",
    background: method === "GET" ? "#238636" : "#1f6feb",
  });

  const endpoints = [
    {
      category: "System",
      items: [
        { method: "GET", path: "/api/status", description: "System status and component health" },
      ],
    },
    {
      category: "Runtime",
      items: [
        { method: "POST", path: "/api/runtime/register", description: "Register a new runtime" },
        { method: "GET", path: "/api/runtime/{id}/status", description: "Get runtime status" },
      ],
    },
    {
      category: "Events",
      items: [
        { method: "GET", path: "/api/events", description: "List recent events" },
        { method: "GET", path: "/api/events/{id}", description: "Get specific event" },
      ],
    },
    {
      category: "Governance",
      items: [
        { method: "GET", path: "/api/governance/status", description: "Governance engine status and policies" },
      ],
    },
    {
      category: "Telemetry",
      items: [
        { method: "GET", path: "/api/telemetry/status", description: "Telemetry collector status" },
        { method: "GET", path: "/api/telemetry/metrics", description: "Collected metrics" },
        { method: "GET", path: "/api/telemetry/health", description: "System health state" },
        { method: "GET", path: "/api/telemetry/executions", description: "Execution telemetry metrics" },
      ],
    },
    {
      category: "Workflow",
      items: [
        { method: "POST", path: "/api/workflow/execute", description: "Execute a workflow" },
        { method: "GET", path: "/api/workflow/{id}/status", description: "Workflow execution status" },
        { method: "GET", path: "/api/workflow/executions", description: "List all executions" },
      ],
    },
    {
      category: "Browser",
      items: [
        { method: "POST", path: "/api/browser/start", description: "Start a browser session" },
        { method: "GET", path: "/api/browser/sessions", description: "List browser sessions" },
        { method: "GET", path: "/api/browser/{id}/status", description: "Browser session status" },
        { method: "POST", path: "/api/browser/{id}/action", description: "Execute browser action" },
      ],
    },
    {
      category: "Terminal",
      items: [
        { method: "POST", path: "/api/terminal/execute", description: "Execute a terminal command" },
        { method: "GET", path: "/api/terminal/{id}/status", description: "Terminal session status" },
      ],
    },
    {
      category: "Skills",
      items: [
        { method: "GET", path: "/api/skills", description: "List registered skills" },
        { method: "POST", path: "/api/skills/invoke", description: "Invoke a skill" },
      ],
    },
    {
      category: "Replay",
      items: [
        { method: "GET", path: "/api/replay/{type}/{id}", description: "Get replay data for a session" },
      ],
    },
  ];

  return (
    <div style={{ padding: "48px 24px", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "12px", color: "#e6edf3" }}>
          API Documentation
        </h1>
        <p style={{ fontSize: "1rem", color: "#8b949e" }}>
          All endpoints are prefixed with <code style={{ color: "#c9d1d9" }}>/api</code>. See the{" "}
          <a href="/docs/api.md" style={{ color: "#58a6ff", textDecoration: "none" }}>
            full API documentation
          </a>{" "}
          for detailed request/response examples.
        </p>
      </div>

      {endpoints.map((group) => (
        <div key={group.category} style={cardStyle}>
          <h2 style={{ fontSize: "1.1rem", marginBottom: "12px", color: "#58a6ff" }}>
            {group.category}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {group.items.map((endpoint) => (
              <div
                key={endpoint.path + endpoint.method}
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "8px 0",
                  borderBottom: "1px solid #21262d",
                }}
              >
                <span style={badgeStyle(endpoint.method)}>{endpoint.method}</span>
                <code style={{ color: "#e6edf3", fontSize: "0.85rem", marginRight: "12px", minWidth: "240px" }}>
                  {endpoint.path}
                </code>
                <span style={{ color: "#8b949e", fontSize: "0.85rem" }}>
                  {endpoint.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div style={{ textAlign: "center", marginTop: "32px" }}>
        <a
          href="/"
          style={{
            display: "inline-block",
            padding: "10px 20px",
            background: "#238636",
            color: "#ffffff",
            borderRadius: "6px",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: "0.9rem",
          }}
        >
          Back to Dashboard
        </a>
      </div>
    </div>
  );
}
