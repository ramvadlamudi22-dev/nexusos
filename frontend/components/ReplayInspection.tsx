"use client";

import { useState } from "react";
import { fetchReplay, ReplayResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

const inputStyle: React.CSSProperties = {
  padding: "6px 8px",
  background: "#0d1117",
  color: "#c9d1d9",
  border: "1px solid #30363d",
  borderRadius: "4px",
  fontSize: "0.85rem",
};

export default function ReplayInspection() {
  const [data, setData] = useState<ReplayResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionType, setSessionType] = useState("terminal");
  const [sessionId, setSessionId] = useState("");

  const handleFetch = () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    fetchReplay(sessionType, sessionId)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Replay Inspection
      </h2>
      <div style={{ marginBottom: "8px", display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
        <select
          value={sessionType}
          onChange={(e) => setSessionType(e.target.value)}
          style={inputStyle}
        >
          <option value="terminal">Terminal</option>
          <option value="browser">Browser</option>
          <option value="workflow">Workflow</option>
        </select>
        <input
          type="text"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Session ID"
          style={{ ...inputStyle, minWidth: "120px" }}
        />
        <button
          onClick={handleFetch}
          style={{
            padding: "6px 12px",
            background: "#238636",
            color: "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          Load
        </button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            Records:{" "}
            <span
              style={{
                display: "inline-block",
                padding: "2px 8px",
                borderRadius: "12px",
                fontSize: "0.75rem",
                fontWeight: 600,
                background: "#58a6ff20",
                color: "#58a6ff",
              }}
            >
              {data.total}
            </span>
          </p>
          <pre
            style={{
              fontSize: "0.75rem",
              overflow: "auto",
              maxHeight: "200px",
              background: "#0d1117",
              padding: "10px",
              borderRadius: "4px",
              marginTop: "8px",
              border: "1px solid #21262d",
            }}
          >
            {JSON.stringify(data.records, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
