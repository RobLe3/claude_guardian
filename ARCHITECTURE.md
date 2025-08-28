# 🏗️ Claude Guardian Architecture & Project Structure

**Version:** v2.0.0-alpha (FastAPI Enterprise Platform)  
**Date:** August 28, 2025

## System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │───▶│  FastAPI App    │───▶│ PostgreSQL      │
│                 │    │  (MCP Server)   │    │ (Audit Logs)    │
└─────────────────┘    └─────────┬───────┘    └─────────────────┘
                                │
                         ┌──────▼──────┐      ┌─────────────────┐
                         │   Security  │      │     Redis       │
                         │   Scanner   │      │   (Caching)     │
                         │ (Regex-based)│      │                 │
                         └─────────────┘      └─────────────────┘
                                │
                         ┌──────▼──────┐
                         │   Qdrant    │
                         │  (Vector    │
                         │ Collections)│
                         └─────────────┘
```

## Actual Implementation

Claude Guardian is a **single FastAPI application** with integrated security scanning capabilities. It provides:

- **MCP Server**: WebSocket integration with Claude Code for security analysis
- **Pattern-based Security Scanner**: Regex-based threat detection (not ML/AI)
- **Audit Database**: PostgreSQL for logging scan results and security events
- **Basic Caching**: Redis for session management and temporary data
- **Vector Storage**: Qdrant configured but used minimally

## Technology Stack

### Core Application
- **Framework**: FastAPI with Python 3.12
- **Protocol**: WebSocket-based MCP (Model Context Protocol)
- **Security Scanner**: Regex pattern matching (not ML-based)
- **Architecture**: Monolithic application with integrated components

### Database Layer

| Container | Technology | Purpose | Usage Level |
|---|---|---|---|
| PostgreSQL | `postgres:17-alpine` | Audit logs, scan results | **Active** |
| Redis | `redis:7-alpine` | Session cache, temporary data | **Active** |
| Qdrant | `qdrant/qdrant:latest` | Vector collections | **Configured, minimal usage** |

### Application Structure

| Component | Location | Purpose |
|---|---|---|
| **FastAPI App** | `src/claude_guardian/main.py` | Main application server |
| **Security Scanner** | `src/claude_guardian/core/security.py` | Pattern-based threat detection |
| **Database Manager** | `src/claude_guardian/core/database.py` | PostgreSQL, Redis, Qdrant integration |
| **MCP Integration** | `src/claude_guardian/api/mcp.py` | Claude Code WebSocket API |

## Data Flow

```
Claude Code → MCP WebSocket → FastAPI Application
                                   ↓
                        ┌─────────────────┐
                        │ Security Scanner │
                        │ (Regex Patterns) │
                        └─────────┬───────┘
                                  ↓
            ┌─────────────────────────────────────┐
            │                                     │
            ▼                                     ▼
    ┌─────────────────┐                   ┌─────────────────┐
    │   PostgreSQL    │                   │      Redis      │
    │                 │                   │                 │
    │ • Audit Logs    │                   │ • Sessions      │
    │ • Scan Results  │                   │ • Cache Data    │
    │ • Security Events│                   │ • Temp Storage  │
    └─────────────────┘                   └─────────────────┘
                            
            Optional (configured but minimal usage):
                    ┌─────────────────┐
                    │     Qdrant      │
                    │                 │
                    │ • Collections   │
                    │ • Vector Storage│
                    └─────────────────┘
```

## Security Analysis Engine

The security scanner uses **regex pattern matching** to identify potential threats:

```python
# Security patterns for threat detection
self.threat_patterns = {
    "sql_injection": [
        r"(?i)union\s+select",
        r"(?i)or\s+1=1",
        r"(?i)drop\s+table"
    ],
    "xss": [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*="
    ],
    # Additional patterns...
}
```

### Current Qdrant Collections (Configured but Minimal Usage):
- `security_procedures` - Security best practices
- `vulnerability_db` - Vulnerability data
- `attack_signatures` - Attack patterns
- `threat_patterns` - Threat signatures

**Note**: Vector search and RAG functionality are configured but not actively used in the current implementation.

## 🔧 **Container Management**

### Using Docker Compose (Recommended):
```bash
# Start all databases
docker-compose up -d

# Start with application container
docker-compose --profile app up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Reset all data
docker-compose down -v
```

### Using Docker Commands:
```bash
# Check status
docker ps

# View specific logs
docker logs claude-guardian-qdrant

# Connect to containers
docker exec -it claude-guardian-postgres psql -U cguser -d claude_guardian
docker exec -it claude-guardian-redis redis-cli -a ${REDIS_PASSWORD}
```

## Deployment Options

### 1. **Development (Recommended)**
- Docker Compose for databases: `docker-compose up -d`
- Local Python FastAPI app: `python -m claude_guardian.main`
- Claude Code MCP integration via WebSocket

### 2. **Containerized (Optional)**
- Full stack: `docker-compose --profile app up -d`
- All services in containers including the FastAPI app

### 3. **Production Considerations**
- Single FastAPI application (not microservices)
- PostgreSQL for persistent data
- Redis for session management
- Simple horizontal scaling via multiple FastAPI instances

## Security Capabilities

### Current Features
- **Pattern-based Scanning**: Regex detection for SQL injection, XSS, command injection
- **Audit Logging**: Complete scan results and security events in PostgreSQL
- **MCP Integration**: Secure WebSocket communication with Claude Code
- **Basic Authentication**: JWT-based auth (if libraries available)

### Limitations
- **No Machine Learning**: Uses regex patterns, not AI/ML models
- **No Complex Enterprise Features**: Single application, not microservices
- **Basic Threat Detection**: Pattern matching with configurable severity levels

## Performance Expectations

- **Response Time**: Variable based on code size and pattern complexity
- **Accuracy**: Pattern-based detection with configurable confidence levels
- **Scalability**: Single FastAPI instance with database backend
- **Throughput**: Suitable for individual developer or small team usage

## Future Roadmap

Features that could be implemented:
- Enhanced ML-based threat detection using Qdrant vector search
- Advanced RAG capabilities with LightRAG integration
- Multi-tenant architecture with role-based access
- Real-time collaborative security analysis
- Integration with external security tools and APIs

---

## 📁 Project Structure

### **Current FastAPI Implementation**

```
claude_guardian/
├── README.md                           📄 Main project documentation
├── GETTING_STARTED.md                  🚀 Comprehensive setup guide  
├── CLAUDE_CODE_INTEGRATION.md          🔗 Claude Code integration guide
├── ARCHITECTURE.md                     🏗️ This file - system architecture
├── API.md                             📡 API documentation
├── CHANGELOG.md                       📝 Version history
│
├── 📁 src/                            💻 Source code
│   └── claude_guardian/               🛡️ Main application package
│       ├── main.py                    🚀 FastAPI application entry point
│       ├── core/                      🧠 Core functionality
│       │   ├── security.py            🔒 Pattern-based security scanner
│       │   └── database.py            💾 Database integration layer
│       └── api/                       📡 API endpoints
│           └── mcp.py                 🔧 MCP WebSocket integration
│
├── 📁 config/                         ⚙️ Configuration files
│   ├── security-tools-registry.json   🛡️ Security tools definitions
│   └── .env.template                  ⚙️ Environment configuration
│
├── 📁 scripts/                        🔧 Utility scripts
│   ├── start-mcp-service.py           🚀 MCP server startup
│   ├── validate-mcp-tools.py          ✅ MCP tool validation
│   ├── guardian-mcp                   🔧 Service management script
│   └── version.py                     📋 Version information
│
├── 📁 deployments/                    🚀 Deployment configurations
│   └── production/                    🏭 Production deployment
│       ├── README.md                  📖 Production setup guide
│       ├── docker-compose.production.yml 🐳 Production stack
│       ├── .env.template              ⚙️ Production environment
│       └── init/                      🔧 Database initialization
│
├── 📁 docs/                          📚 User documentation
│   └── README.md                      📖 Documentation index
│
├── 📁 tests/                         🧪 Test suites
│   └── mcp-integration/               🔧 MCP-specific tests
│
└── 📁 dev-archives/                  📋 Development artifacts
    ├── documentation/                 📝 Archived documentation
    ├── benchmarks/                    📊 Performance benchmarks
    └── duplicate-clone-analysis/      🔍 Repository analysis
```

### **Key Components**

| Component | Location | Purpose | Status |
|---|---|---|---|
| **FastAPI App** | `src/claude_guardian/main.py` | Main application server | ✅ Active |
| **Security Scanner** | `src/claude_guardian/core/security.py` | Pattern-based threat detection | ✅ Active |
| **Database Manager** | `src/claude_guardian/core/database.py` | PostgreSQL, Redis, Qdrant integration | ✅ Active |
| **MCP Integration** | `src/claude_guardian/api/mcp.py` | Claude Code WebSocket API | ✅ Active |
| **Service Management** | `scripts/guardian-mcp` | Start/stop/status management | ✅ Active |
| **Setup Automation** | `easy-setup.sh`, `setup-v2.sh` | Automated installation | ✅ Active |

### **Configuration Management**

```
Configuration Hierarchy:
├── .env.template                      🔧 Base environment configuration
├── config/security-tools-registry.json 🛡️ Security tool definitions
├── deployments/production/.env.template 🏭 Production overrides
└── Runtime Environment Variables       ⚙️ Runtime configuration
```

### **Database Schema (Actual Implementation)**

```sql
-- PostgreSQL Tables (Active)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    scan_id UUID,
    timestamp TIMESTAMP,
    code_content TEXT,
    threat_level VARCHAR(20),
    findings JSONB
);

CREATE TABLE scan_results (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    scan_timestamp TIMESTAMP,
    security_issues JSONB,
    risk_score DECIMAL
);

-- Redis Keys (Active)
sessions:*           # Session data and temporary storage
cache:*              # Analysis results caching
temp:*               # Temporary processing data

-- Qdrant Collections (Configured, minimal usage)
security_procedures  # Security best practices
vulnerability_db     # Vulnerability data  
attack_signatures    # Attack patterns
threat_patterns      # Threat signatures
```

---

**Current State**: Functional single-application security scanner with MCP integration
**Target Use Case**: Individual developers and small teams using Claude Code for security analysis