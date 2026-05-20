/**
 * API client helper for NexusOS backend.
 * Base URL defaults to '' (same origin, proxied by Next.js rewrites in dev).
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export interface FetchOptions {
  signal?: AbortSignal;
}

async function fetchJSON<T>(path: string, options?: FetchOptions): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { signal: options?.signal });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface HealthResponse {
  overall: string;
  components: Record<string, string>;
}

export interface EventItem {
  id: string;
  event_type: string;
  timestamp: string;
  sequence: number;
  payload: Record<string, unknown>;
}

export interface EventsResponse {
  events: EventItem[];
  total: number;
}

export interface GovernanceStatusResponse {
  active: boolean;
  policy_count: number;
  policies: { id: string; name: string; active: boolean }[];
}

export interface MetricItem {
  name: string;
  value: number;
  timestamp: string;
  labels: Record<string, string>;
}

export interface MetricsResponse {
  metrics: MetricItem[];
  total: number;
}

export interface WorkflowExecutionItem {
  id: string;
  workflow_id: string;
  state: string;
  start_timestamp: string;
}

export interface WorkflowExecutionsResponse {
  executions: WorkflowExecutionItem[];
  total: number;
}

export interface BrowserSessionItem {
  id: string;
  url: string;
  state: string;
  creation_timestamp: string;
}

export interface BrowserSessionsResponse {
  sessions: BrowserSessionItem[];
  total: number;
}

export interface TerminalStatusResponse {
  id: string;
  state: string;
  command_count: number;
  creation_timestamp: string;
}

export interface ExecutionTelemetryResponse {
  metrics: {
    counters: Record<string, number>;
    errors: Record<string, number>;
    total_operations: number;
    total_errors: number;
  };
  health: Record<string, { status: string; total_operations: number; errors: number }>;
}

export interface SkillItem {
  id: string;
  name: string;
  description: string;
  version: string;
}

export interface SkillsResponse {
  skills: SkillItem[];
  total: number;
}

export interface ReplayResponse {
  session_type: string;
  session_id: string;
  records: Record<string, unknown>[];
  total: number;
}

export interface AuditRecordItem {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  resource: string;
  outcome: string;
  metadata: Record<string, unknown>;
  checksum: string;
}

export interface AuditTrailResponse {
  records: AuditRecordItem[];
  total: number;
}

async function postJSON<T>(path: string, body: unknown, options?: FetchOptions): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: options?.signal,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function executeWorkflow(workflow: unknown, options?: FetchOptions): Promise<unknown> {
  return postJSON("/api/workflow/execute", workflow, options);
}

export function fetchWorkflowStatus(executionId: string, options?: FetchOptions): Promise<unknown> {
  return fetchJSON(`/api/workflow/${executionId}/status`, options);
}

export function fetchHealth(options?: FetchOptions): Promise<HealthResponse> {
  return fetchJSON<HealthResponse>("/api/telemetry/health", options);
}

export function fetchEvents(options?: FetchOptions): Promise<EventsResponse> {
  return fetchJSON<EventsResponse>("/api/events", options);
}

export function fetchGovernanceStatus(options?: FetchOptions): Promise<GovernanceStatusResponse> {
  return fetchJSON<GovernanceStatusResponse>("/api/governance/status", options);
}

export function fetchMetrics(options?: FetchOptions): Promise<MetricsResponse> {
  return fetchJSON<MetricsResponse>("/api/telemetry/metrics", options);
}

export function fetchWorkflowExecutions(options?: FetchOptions): Promise<WorkflowExecutionsResponse> {
  return fetchJSON<WorkflowExecutionsResponse>("/api/workflow/executions", options);
}

export function fetchBrowserSessions(options?: FetchOptions): Promise<BrowserSessionsResponse> {
  return fetchJSON<BrowserSessionsResponse>("/api/browser/sessions", options);
}

export function fetchTerminalStatus(sessionId: string, options?: FetchOptions): Promise<TerminalStatusResponse> {
  return fetchJSON<TerminalStatusResponse>(`/api/terminal/${sessionId}/status`, options);
}

export function fetchExecutionTelemetry(options?: FetchOptions): Promise<ExecutionTelemetryResponse> {
  return fetchJSON<ExecutionTelemetryResponse>("/api/telemetry/executions", options);
}

export function fetchSkills(options?: FetchOptions): Promise<SkillsResponse> {
  return fetchJSON<SkillsResponse>("/api/skills", options);
}

export function fetchReplay(sessionType: string, sessionId: string, options?: FetchOptions): Promise<ReplayResponse> {
  return fetchJSON<ReplayResponse>(`/api/replay/${sessionType}/${sessionId}`, options);
}

export function fetchAuditTrail(options?: FetchOptions): Promise<AuditTrailResponse> {
  return fetchJSON<AuditTrailResponse>("/api/governance/audit", options);
}

// --- Verification API ---

export interface VerifyRunSummary {
  id: string;
  timestamp: string;
  target_url: string;
  verdict: string;
  score: number;
  duration_ms: number;
  pages_checked: number;
  apis_checked: number;
  retries: number;
}

export interface VerifyRunsResponse {
  runs: VerifyRunSummary[];
  total: number;
}

export interface VerifyRequestBody {
  target_url: string;
  pages?: { path: string; name?: string }[];
  api_checks?: { path: string; expected_status?: number }[];
}

export function fetchVerifyRuns(options?: FetchOptions): Promise<VerifyRunsResponse> {
  return fetchJSON<VerifyRunsResponse>("/api/verify/runs", options);
}

export function runVerification(body: VerifyRequestBody, options?: FetchOptions): Promise<unknown> {
  return postJSON("/api/verify", body, options);
}
