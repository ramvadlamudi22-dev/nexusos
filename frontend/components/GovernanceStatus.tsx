"use client";

import { useEffect, useState } from "react";
import { fetchGovernanceStatus, GovernanceStatusResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function GovernanceStatus() {
  const [data, setData] = useState<GovernanceStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchGovernanceStatus({ signal: controller.signal })
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
        Governance Status
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <p>
              Engine:{" "}
              <strong style={{ color: data.active ? "#3fb950" : "#f85149" }}>
                {data.active ? "Active" : "Inactive"}
              </strong>
            </p>
            <span
              style={{
                display: "inline-block",
                padding: "2px 8px",
                borderRadius: "12px",
                fontSize: "0.7rem",
                fontWeight: 600,
                background: data.active ? "#3fb95020" : "#f8514920",
                color: data.active ? "#3fb950" : "#f85149",
              }}
            >
              {data.active ? "Active" : "Inactive"}
            </span>
          </div>
          <p style={{ marginTop: "4px" }}>
            Policies: {data.policy_count}
          </p>
          <p style={{ marginTop: "4px", fontSize: "0.8rem", color: "#8b949e" }}>
            Audit: <span style={{ color: "#3fb950" }}>Active Enforcement</span>
          </p>
          {data.policies.length > 0 && (
            <ul style={{ listStyle: "none", marginTop: "8px" }}>
              {data.policies.map((p) => (
                <li key={p.id} style={{ marginBottom: "4px", fontSize: "0.85rem" }}>
                  {p.name} -{" "}
                  <span style={{ color: p.active ? "#3fb950" : "#8b949e" }}>
                    {p.active ? "active" : "inactive"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
