"use client";

import { useEffect, useState } from "react";
import { fetchWorkflowExecutions, WorkflowExecutionsResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

const badgeStyle = (color: string): React.CSSProperties => ({
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: "12px",
  fontSize: "0.75rem",
  fontWeight: 600,
  background: color + "20",
  color: color,
});

function stateColor(state: string): string {
  switch (state) {
    case "COMPLETED":
      return "#3fb950";
    case "RUNNING":
      return "#58a6ff";
    case "PENDING":
      return "#d29922";
    case "FAILED":
      return "#f85149";
    default:
      return "#8b949e";
  }
}

export default function WorkflowView() {
  const [data, setData] = useState<WorkflowExecutionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCurl, setShowCurl] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchWorkflowExecutions({ signal: controller.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Active Workflows
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p>Total executions: <strong>{data.total}</strong></p>
          {data.executions.length > 0 ? (
            <ul style={{ listStyle: "none", marginTop: "8px", padding: 0 }}>
              {data.executions.slice(0, 5).map((exec) => (
                <li key={exec.id} style={{ marginBottom: "6px" }}>
                  <span style={badgeStyle(stateColor(exec.state))}>
                    {exec.state}
                  </span>{" "}
                  <span style={{ fontSize: "0.85rem" }}>{exec.workflow_id}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: "#8b949e" }}>No workflows executed yet</p>
          )}
          <button
            onClick={() => setShowCurl(!showCurl)}
            style={{
              marginTop: "12px",
              padding: "4px 10px",
              background: "#21262d",
              color: "#c9d1d9",
              border: "1px solid #30363d",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "0.8rem",
            }}
          >
            {showCurl ? "Hide" : "Demo Execute"}
          </button>
          {showCurl && (
            <pre
              style={{
                marginTop: "8px",
                padding: "8px",
                background: "#0d1117",
                borderRadius: "4px",
                fontSize: "0.75rem",
                overflow: "auto",
                color: "#c9d1d9",
              }}
            >
{`curl -X POST http://localhost:8000/api/workflow/execute \\
  -H "Content-Type: application/json" \\
  -d '{"workflow_id": "example", "steps": [{"id": "s1", "action": "echo"}]}'`}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
