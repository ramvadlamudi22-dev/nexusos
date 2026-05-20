-- NexusOS Initial Schema Migration
-- Run this in Supabase SQL Editor

-- Verification runs table
CREATE TABLE IF NOT EXISTS verification_runs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    target_url TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('PASS', 'FAIL', 'DEGRADED', 'ERROR')),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    duration_ms REAL NOT NULL,
    pages_checked INTEGER NOT NULL DEFAULT 0,
    apis_checked INTEGER NOT NULL DEFAULT 0,
    retries_total INTEGER NOT NULL DEFAULT 0,
    console_errors INTEGER NOT NULL DEFAULT 0,
    governance_decisions INTEGER NOT NULL DEFAULT 0,
    config JSONB,
    proof_manifest JSONB,
    pages JSONB,
    api_results JSONB,
    owner_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON verification_runs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_runs_target ON verification_runs(target_url);
CREATE INDEX IF NOT EXISTS idx_runs_verdict ON verification_runs(verdict);
CREATE INDEX IF NOT EXISTS idx_runs_owner ON verification_runs(owner_id);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'starter',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 10,
    monthly_quota INTEGER NOT NULL DEFAULT 100,
    usage_this_month INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keys_owner ON api_keys(owner_id);

-- Audit trail table
CREATE TABLE IF NOT EXISTS audit_records (
    id TEXT PRIMARY KEY,
    sequence INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    resource TEXT,
    outcome TEXT NOT NULL,
    metadata JSONB,
    checksum TEXT NOT NULL,
    previous_checksum TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_records(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_records(action);
CREATE INDEX IF NOT EXISTS idx_audit_sequence ON audit_records(sequence);

-- Evidence artifacts index
CREATE TABLE IF NOT EXISTS evidence_artifacts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES verification_runs(id),
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mime_type TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_run ON evidence_artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON evidence_artifacts(type);

-- Row Level Security (enable for multi-tenant)
ALTER TABLE verification_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own runs
CREATE POLICY "Users see own runs" ON verification_runs
    FOR SELECT USING (owner_id = current_setting('app.current_user_id', true));

-- Policy: users can only see their own keys
CREATE POLICY "Users see own keys" ON api_keys
    FOR SELECT USING (owner_id = current_setting('app.current_user_id', true));
