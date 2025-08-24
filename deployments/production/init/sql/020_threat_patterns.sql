-- Insert enhanced threat detection policies and patterns
-- Based on Claude Guardian development security analysis

INSERT INTO policy (id, level, description, snippet, metadata) VALUES
-- Code injection patterns
('pol_code_001', 'block', 'Block dangerous eval() usage in any language', 
 'eval\s*\(.*\)', 
 '{"pattern_type": "regex", "languages": ["python", "javascript", "php"], "severity": 9}'),

('pol_code_002', 'block', 'Block exec() function calls', 
 'exec\s*\(.*\)', 
 '{"pattern_type": "regex", "languages": ["python"], "severity": 9}'),

('pol_code_003', 'warn', 'Warn on os.system() usage', 
 'os\.system\s*\(.*\)', 
 '{"pattern_type": "regex", "languages": ["python"], "severity": 7}'),

-- SQL injection patterns
('pol_sql_001', 'block', 'Block SQL injection attempts', 
 '''.*;\s*(DROP|DELETE|INSERT|UPDATE)', 
 '{"pattern_type": "regex", "attack_type": "sql_injection", "severity": 10}'),

('pol_sql_002', 'block', 'Block UNION-based SQL injection', 
 'UNION\s+SELECT.*', 
 '{"pattern_type": "regex", "attack_type": "sql_injection", "severity": 9}'),

-- File system access patterns
('pol_file_001', 'warn', 'Warn on sensitive file access', 
 '/etc/(passwd|shadow|hosts)', 
 '{"pattern_type": "regex", "attack_type": "file_access", "severity": 8}'),

('pol_file_002', 'block', 'Block path traversal attempts', 
 '\.\./.*', 
 '{"pattern_type": "regex", "attack_type": "path_traversal", "severity": 8}'),

-- Network and command patterns  
('pol_net_001', 'warn', 'Monitor outbound network connections', 
 'curl|wget|requests\.get', 
 '{"pattern_type": "regex", "attack_type": "data_exfiltration", "severity": 6}'),

('pol_cmd_001', 'block', 'Block dangerous shell commands', 
 'rm\s+-rf\s+/', 
 '{"pattern_type": "regex", "attack_type": "destructive_command", "severity": 10}'),

-- XSS patterns
('pol_xss_001', 'warn', 'Detect script injection attempts', 
 '<script.*?>.*?</script>', 
 '{"pattern_type": "regex", "attack_type": "xss", "severity": 7}'),

('pol_xss_002', 'warn', 'Detect javascript protocol usage', 
 'javascript\s*:', 
 '{"pattern_type": "regex", "attack_type": "xss", "severity": 6}'),

-- Privilege escalation patterns
('pol_priv_001', 'warn', 'Monitor sudo usage', 
 'sudo\s+.*', 
 '{"pattern_type": "regex", "attack_type": "privilege_escalation", "severity": 7}'),

('pol_priv_002', 'block', 'Block setuid attempts', 
 'setuid|seteuid', 
 '{"pattern_type": "regex", "attack_type": "privilege_escalation", "severity": 9}'),

-- Cryptocurrency/mining patterns
('pol_crypto_001', 'warn', 'Detect cryptocurrency mining', 
 'mining|miner|cryptonight', 
 '{"pattern_type": "regex", "attack_type": "cryptocurrency_mining", "severity": 5}'),

-- Process manipulation
('pol_proc_001', 'warn', 'Monitor process creation', 
 'subprocess\.Popen|os\.spawn', 
 '{"pattern_type": "regex", "attack_type": "process_manipulation", "severity": 6}')

ON CONFLICT (id) DO UPDATE SET
    level = EXCLUDED.level,
    description = EXCLUDED.description,
    snippet = EXCLUDED.snippet,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Insert threat indicators from common attack patterns
INSERT INTO threat_indicators (indicator_type, value, threat_level, source, confidence, metadata) VALUES
-- Malicious IP ranges (example)
('ip', '192.168.1.1', 'medium', 'claude_guardian_builtin', 0.75, '{"description": "Known scanning host"}'),

-- File hashes of known malicious code patterns
('hash', 'a1b2c3d4e5f6', 'high', 'claude_guardian_patterns', 0.90, '{"description": "Dangerous eval pattern hash"}'),

-- Domain patterns
('domain', 'evil-domain.com', 'critical', 'threat_intelligence', 0.95, '{"description": "Known C&C domain"}'),

-- Code patterns (stored as signatures)
('pattern', 'eval(base64_decode', 'critical', 'claude_guardian_analysis', 0.88, '{"description": "Obfuscated code execution"}'),
('pattern', 'document.write(<script', 'high', 'claude_guardian_analysis', 0.85, '{"description": "DOM-based XSS"}'),
('pattern', 'system("rm -rf /', 'critical', 'claude_guardian_analysis', 0.95, '{"description": "Destructive system command"}')

ON CONFLICT (value) DO UPDATE SET
    threat_level = EXCLUDED.threat_level,
    confidence = EXCLUDED.confidence,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Create audit entries for policy initialization
INSERT INTO audit_event (actor, kind, label, risk, details) VALUES
('claude_guardian_init', 'policy_update', 'Security policies initialized', 2.0, 
 '{"policy_count": 15, "threat_indicator_count": 6, "initialization": "complete"}'),

('claude_guardian_init', 'system_startup', 'Claude Guardian production deployment', 1.0,
 '{"version": "2.0", "deployment_mode": "production", "features": ["threat_detection", "vector_search", "audit_logging"]}');