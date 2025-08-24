-- Enhanced audit and security tables for Claude Guardian
-- Integrates with existing schema from 001_schema.sql

-- Threat detection results table
CREATE TABLE IF NOT EXISTS threat_detection (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID NOT NULL,
    tool_name TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    threat_level TEXT NOT NULL CHECK (threat_level IN ('safe', 'low', 'medium', 'high', 'critical')),
    risk_score NUMERIC(5,2) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 10),
    patterns_matched JSONB,
    analysis_duration_ms INTEGER,
    blocked BOOLEAN DEFAULT FALSE,
    INDEX (session_id),
    INDEX (tool_name),
    INDEX (threat_level),
    INDEX (created_at)
);

-- MCP tool execution logs
CREATE TABLE IF NOT EXISTS mcp_tool_execution (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID NOT NULL,
    tool_name TEXT NOT NULL,
    arguments JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    user_context JSONB,
    INDEX (session_id),
    INDEX (tool_name),
    INDEX (timestamp)
);

-- Security policy violations
CREATE TABLE IF NOT EXISTS policy_violation (
    id BIGSERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    policy_id TEXT NOT NULL,
    violation_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warn', 'error', 'critical')),
    context JSONB,
    resolved_at TIMESTAMPTZ,
    resolution_action TEXT,
    INDEX (policy_id),
    INDEX (violation_type),
    INDEX (severity),
    INDEX (detected_at)
);

-- Vector search performance metrics
CREATE TABLE IF NOT EXISTS vector_search_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    collection_name TEXT NOT NULL,
    query_type TEXT NOT NULL,
    search_time_ms INTEGER NOT NULL,
    results_count INTEGER NOT NULL,
    score_threshold NUMERIC(3,2),
    INDEX (collection_name),
    INDEX (timestamp),
    INDEX (query_type)
);

-- Enhanced policy table with vector embeddings
ALTER TABLE policy 
ADD COLUMN IF NOT EXISTS vector_id UUID,
ADD COLUMN IF NOT EXISTS embedding_model TEXT DEFAULT 'text-embedding-ada-002',
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Threat intelligence indicators
CREATE TABLE IF NOT EXISTS threat_indicators (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    indicator_type TEXT NOT NULL CHECK (indicator_type IN ('hash', 'ip', 'domain', 'pattern', 'signature')),
    value TEXT NOT NULL UNIQUE,
    threat_level TEXT NOT NULL CHECK (threat_level IN ('low', 'medium', 'high', 'critical')),
    source TEXT NOT NULL,
    confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
    metadata JSONB,
    expires_at TIMESTAMPTZ,
    INDEX (indicator_type),
    INDEX (threat_level),
    INDEX (source),
    INDEX (created_at)
);

-- User sessions for MCP connections
CREATE TABLE IF NOT EXISTS user_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT NOT NULL,
    client_info JSONB,
    permissions TEXT[] DEFAULT '{}',
    session_active BOOLEAN DEFAULT TRUE,
    INDEX (user_id),
    INDEX (last_activity),
    INDEX (session_active)
);

-- Create indexes for optimal query performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS audit_event_ts_idx ON audit_event (ts DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS audit_event_actor_kind_idx ON audit_event (actor, kind);
CREATE INDEX CONCURRENTLY IF NOT EXISTS audit_event_risk_idx ON audit_event (risk DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS threat_detection_session_time_idx ON threat_detection (session_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS policy_violation_policy_time_idx ON policy_violation (policy_id, detected_at DESC);

-- Create views for common queries
CREATE OR REPLACE VIEW high_risk_events AS
SELECT 
    ae.id,
    ae.ts,
    ae.actor,
    ae.kind,
    ae.label,
    ae.risk,
    td.threat_level,
    td.patterns_matched
FROM audit_event ae
LEFT JOIN threat_detection td ON ae.details->>'session_id' = td.session_id::text
WHERE ae.risk >= 7.0 OR td.threat_level IN ('high', 'critical')
ORDER BY ae.ts DESC;

CREATE OR REPLACE VIEW security_dashboard AS
SELECT 
    COUNT(*) FILTER (WHERE risk >= 8.0) as critical_events,
    COUNT(*) FILTER (WHERE risk >= 5.0 AND risk < 8.0) as high_events,
    COUNT(*) FILTER (WHERE risk >= 3.0 AND risk < 5.0) as medium_events,
    COUNT(*) FILTER (WHERE risk < 3.0) as low_events,
    AVG(risk) as avg_risk_score,
    COUNT(DISTINCT actor) as unique_actors
FROM audit_event 
WHERE ts >= NOW() - INTERVAL '24 hours';

-- Function to cleanup old audit data
CREATE OR REPLACE FUNCTION cleanup_old_audit_data(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_event 
    WHERE ts < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM threat_detection 
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    DELETE FROM mcp_tool_execution 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;