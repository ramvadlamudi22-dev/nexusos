"use client";

import { useEffect, useState } from "react";
import { fetchMetrics, MetricsResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function TelemetryOverview() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchMetrics({ signal: controller.signal })
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
        Telemetry Overview
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p style={{ marginBottom: "8px" }}>Total metrics: {data.total}</p>
          {data.metrics.length === 0 ? (
            <p style={{ color: "#8b949e" }}>No metrics collected yet.</p>
          ) : (
            <ul style={{ listStyle: "none" }}>
              {data.metrics.slice(0, 10).map((m, idx) => (
                <li
                  key={idx}
                  style={{
                    marginBottom: "6px",
                    fontSize: "0.85rem",
                    borderBottom: "1px solid #21262d",
                    paddingBottom: "4px",
                  }}
                >
                  <span style={{ color: "#58a6ff" }}>{m.name}</span>:{" "}
                  <strong>{m.value}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
