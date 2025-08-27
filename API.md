# Claude Guardian API Documentation

**Version**: 2.0.0-alpha  
**Last Updated**: August 26, 2025  
**Base URL**: `http://localhost:8000`

---

## Overview

Claude Guardian provides a FastAPI-based security analysis platform with MCP (Model Context Protocol) integration for Claude Code. The API offers pattern-based security scanning, audit logging, and system administration capabilities.

### **Important: Actual Implementation Notes**

This documentation reflects the **actual implemented capabilities**, not aspirational features. Claude Guardian currently provides:

- **Pattern-based security scanning** using regex patterns (not ML-based analysis)
- **Basic threat detection** across 5 categories with simple pattern matching
- **Database logging** for audit trails and scan results
- **MCP integration** via HTTP endpoints for Claude Code tools
- **System monitoring** and health checks

**What is NOT implemented:**
- Advanced ML/AI analysis
- Vector-graph correlation
- Enterprise SIEM integration
- LightRAG semantic search (referenced but not operational)
- Sub-6ms response times (actual times vary)
- Real-time threat intelligence feeds

---

## Authentication

Currently, the API does not require authentication for most endpoints. JWT token support is implemented in the SecurityManager but not enforced at the API level.

**Future Enhancement**: API key or JWT-based authentication will be added in future versions.

---

## Base Endpoints

### Root Information
```http
GET /
```

Returns basic system information and available endpoint paths.

**Response:**
```json
{
  "name": "Claude Guardian Security Platform",
  "version": "2.0.0-alpha",
  "status": "operational",
  "endpoints": {
    "mcp": "/api/v1/mcp",
    "security": "/api/v1/security",
    "admin": "/api/v1/admin",
    "health": "/health",
    "metrics": "/metrics"
  }
}
```

### Health Check
```http
GET /health
```

Comprehensive system health check including database and security manager status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-26T12:00:00Z",
  "services": {
    "database": "healthy",
    "security": "healthy", 
    "mcp": "operational"
  }
}
```

---

## MCP Protocol API (`/api/v1/mcp`)

The MCP API provides security tools for Claude Code integration via HTTP endpoints.

### List Available Tools
```http
GET /api/v1/mcp/tools
```

Returns list of available MCP security tools.

**Response:**
```json
[
  {
    "name": "scan_code_security",
    "description": "Analyze code for security vulnerabilities and threats",
    "parameters": {
      "code": {
        "type": "string",
        "description": "Source code to analyze"
      },
      "context": {
        "type": "string",
        "description": "Optional context about the code",
        "required": false
      }
    }
  },
  {
    "name": "check_dependencies",
    "description": "Scan dependencies for known vulnerabilities",
    "parameters": {
      "dependencies": {
        "type": "array",
        "description": "List of dependencies to check"
      }
    }
  },
  {
    "name": "analyze_network_config",
    "description": "Review network configuration for security issues",
    "parameters": {
      "config": {
        "type": "string",
        "description": "Network configuration to analyze"
      }
    }
  },
  {
    "name": "audit_permissions",
    "description": "Audit file and system permissions",
    "parameters": {
      "path": {
        "type": "string",
        "description": "Path to audit permissions for"
      }
    }
  },
  {
    "name": "detect_secrets",
    "description": "Scan for hardcoded secrets and credentials",
    "parameters": {
      "content": {
        "type": "string",
        "description": "Content to scan for secrets"
      }
    }
  }
]
```

### Security Code Analysis
```http
POST /api/v1/mcp/scan/security
```

Performs regex pattern-based security analysis on code.

**Request Body:**
```json
{
  "code": "SELECT * FROM users WHERE id = '1' OR 1=1--",
  "context": "database query",
  "scan_type": "comprehensive"
}
```

**Response:**
```json
{
  "threat_level": "high",
  "confidence": 0.85,
  "findings": [
    {
      "type": "sql_injection",
      "severity": "high",
      "pattern": "(?i)or\\s+1=1",
      "matches": ["OR 1=1"],
      "count": 1,
      "description": "Potential SQL injection vulnerability detected"
    }
  ],
  "recommendations": [
    "Use parameterized queries or prepared statements",
    "Implement input validation and sanitization"
  ],
  "processing_time_ms": 45,
  "scan_id": "a1b2c3d4"
}
```

**Threat Detection Patterns (23 total patterns across 5 categories):**

1. **SQL Injection** (`sql_injection`) - 5 patterns
   - `(?i)union\s+select`
   - `(?i)or\s+1=1`
   - `(?i)drop\s+table`
   - `(?i)exec\s*\(`
   - `(?i)script\s*>`

2. **Cross-Site Scripting** (`xss`) - 5 patterns
   - `<script[^>]*>`
   - `javascript:`
   - `on\w+\s*=`
   - `eval\s*\(`
   - `document\.cookie`

3. **Path Traversal** (`path_traversal`) - 4 patterns
   - `\.\.\/`
   - `\.\.\\`
   - `%2e%2e%2f`
   - `%252e%252e%252f`

4. **Command Injection** (`command_injection`) - 4 patterns
   - `;\s*(cat|ls|pwd|whoami)`
   - `\|\s*(curl|wget|nc)`
   - `` `.*` ``
   - `\$\(.*\)`

5. **Insecure Secrets** (`insecure_secrets`) - 4 patterns
   - `(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{1,50}['\"]`
   - `(?i)(api_key|apikey)\s*=\s*['\"][^'\"]{10,}['\"]`
   - `(?i)(secret|token)\s*=\s*['\"][^'\"]{10,}['\"]`
   - `-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----`

Additional security checks include detection of `eval()` function usage and weak randomization methods.

### Dependency Scanning
```http
POST /api/v1/mcp/scan/dependencies
```

**Note: This is currently a placeholder implementation**

**Request Body:**
```json
{
  "dependencies": ["express@4.17.1", "lodash@4.17.20"]
}
```

**Response:**
```json
{
  "dependencies": [
    {
      "name": "express@4.17.1",
      "version": "unknown",
      "vulnerabilities": [],
      "risk_level": "low",
      "recommendations": ["Keep dependencies updated"]
    }
  ],
  "summary": {
    "total": 2,
    "vulnerable": 0
  }
}
```

### Network Configuration Analysis
```http
POST /api/v1/mcp/analyze/network
```

**Note: Basic pattern matching implementation**

**Request Body:**
```json
{
  "config": "server_password=secret123\nport=8080"
}
```

**Response:**
```json
{
  "analysis_type": "network_configuration",
  "findings": [
    {
      "type": "credential_exposure",
      "severity": "high",
      "description": "Potential credential exposure in configuration"
    }
  ],
  "risk_score": 2.5,
  "recommendations": ["Review configuration for security best practices"]
}
```

### Permission Auditing
```http
POST /api/v1/mcp/audit/permissions
```

**Note: Placeholder implementation**

**Request Body:**
```json
{
  "path": "/home/user/app"
}
```

**Response:**
```json
{
  "path": "/home/user/app",
  "permissions": "755",
  "owner": "user",
  "group": "user",
  "issues": [],
  "recommendations": ["Follow principle of least privilege"]
}
```

### Secret Detection
```http
POST /api/v1/mcp/detect/secrets
```

Uses the same pattern matching as the main security analysis, filtered for secret-related findings.

**Request Body:**
```json
{
  "content": "const API_KEY = 'sk-1234567890abcdef';"
}
```

**Response:**
```json
{
  "secrets_found": 1,
  "findings": [
    {
      "type": "insecure_secrets",
      "severity": "high",
      "pattern": "(?i)(api_key|apikey)\\s*=\\s*['\"][^'\"]{10,}['\"]",
      "matches": ["API_KEY = 'sk-1234567890abcdef'"],
      "count": 1,
      "description": "Hardcoded secrets or credentials found"
    }
  ],
  "severity": "high",
  "recommendations": [
    "Remove hardcoded secrets",
    "Use environment variables or secret management systems",
    "Scan repositories for exposed credentials"
  ]
}
```

---

## Security API (`/api/v1/security`)

Direct access to security analysis and audit logging capabilities.

### Log Security Event
```http
POST /api/v1/security/events
```

**Request Body:**
```json
{
  "event_type": "unauthorized_access",
  "severity": "high",
  "description": "Failed login attempt from suspicious IP",
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "curl/7.68.0"
  }
}
```

**Response:**
```json
{
  "status": "logged",
  "timestamp": "2025-08-26T12:00:00.000Z"
}
```

### Get Security Events
```http
GET /api/v1/security/events?limit=50&severity=high&event_type=unauthorized_access
```

**Query Parameters:**
- `limit` (integer, 1-1000): Number of events to return (default: 50)
- `severity` (string, optional): Filter by severity level
- `event_type` (string, optional): Filter by event type

**Response:**
```json
{
  "events": [
    {
      "id": 1,
      "event_type": "unauthorized_access",
      "severity": "high",
      "description": "Failed login attempt",
      "metadata": {"ip_address": "192.168.1.100"},
      "timestamp": "2025-08-26T12:00:00.000Z"
    }
  ],
  "count": 1,
  "filters": {
    "severity": "high",
    "event_type": "unauthorized_access"
  }
}
```

### Get Scan Results
```http
GET /api/v1/security/scan-results?limit=20&threat_level=high&scan_type=code_security_analysis
```

**Query Parameters:**
- `limit` (integer, 1-100): Number of results to return (default: 20)
- `threat_level` (string, optional): Filter by threat level
- `scan_type` (string, optional): Filter by scan type

**Response:**
```json
{
  "scan_results": [
    {
      "id": 1,
      "scan_type": "code_security_analysis",
      "target_hash": "a1b2c3d4e5f6g7h8",
      "threat_level": "high",
      "findings": {
        "findings": [...],
        "recommendations": [...]
      },
      "processing_time_ms": 45,
      "timestamp": "2025-08-26T12:00:00.000Z"
    }
  ],
  "count": 1,
  "filters": {
    "threat_level": "high",
    "scan_type": "code_security_analysis"
  }
}
```

### Security Statistics
```http
GET /api/v1/security/statistics?days=7
```

**Query Parameters:**
- `days` (integer, 1-90): Number of days to include in statistics (default: 7)

**Response:**
```json
{
  "events_by_severity": {
    "low": 25,
    "medium": 10,
    "high": 5,
    "critical": 1
  },
  "scans_by_threat_level": {
    "low": 100,
    "medium": 20,
    "high": 8,
    "critical": 2
  },
  "total_events": 41,
  "total_scans": 130,
  "period_days": 7,
  "generated_at": "2025-08-26T12:00:00.000Z"
}
```

### Bulk Security Analysis
```http
POST /api/v1/security/analyze/bulk
```

**Note: Limited to 10 items per request**

**Request Body:**
```json
[
  {
    "code": "SELECT * FROM users",
    "context": "query1"
  },
  {
    "code": "eval(userInput)",
    "context": "query2"
  }
]
```

**Response:**
```json
{
  "results": [
    {
      "item_id": 0,
      "threat_level": "low",
      "confidence": 0.9,
      "findings_count": 0,
      "processing_time_ms": 12
    },
    {
      "item_id": 1,
      "threat_level": "high",
      "confidence": 0.8,
      "findings_count": 1,
      "processing_time_ms": 15
    }
  ],
  "summary": {
    "total_items": 2,
    "successful": 2,
    "failed": 0
  }
}
```

### Get Threat Patterns
```http
GET /api/v1/security/patterns?pattern_type=sql_injection
```

**Query Parameters:**
- `pattern_type` (string, optional): Specific pattern type to retrieve

**Response:**
```json
{
  "pattern_type": "sql_injection",
  "patterns": [
    "(?i)union\\s+select",
    "(?i)or\\s+1=1",
    "(?i)drop\\s+table",
    "(?i)exec\\s*\\(",
    "(?i)script\\s*>"
  ],
  "count": 5
}
```

---

## Administrative API (`/api/v1/admin`)

System management and monitoring endpoints.

### System Information
```http
GET /api/v1/admin/system/info
```

**Response:**
```json
{
  "version": "2.0.0-alpha",
  "uptime": "2:15:30",
  "memory_usage": {
    "total": 16777216000,
    "available": 8388608000,
    "used": 8388608000,
    "percentage": 50.0
  },
  "cpu_usage": 25.5,
  "disk_usage": {
    "total": 1000000000000,
    "used": 500000000000,
    "free": 500000000000,
    "percentage": 50.0
  },
  "active_connections": 12
}
```

### Comprehensive Health Check
```http
GET /api/v1/admin/system/health
```

**Response:**
```json
{
  "overall": "healthy",
  "timestamp": "2025-08-26T12:00:00.000Z",
  "components": {
    "database": {
      "status": "healthy",
      "details": "All database connections operational"
    },
    "security": {
      "status": "healthy", 
      "details": "Security manager operational"
    },
    "resources": {
      "status": "healthy",
      "details": "System resources normal"
    }
  }
}
```

### System Configuration
```http
GET /api/v1/admin/configuration
```

Returns sanitized system configuration (secrets redacted).

### Data Cleanup
```http
POST /api/v1/admin/maintenance/cleanup
```

**Request Body:**
```json
{
  "days_to_keep": 30
}
```

**Response:**
```json
{
  "status": "completed",
  "cutoff_date": "2025-07-27T12:00:00.000Z",
  "deleted": {
    "security_events": 150,
    "scan_results": 200
  },
  "total_deleted": 350
}
```

---

## Error Responses

All endpoints return standard HTTP error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Database not available"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. This will be added in future versions for production deployments.

---

## Data Models

### Threat Levels
- `low`: Minimal security concern
- `medium`: Moderate security risk
- `high`: Significant security risk
- `critical`: Severe security vulnerability

### Severity Levels  
- `info`: Informational events
- `low`: Low priority issues
- `medium`: Medium priority issues  
- `high`: High priority issues
- `critical`: Critical security events

---

## Performance Characteristics

Based on actual testing:

- **Average Response Time**: 15-50ms for security scans (varies by code size)
- **Pattern Matching**: Regex-based detection across 5 threat categories
- **Database Storage**: PostgreSQL for persistent audit logs and scan results
- **Concurrent Requests**: Supports multiple simultaneous API calls
- **Memory Usage**: ~100-500MB depending on database connections

**Note**: Claims of "sub-6ms response times" in other documentation are aspirational targets, not current performance metrics.

---

## Integration Examples

### Claude Code MCP Configuration
```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["-m", "uvicorn", "src.claude_guardian.main:app", "--host", "0.0.0.0", "--port", "8083"]
}
```

### Python Client Example
```python
import requests

# Security scan
response = requests.post('http://localhost:8083/api/v1/mcp/scan/security', json={
    'code': 'SELECT * FROM users WHERE id = ?',
    'context': 'user_lookup'
})

result = response.json()
print(f"Threat Level: {result['threat_level']}")
print(f"Findings: {len(result['findings'])}")
```

### cURL Examples
```bash
# Health check
curl http://localhost:8083/health

# Security scan
curl -X POST http://localhost:8083/api/v1/mcp/scan/security \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(userInput)", "context": "test"}'

# Get security events
curl "http://localhost:8083/api/v1/security/events?limit=10&severity=high"
```

---

## Limitations and Future Enhancements

### Current Limitations
1. **Pattern-based Detection Only**: No machine learning or semantic analysis
2. **Limited Language Support**: Optimized for Python, JavaScript, SQL patterns
3. **No Authentication**: API endpoints are currently open (security risk)
4. **Basic Error Handling**: Limited error context and recovery
5. **Placeholder Implementations**: Some endpoints like dependency scanning are not fully implemented

### Planned Enhancements
1. **Authentication & Authorization**: JWT-based API security
2. **Machine Learning Integration**: Advanced threat detection models
3. **Real-time Monitoring**: WebSocket-based live threat feeds
4. **SIEM Integration**: Connectors for popular security platforms
5. **Custom Rules Engine**: User-defined detection patterns
6. **Performance Optimization**: Caching and async processing improvements

---

## Support and Troubleshooting

### Common Issues
1. **Database Connection Errors**: Ensure PostgreSQL is running and accessible
2. **Port Already in Use**: Check if port 8083 is available (`lsof -i :8083`)
3. **Import Errors**: Verify all dependencies are installed (`pip install -r requirements.txt`)

### Logging
Application logs are written to `/tmp/claude-guardian-v2.log` and console output.

### Health Monitoring
Use the `/health` endpoint for basic health checks and `/api/v1/admin/system/health` for comprehensive system status.