"use client";

import { useEffect, useState } from "react";
import { fetchBrowserSessions, BrowserSessionsResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function BrowserStatus() {
  const [data, setData] = useState<BrowserSessionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchBrowserSessions({ signal: controller.signal })
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
        Browser Sessions
      </h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p>Active sessions: <strong>{data.total}</strong></p>
          {data.sessions.length > 0 ? (
            <ul style={{ listStyle: "none", marginTop: "8px", padding: 0 }}>
              {data.sessions.slice(0, 5).map((session) => (
                <li key={session.id} style={{ marginBottom: "4px" }}>
                  <span style={{ color: session.state === "ACTIVE" ? "#3fb950" : "#8b949e" }}>
                    {session.state}
                  </span>{" "}
                  {session.url}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: "#8b949e" }}>No browser sessions active</p>
          )}
        </div>
      )}
    </div>
  );
}
