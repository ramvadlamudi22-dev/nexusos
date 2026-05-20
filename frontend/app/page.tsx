import RuntimeHealth from "@/components/RuntimeHealth";
import EventStream from "@/components/EventStream";
import GovernanceStatus from "@/components/GovernanceStatus";
import TelemetryOverview from "@/components/TelemetryOverview";
import WorkflowView from "@/components/WorkflowView";
import BrowserStatus from "@/components/BrowserStatus";
import TerminalStatus from "@/components/TerminalStatus";
import ExecutionTelemetry from "@/components/ExecutionTelemetry";
import ReplayInspection from "@/components/ReplayInspection";
import WorkflowHistory from "@/components/WorkflowHistory";
import SystemBanner from "@/components/SystemBanner";
import DemoRunner from "@/components/DemoRunner";
import AuditTrail from "@/components/AuditTrail";
import VerificationPanel from "@/components/VerificationPanel";

export default function DashboardPage() {
  return (
    <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ marginBottom: "24px", fontSize: "1.5rem" }}>
        NexusOS Dashboard
      </h1>

      <SystemBanner />

      <div style={{ marginTop: "24px" }}>
        <VerificationPanel />
      </div>

      <div style={{ marginTop: "24px" }}>
        <h3 className="section-header">System Health</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          <RuntimeHealth />
          <GovernanceStatus />
          <AuditTrail />
          <TelemetryOverview />
        </div>
      </div>

      <div style={{ marginTop: "24px" }}>
        <h3 className="section-header">Execution Runtime</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          <ExecutionTelemetry />
          <BrowserStatus />
          <TerminalStatus />
        </div>
      </div>

      <div style={{ marginTop: "24px" }}>
        <h3 className="section-header">Orchestration &amp; Replay</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          <WorkflowView />
          <WorkflowHistory />
          <EventStream />
          <ReplayInspection />
        </div>
      </div>

      <div style={{ marginTop: "24px" }}>
        <h3 className="section-header">Demo Workflows</h3>
        <DemoRunner />
      </div>
    </div>
  );
}
