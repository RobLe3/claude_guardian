# 🏗️ Claude Guardian Architecture

## Container Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLAUDE GUARDIAN v2.0.0                          │
├─────────────────────────────────────────────────────────────────────────┤
│  🐍 Python Application (FastAPI)                                       │
│  ├── MCP Server (Claude Code Integration)                              │
│  ├── Security Analysis Engine                                          │
│  ├── LightRAG Integration (Python Library)                             │
│  └── API Endpoints (REST + WebSocket)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                        DATABASE LAYER                                  │
├─────────────────┬─────────────────┬─────────────────────────────────────┤
│   PostgreSQL    │     Qdrant      │            Redis                    │
│  🗄️ Container   │  🎯 Container   │         ⚡ Container               │
│                 │                 │                                     │
│ • Audit Logs    │ • Threat Vectors│ • Session Cache                     │
│ • Scan Results  │ • Semantic Search│ • Real-time Data                   │
│ • Security Events│ • LightRAG Data │ • Rate Limiting                    │
│ • User Data     │ • ML Embeddings │ • Temp Storage                      │
└─────────────────┴─────────────────┴─────────────────────────────────────┘
```

## Service Breakdown

### 🐳 **Container Services**

| Container Name | Image | Ports | Purpose |
|---|---|---|---|
| `claude-guardian-postgres` | `postgres:17-alpine` | `5432:5432` | Persistent data storage |
| `claude-guardian-qdrant` | `qdrant/qdrant:latest` | `6333:6333`, `6334:6334` | Vector database |
| `claude-guardian-redis` | `redis:7-alpine` | `6379:6379` | Cache & session store |

### 🐍 **Python Application Components**

| Component | Location | Purpose |
|---|---|---|
| **FastAPI App** | `src/iff_guardian/main.py` | Main application server |
| **LightRAG** | Python Library (not containerized) | RAG functionality using Qdrant |
| **Security Engine** | `src/iff_guardian/core/security.py` | Threat detection & analysis |
| **Database Manager** | `src/iff_guardian/core/database.py` | Multi-database integration |
| **MCP Server** | `src/iff_guardian/api/mcp.py` | Claude Code integration |

## 🔄 **Data Flow Architecture**

```
Claude Code → MCP Protocol → FastAPI → Security Engine
                                  ↓
                          ┌─────────────────┐
                          │   LightRAG      │
                          │  (Python Lib)  │
                          └─────────────────┘
                                  ↓
    ┌─────────────────┬─────────────────┬─────────────────┐
    │   PostgreSQL    │     Qdrant      │      Redis      │
    │                 │                 │                 │
    │ Store Results → │ ← Vector Search │ ← Cache Data    │
    │ Log Events      │   Embeddings    │   Sessions      │
    │ Audit Trail     │   Similarity    │   Rate Limits   │
    └─────────────────┴─────────────────┴─────────────────┘
```

## 🎯 **LightRAG Integration Details**

**LightRAG is NOT containerized** - it's a Python library that runs within the Claude Guardian application:

```python
# LightRAG connects to Qdrant for vector operations
lightrag_service = LightRAG(
    qdrant_client=qdrant_client,  # Points to claude-guardian-qdrant:6333
    collections=['security_procedures', 'vulnerability_db', 'threat_patterns']
)
```

### Current Qdrant Collections:
- `security_procedures` - Security best practices and procedures
- `vulnerability_db` - Known vulnerabilities and CVE data  
- `attack_signatures` - Attack pattern signatures
- `threat_patterns` - ML threat pattern embeddings

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
docker exec -it claude-guardian-redis redis-cli -a redis_password_123
```

## 🚀 **Production Deployment**

The architecture supports multiple deployment scenarios:

1. **Development**: Containers + Local Python app
2. **Docker**: Full containerized stack with docker-compose
3. **Kubernetes**: Helm charts with persistent volumes
4. **Hybrid**: Cloud databases + Local application

## 🛡️ **Security Features**

- **Network Isolation**: All containers in `claude-guardian-network`
- **Persistent Storage**: Named volumes for data persistence  
- **Health Checks**: Automated container health monitoring
- **Authentication**: Database passwords and Redis authentication
- **Port Management**: Standardized port mapping across services

This architecture provides enterprise-grade scalability while maintaining simplicity for development and deployment.