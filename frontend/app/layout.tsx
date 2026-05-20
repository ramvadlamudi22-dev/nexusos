import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusOS Dashboard",
  description: "Runtime monitoring dashboard for NexusOS",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
        <header
          style={{
            background: "#161b22",
            borderBottom: "1px solid #30363d",
            padding: "12px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
            <span style={{ fontWeight: 700, fontSize: "1.1rem", color: "#e6edf3" }}>
              NexusOS
            </span>
            <nav style={{ display: "flex", gap: "16px" }}>
              <a href="/" style={{ color: "#c9d1d9", textDecoration: "none", fontSize: "0.9rem" }}>
                Dashboard
              </a>
              <a href="/landing" style={{ color: "#c9d1d9", textDecoration: "none", fontSize: "0.9rem" }}>
                Overview
              </a>
              <a href="/docs" style={{ color: "#c9d1d9", textDecoration: "none", fontSize: "0.9rem" }}>
                API Docs
              </a>
            </nav>
          </div>
        </header>
        <main style={{ flex: 1 }}>{children}</main>
        <footer
          style={{
            background: "#161b22",
            borderTop: "1px solid #30363d",
            padding: "12px 24px",
            textAlign: "center",
            fontSize: "0.8rem",
            color: "#8b949e",
          }}
        >
          NexusOS v0.2.0 - Governed AI Execution Runtime
        </footer>
      </body>
    </html>
  );
}
