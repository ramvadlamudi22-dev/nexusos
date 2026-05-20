"use client";

import { useEffect, useState } from "react";
import { fetchExecutionTelemetry, ExecutionTelemetryResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function ExecutionTelemetry() {
  const [data, setData] = useState<ExecutionTelemetryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchExecutionTelemetry({ signal: controller.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const errorRate =
    data && data.metrics.total_operations > 0
      ? ((data.metrics.total_errors / data.metrics.total_operations) * 100).toFixed(1)
      : "0.0";

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Execution Telemetry
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p>
            Total operations: <strong>{data.metrics.total_operations}</strong>
          </p>
          <p>
            Total errors:{" "}
            <strong style={{ color: data.metrics.total_errors > 0 ? "#f85149" : "#3fb950" }}>
              {data.metrics.total_errors}
            </strong>
          </p>
          <p style={{ marginTop: "4px", fontSize: "0.85rem" }}>
            Error rate:{" "}
            <strong style={{ color: parseFloat(errorRate) > 5 ? "#f85149" : "#3fb950" }}>
              {errorRate}%
            </strong>
          </p>
          {data.metrics.total_operations > 0 && (
            <div style={{ marginTop: "10px" }}>
              <div style={{ fontSize: "0.75rem", color: "#8b949e", marginBottom: "4px" }}>
                Operations
              </div>
              <div
                style={{
                  height: "6px",
                  background: "#21262d",
                  borderRadius: "3px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${Math.min(100, data.metrics.total_operations * 10)}%`,
                    background: "#58a6ff",
                    borderRadius: "3px",
                  }}
                />
              </div>
              {data.metrics.total_errors > 0 && (
                <>
                  <div style={{ fontSize: "0.75rem", color: "#8b949e", marginBottom: "4px", marginTop: "6px" }}>
                    Errors
                  </div>
                  <div
                    style={{
                      height: "6px",
                      background: "#21262d",
                      borderRadius: "3px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.min(100, data.metrics.total_errors * 10)}%`,
                        background: "#f85149",
                        borderRadius: "3px",
                      }}
                    />
                  </div>
                </>
              )}
            </div>
          )}
          <ul style={{ listStyle: "none", marginTop: "10px", padding: 0 }}>
            {Object.entries(data.health).map(([runtime, info]) => (
              <li key={runtime} style={{ marginBottom: "4px" }}>
                {runtime}:{" "}
                <span
                  style={{
                    color:
                      info.status === "healthy"
                        ? "#3fb950"
                        : info.status === "idle"
                        ? "#8b949e"
                        : "#f85149",
                  }}
                >
                  {info.status}
                </span>{" "}
                ({info.total_operations} ops)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
