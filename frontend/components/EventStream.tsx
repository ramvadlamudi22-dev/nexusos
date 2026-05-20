"use client";

import { useEffect, useState } from "react";
import { fetchEvents, EventsResponse } from "@/lib/api";

const panelStyle: React.CSSProperties = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: "8px",
  padding: "16px",
};

export default function EventStream() {
  const [data, setData] = useState<EventsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchEvents({ signal: controller.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  return (
    <div style={panelStyle}>
      <h2 style={{ fontSize: "1rem", marginBottom: "12px" }}>Event Stream</h2>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#f85149" }}>Error: {error}</p>}
      {data && (
        <div>
          <p style={{ marginBottom: "8px" }}>Total events: {data.total}</p>
          {data.events.length === 0 ? (
            <p style={{ color: "#8b949e" }}>No events recorded yet.</p>
          ) : (
            <ul style={{ listStyle: "none" }}>
              {data.events.slice(0, 10).map((event) => (
                <li
                  key={event.id}
                  style={{
                    marginBottom: "6px",
                    fontSize: "0.85rem",
                    borderBottom: "1px solid #21262d",
                    paddingBottom: "4px",
                  }}
                >
                  <span style={{ color: "#58a6ff" }}>[{event.event_type}]</span>{" "}
                  #{event.sequence} - {event.timestamp}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
