"use client";

import { useEffect, useState } from "react";
import {
  fetchVerifyRuns,
  runVerification,
  VerifyRunSummary,
} from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

const btnStyle: React.CSSProperties = {
  background: "#238636",
  color: "#fff",
  border: "none",
  borderRadius: "6px",
  padding: "8px 16px",
  cursor: "pointer",
  fontSize: "0.85rem",
  fontWeight: 600,
};

const inputStyle: React.CSSProperties = {
  background: "#0d1117",
  border: "1px solid #30363d",
  borderRadius: "6px",
  padding: "8px 12px",
  color: "#e6edf3",
  fontSize: "0.85rem",
  width: "100%",
  maxWidth: "400px",
};

function verdictColor(verdict: string): string {
  switch (verdict) {
    case "PASS":
      return "#3fb950";
    case "DEGRADED":
      return "#d29922";
    case "FAIL":
    case "ERROR":
      return "#f85149";
    default:
      return "#8b949e";
  }
}

function verdictIcon(verdict: string): string {
  switch (verdict) {
    case "PASS":
      return "✅";
    case "DEGRADED":
      return "⚠️";
    case "FAIL":
      return "❌";
    case "ERROR":
      return "🚫";
    default:
      return "❓";
  }
}

export default function VerificationPanel() {
  const [runs, setRuns] = useState<VerifyRunSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [targetUrl, setTargetUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadRuns = () => {
    fetchVerifyRuns()
      .then((data) => {
        setRuns(data.runs);
        setTotal(data.total);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRun = async () => {
    if (!targetUrl.trim()) return;
    setRunning(true);
    setError(null);
    try {
      await runVerification({ target_url: targetUrl.trim() });
      loadRuns();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>
        Deployment Verification
      </h2>

      {/* Run form */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
        }}
      >
        <input
          type="text"
          placeholder="https://your-app.com"
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleRun()}
          style={inputStyle}
          aria-label="Target URL"
        />
        <button
          onClick={handleRun}
          disabled={running || !targetUrl.trim()}
          style={{
            ...btnStyle,
            opacity: running || !targetUrl.trim() ? 0.5 : 1,
          }}
        >
          {running ? "Verifying..." : "▶ Verify"}
        </button>
      </div>

      {error && (
        <p style={{ color: "#f85149", fontSize: "0.8rem", marginBottom: "8px" }}>
          {error}
        </p>
      )}

      {/* Run history */}
      {loading && <p style={{ color: "#8b949e" }}>Loading...</p>}

      {!loading && runs.length === 0 && (
        <p style={{ color: "#8b949e", fontSize: "0.85rem" }}>
          No verification runs yet. Enter a URL above to start.
        </p>
      )}

      {runs.length > 0 && (
        <div>
          <p style={{ fontSize: "0.75rem", color: "#8b949e", marginBottom: "8px" }}>
            Total runs: {total}
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {runs.slice(0, 10).map((run) => (
              <div
                key={run.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "8px 12px",
                  background: "#0d1117",
                  borderRadius: "6px",
                  fontSize: "0.8rem",
                }}
              >
                <span>{verdictIcon(run.verdict)}</span>
                <span
                  style={{
                    color: verdictColor(run.verdict),
                    fontWeight: 600,
                    minWidth: "70px",
                  }}
                >
                  {run.verdict}
                </span>
                <span style={{ color: "#e6edf3", flex: 1 }}>
                  {run.target_url}
                </span>
                <span style={{ color: "#8b949e" }}>
                  {run.score}/100
                </span>
                <span style={{ color: "#8b949e" }}>
                  {(run.duration_ms / 1000).toFixed(1)}s
                </span>
                <span style={{ color: "#8b949e", fontSize: "0.7rem" }}>
                  {new Date(run.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
