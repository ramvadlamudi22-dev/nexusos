"use client";

import { useEffect, useState } from "react";
import { fetchWorkflowExecutions, WorkflowExecutionsResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function WorkflowHistory() {
  const [data, setData] = useState<WorkflowExecutionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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

  const completed = data?.executions.filter((e) => e.state === "COMPLETED") || [];

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Workflow History
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p>Completed: <strong>{completed.length}</strong></p>
          {completed.length > 0 ? (
            <ul style={{ listStyle: "none", marginTop: "8px", padding: 0 }}>
              {completed.slice(0, 10).map((exec) => (
                <li key={exec.id} style={{ marginBottom: "4px", fontSize: "0.85rem" }}>
                  <span style={{ color: "#3fb950" }}>OK</span>{" "}
                  {exec.workflow_id} - {exec.start_timestamp}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: "#8b949e" }}>No completed workflows</p>
          )}
        </div>
      )}
    </div>
  );
}
