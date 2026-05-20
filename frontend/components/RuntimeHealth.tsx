"use client";

import { useEffect, useState } from "react";
import { HealthResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function RuntimeHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const loadData = () => {
      fetch("/api/telemetry/health", { signal: controller.signal })
        .then((r) => {
          if (!r.ok) throw new Error(`API error: ${r.status} ${r.statusText}`);
          return r.json();
        })
        .then((d) => {
          setData(d);
          setLastUpdated(new Date().toLocaleTimeString());
        })
        .catch((err) => {
          if (err.name !== "AbortError") {
            setError(err.message);
          }
        })
        .finally(() => setLoading(false));
    };

    loadData();
    const interval = setInterval(loadData, 10000);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  const dotColor =
    data?.overall?.toLowerCase() === "healthy"
      ? "#3fb950"
      : data?.overall?.toLowerCase() === "degraded"
      ? "#d29922"
      : "#f85149";

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Runtime Health
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: dotColor,
              }}
            />
            Overall:{" "}
            <strong
              style={{
                color: data.overall.toLowerCase() === "healthy" ? "#3fb950" : "#f85149",
              }}
            >
              {data.overall}
            </strong>
          </p>
          {Object.keys(data.components).length > 0 && (
            <ul style={{ listStyle: "none", marginTop: "8px" }}>
              {Object.entries(data.components).map(([name, state]) => (
                <li key={name} style={{ marginBottom: "4px" }}>
                  {name}: {state}
                </li>
              ))}
            </ul>
          )}
          {lastUpdated && (
            <p style={{ marginTop: "8px", fontSize: "0.75rem", color: "#8b949e" }}>
              Last updated: {lastUpdated}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
