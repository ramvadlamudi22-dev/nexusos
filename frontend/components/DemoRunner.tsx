"use client";

import { useState } from "react";
import { executeWorkflow } from "@/lib/api";

interface DemoWorkflow {
  id: string;
  name: string;
  stepCount: number;
  workflow: Record<string, unknown>;
}

interface DemoState {
  status: "idle" | "running" | "done" | "error";
  result?: Record<string, unknown>;
  error?: string;
}

const DEMOS: DemoWorkflow[] = [
  {
    id: "browser_automation",
    name: "Browser Automation",
    stepCount: 2,
    workflow: {
      workflow_id: "browser_automation",
      name: "Browser Automation",
      steps: [
        { id: "navigate", name: "Navigate", step_type: "BROWSER", config: { url: "https://example.com" }, depends_on: [] },
        { id: "screenshot", name: "Screenshot", step_type: "BROWSER", config: { action: "screenshot" }, depends_on: ["navigate"] },
      ],
    },
  },
  {
    id: "terminal_automation",
    name: "Terminal Automation",
    stepCount: 2,
    workflow: {
      workflow_id: "terminal_automation",
      name: "Terminal Automation",
      steps: [
        { id: "list_dir", name: "List Directory", step_type: "TERMINAL", config: { command: "ls -la", working_dir: "/tmp" }, depends_on: [] },
        { id: "echo", name: "Echo", step_type: "TERMINAL", config: { command: "echo hello", working_dir: "/tmp" }, depends_on: ["list_dir"] },
      ],
    },
  },
  {
    id: "orchestration_demo",
    name: "Orchestration (Diamond)",
    stepCount: 4,
    workflow: {
      workflow_id: "orchestration_demo",
      name: "Orchestration Diamond",
      steps: [
        { id: "A", name: "Step A", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: [] },
        { id: "B", name: "Step B", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: ["A"] },
        { id: "C", name: "Step C", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: ["A"] },
        { id: "D", name: "Step D", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: ["B", "C"] },
      ],
    },
  },
  {
    id: "governance_demo",
    name: "Governance Validation",
    stepCount: 2,
    workflow: {
      workflow_id: "governance_demo",
      name: "Governance Validation",
      steps: [
        { id: "validate", name: "Validate Policy", step_type: "CUSTOM", config: { action: "check_policy", policy: "default" }, depends_on: [] },
        { id: "audit", name: "Audit Log", step_type: "CUSTOM", config: { action: "audit_log" }, depends_on: ["validate"] },
      ],
    },
  },
  {
    id: "replay_demo",
    name: "Replay Demo",
    stepCount: 2,
    workflow: {
      workflow_id: "replay_demo",
      name: "Replay Demo",
      steps: [
        { id: "record", name: "Record Action", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: [] },
        { id: "replay", name: "Replay Action", step_type: "CUSTOM", config: { action: "replay_last" }, depends_on: ["record"] },
      ],
    },
  },
  {
    id: "telemetry_demo",
    name: "Telemetry Demo",
    stepCount: 3,
    workflow: {
      workflow_id: "telemetry_demo",
      name: "Telemetry Demo",
      steps: [
        { id: "browser_step", name: "Browser Navigate", step_type: "BROWSER", config: { url: "https://example.com" }, depends_on: [] },
        { id: "terminal_step", name: "Terminal Execute", step_type: "TERMINAL", config: { command: "echo telemetry", working_dir: "/tmp" }, depends_on: [] },
        { id: "skill_step", name: "Skill Execute", step_type: "SKILL", config: { skill_name: "noop" }, depends_on: ["browser_step", "terminal_step"] },
      ],
    },
  },
];

export default function DemoRunner() {
  const [states, setStates] = useState<Record<string, DemoState>>({});

  const runDemo = async (demo: DemoWorkflow) => {
    setStates((prev) => ({
      ...prev,
      [demo.id]: { status: "running" },
    }));

    try {
      const result = await executeWorkflow(demo.workflow);
      setStates((prev) => ({
        ...prev,
        [demo.id]: { status: "done", result: result as Record<string, unknown> },
      }));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setStates((prev) => ({
        ...prev,
        [demo.id]: { status: "error", error: message },
      }));
    }
  };

  const runAll = async () => {
    for (const demo of DEMOS) {
      await runDemo(demo);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "16px" }}>
        <button
          onClick={runAll}
          style={{
            background: "#58a6ff",
            color: "#0d1117",
            border: "none",
            borderRadius: "6px",
            padding: "8px 16px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Run All
        </button>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
        }}
      >
        {DEMOS.map((demo) => {
          const state = states[demo.id] || { status: "idle" };
          return (
            <div
              key={demo.id}
              style={{
                background: "#161b22",
                border: "1px solid #30363d",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <h4 style={{ margin: 0, color: "#e6edf3" }}>{demo.name}</h4>
                <span style={{ color: "#8b949e", fontSize: "0.85rem" }}>
                  {demo.stepCount} steps
                </span>
              </div>

              {state.status === "idle" && (
                <button
                  onClick={() => runDemo(demo)}
                  style={{
                    background: "transparent",
                    color: "#58a6ff",
                    border: "1px solid #58a6ff",
                    borderRadius: "6px",
                    padding: "6px 12px",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  Run
                </button>
              )}

              {state.status === "running" && (
                <span style={{ color: "#d29922", fontSize: "0.85rem" }}>Executing...</span>
              )}

              {state.status === "done" && state.result && (
                <div style={{ fontSize: "0.85rem", color: "#c9d1d9" }}>
                  <div style={{ color: "#3fb950", marginBottom: "4px" }}>Done</div>
                  <div>ID: {String(state.result.execution_id || "N/A")}</div>
                  <div>Status: {String(state.result.status || state.result.state || "completed")}</div>
                </div>
              )}

              {state.status === "error" && (
                <div style={{ fontSize: "0.85rem", color: "#f85149" }}>
                  Error: {state.error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
