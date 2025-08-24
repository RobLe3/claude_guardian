-- IFF-Guardian PostgreSQL Initialization Script
-- Creates database schema for authentication, RBAC, and audit logging

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS rbac;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS config;

-- Users table for authentication
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username CITEXT UNIQUE NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id)
);

-- Sessions table for JWT token management
CREATE TABLE auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,
    access_token_jti UUID NOT NULL UNIQUE,
    refresh_token_jti UUID NOT NULL UNIQUE,
    user_agent TEXT,
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Password reset tokens
CREATE TABLE auth.password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RBAC: Roles table
CREATE TABLE rbac.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id)
);

-- RBAC: Permissions table
CREATE TABLE rbac.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RBAC: Role-Permission assignments
CREATE TABLE rbac.role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES rbac.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES rbac.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    UNIQUE(role_id, permission_id)
);

-- RBAC: User-Role assignments
CREATE TABLE rbac.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES rbac.roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    granted_by UUID REFERENCES auth.users(id),
    UNIQUE(user_id, role_id)
);

-- Audit log table
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    session_id UUID REFERENCES auth.sessions(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Security events table
CREATE TABLE audit.security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    user_id UUID REFERENCES auth.users(id),
    session_id UUID REFERENCES auth.sessions(id),
    source_ip INET,
    details JSONB NOT NULL,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Configuration table
CREATE TABLE config.system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id)
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_active ON auth.users(is_active);
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON auth.sessions(refresh_token_jti);
CREATE INDEX idx_sessions_access_token ON auth.sessions(access_token_jti);
CREATE INDEX idx_sessions_expires ON auth.sessions(expires_at);
CREATE INDEX idx_user_roles_user_id ON rbac.user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON rbac.user_roles(role_id);
CREATE INDEX idx_role_permissions_role_id ON rbac.role_permissions(role_id);
CREATE INDEX idx_audit_logs_user_id ON audit.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit.audit_logs(created_at);
CREATE INDEX idx_security_events_user_id ON audit.security_events(user_id);
CREATE INDEX idx_security_events_severity ON audit.security_events(severity);
CREATE INDEX idx_security_events_created_at ON audit.security_events(created_at);

-- Insert default roles
INSERT INTO rbac.roles (name, description, is_system) VALUES
    ('admin', 'System Administrator with full access', true),
    ('security_analyst', 'Security analyst with threat detection access', true),
    ('user', 'Standard user with basic access', true),
    ('readonly', 'Read-only access to security data', true);

-- Insert default permissions
INSERT INTO rbac.permissions (name, resource, action, description) VALUES
    -- Auth permissions
    ('auth:read', 'authentication', 'read', 'Read authentication data'),
    ('auth:write', 'authentication', 'write', 'Manage authentication'),
    
    -- User permissions
    ('users:read', 'users', 'read', 'Read user data'),
    ('users:write', 'users', 'write', 'Manage users'),
    ('users:delete', 'users', 'delete', 'Delete users'),
    
    -- RBAC permissions
    ('rbac:read', 'rbac', 'read', 'Read RBAC data'),
    ('rbac:write', 'rbac', 'write', 'Manage roles and permissions'),
    
    -- Security permissions
    ('security:read', 'security', 'read', 'Read security data'),
    ('security:write', 'security', 'write', 'Manage security settings'),
    ('security:analyze', 'security', 'analyze', 'Analyze security threats'),
    
    -- Audit permissions
    ('audit:read', 'audit', 'read', 'Read audit logs'),
    ('audit:write', 'audit', 'write', 'Manage audit settings'),
    
    -- Config permissions
    ('config:read', 'config', 'read', 'Read system configuration'),
    ('config:write', 'config', 'write', 'Manage system configuration');

-- Assign permissions to roles
INSERT INTO rbac.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM rbac.roles r, rbac.permissions p 
WHERE r.name = 'admin'; -- Admin gets all permissions

INSERT INTO rbac.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM rbac.roles r, rbac.permissions p 
WHERE r.name = 'security_analyst' 
AND p.name IN ('auth:read', 'users:read', 'security:read', 'security:write', 'security:analyze', 'audit:read');

INSERT INTO rbac.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM rbac.roles r, rbac.permissions p 
WHERE r.name = 'user' 
AND p.name IN ('auth:read', 'security:read');

INSERT INTO rbac.role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM rbac.roles r, rbac.permissions p 
WHERE r.name = 'readonly' 
AND p.name LIKE '%:read';

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON rbac.roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON config.system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system configuration
INSERT INTO config.system_config (key, value, description) VALUES
    ('security.max_login_attempts', '5', 'Maximum failed login attempts before account lockout'),
    ('security.lockout_duration', '900', 'Account lockout duration in seconds'),
    ('security.password_min_length', '12', 'Minimum password length'),
    ('security.password_require_uppercase', 'true', 'Require uppercase letters in passwords'),
    ('security.password_require_lowercase', 'true', 'Require lowercase letters in passwords'),
    ('security.password_require_numbers', 'true', 'Require numbers in passwords'),
    ('security.password_require_special', 'true', 'Require special characters in passwords'),
    ('security.session_timeout', '3600', 'Session timeout in seconds'),
    ('security.refresh_token_timeout', '604800', 'Refresh token timeout in seconds'),
    ('mcp.enabled', 'true', 'Enable MCP protocol integration'),
    ('threat_detection.enabled', 'true', 'Enable threat detection engine'),
    ('threat_detection.threshold', '0.75', 'Threat detection threshold'),
    ('audit.retention_days', '365', 'Audit log retention period in days');

-- Create admin user (password: admin123!@# - CHANGE IN PRODUCTION)
INSERT INTO auth.users (username, email, password_hash, salt, first_name, last_name, is_active, is_verified) 
VALUES (
    'admin', 
    'admin@iff-guardian.local',
    crypt('admin123!@#', gen_salt('bf', 12)),
    gen_salt('bf', 12),
    'System',
    'Administrator',
    true,
    true
);

-- Assign admin role to admin user
INSERT INTO rbac.user_roles (user_id, role_id)
SELECT u.id, r.id 
FROM auth.users u, rbac.roles r 
WHERE u.username = 'admin' AND r.name = 'admin';

-- Grant necessary permissions to application
GRANT USAGE ON SCHEMA auth, rbac, audit, config TO iff_guardian;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth, rbac, audit, config TO iff_guardian;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth, rbac, audit, config TO iff_guardian;