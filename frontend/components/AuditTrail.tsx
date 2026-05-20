"use client";

import { useEffect, useState } from "react";
import { fetchAuditTrail, AuditTrailResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function AuditTrail() {
  const [data, setData] = useState<AuditTrailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    const loadData = () => {
      fetchAuditTrail({ signal: controller.signal })
        .then(setData)
        .catch((err) => {
          if (err.name !== "AbortError") setError(err.message);
        })
        .finally(() => setLoading(false));
    };

    loadData();
    const interval = setInterval(loadData, 15000);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, []);

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Audit Trail
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p style={{ marginBottom: "8px", fontSize: "0.85rem", color: "#8b949e" }}>
            Total records: {data.total}
          </p>
          {data.records.length === 0 && (
            <p style={{ fontSize: "0.85rem", color: "#8b949e" }}>No audit records yet.</p>
          )}
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {data.records.map((record) => (
              <li
                key={record.id}
                style={{
                  marginBottom: "8px",
                  fontSize: "0.85rem",
                  borderBottom: "1px solid #21262d",
                  paddingBottom: "6px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontWeight: 600 }}>{record.action}</span>
                  <span
                    style={{
                      color: record.outcome === "permitted" ? "#3fb950" : "#f85149",
                      fontWeight: 600,
                    }}
                  >
                    {record.outcome}
                  </span>
                </div>
                <div style={{ color: "#8b949e", fontSize: "0.75rem", marginTop: "2px" }}>
                  Actor: {record.actor} | {record.timestamp}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
