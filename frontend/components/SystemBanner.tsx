"use client";

import { useEffect, useState } from "react";

interface BannerData {
  overall: string;
  componentCount: number;
  eventCount: number;
  governanceActive: boolean;
}

export default function SystemBanner() {
  const [data, setData] = useState<BannerData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const loadData = () => {
      Promise.all([
        fetch("/api/telemetry/health", { signal: controller.signal }).then((r) => {
          if (!r.ok) throw new Error(`API error: ${r.status} ${r.statusText}`);
          return r.json();
        }),
        fetch("/api/status", { signal: controller.signal }).then((r) => {
          if (!r.ok) throw new Error(`API error: ${r.status} ${r.statusText}`);
          return r.json();
        }),
      ])
        .then(([health, status]) => {
          setData({
            overall: health.overall || "unknown",
            componentCount: Object.keys(health.components || {}).length,
            eventCount: status.components?.event_bus?.event_count ?? 0,
            governanceActive: status.components?.governance_engine?.active ?? false,
          });
        })
        .catch((err) => {
          if (err.name !== "AbortError") {
            setError(err.message);
          }
        });
    };

    loadData();
    const interval = setInterval(loadData, 15000);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  const isHealthy = data?.overall?.toLowerCase() === "healthy";

  return (
    <div
      style={{
        background: "#161b22",
        border: "1px solid #30363d",
        borderRadius: "8px",
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "12px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span
          style={{
            display: "inline-block",
            width: "10px",
            height: "10px",
            borderRadius: "50%",
            background: error ? "#f85149" : isHealthy ? "#3fb950" : "#d29922",
          }}
        />
        <strong style={{ color: "#e6edf3", fontSize: "1rem" }}>
          System: {error ? "Error" : data?.overall || "Loading..."}
        </strong>
      </div>
      {data && !error && (
        <div style={{ display: "flex", gap: "24px", fontSize: "0.85rem", color: "#8b949e" }}>
          <span>Components: <strong style={{ color: "#c9d1d9" }}>{data.componentCount}</strong></span>
          <span>Events: <strong style={{ color: "#c9d1d9" }}>{data.eventCount}</strong></span>
          <span>
            Governance:{" "}
            <strong style={{ color: data.governanceActive ? "#3fb950" : "#f85149" }}>
              {data.governanceActive ? "Active" : "Inactive"}
            </strong>
          </span>
        </div>
      )}
    </div>
  );
}
