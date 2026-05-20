"use client";

import { useEffect, useState } from "react";
import { fetchExecutionTelemetry, ExecutionTelemetryResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function TerminalStatus() {
  const [data, setData] = useState<ExecutionTelemetryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExecutionTelemetry()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Terminal Sessions
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p>
            Commands executed:{" "}
            <strong>{data.metrics.counters.terminal_commands || 0}</strong>
          </p>
          <p>
            Status:{" "}
            <span
              style={{
                color:
                  data.health.terminal?.status === "healthy"
                    ? "#3fb950"
                    : data.health.terminal?.status === "idle"
                    ? "#8b949e"
                    : "#f85149",
              }}
            >
              {data.health.terminal?.status || "idle"}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
