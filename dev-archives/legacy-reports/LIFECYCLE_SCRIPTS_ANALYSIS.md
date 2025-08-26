# 🔄 Lifecycle Scripts Analysis: What Actually Gets Started

**Reality Check: What services do the management scripts actually spawn?**

## 📋 **Scripts Analyzed:**

1. **`scripts/guardian-mcp`** - "MCP Server Management"
2. **`scripts/guardian-backend`** - "Backend Services Management" 
3. **`deployments/production/deploy.sh`** - "Production Deployment"
4. **`easy-setup.sh`** - "Easy Setup"

---

## 🎯 **What Each Script Actually Spawns**

### **1. `scripts/guardian-mcp` (Line 8: `MCP_SCRIPT="$SCRIPT_DIR/start-mcp-service.py"`)**

**Claims:** "MCP Server Management Script"

**Actually Spawns:**
- ✅ **ONLY** Python MCP service (`start-mcp-service.py`)
- ✅ Single WebSocket server on port 8083
- ✅ Zero external dependencies

**Services NOT Started:**
- ❌ LightRAG
- ❌ PostgreSQL  
- ❌ Qdrant
- ❌ Any Docker containers

**Reality:** This is the **only** script that's honest about what it does.

---

### **2. `scripts/guardian-backend` (Line 20: `SERVICES=("qdrant" "postgres" "claude-guardian-mcp" "init-service" "prometheus")`)**

**Claims:** "Backend Services Management"

**Attempts to Spawn:**
- 🔄 Qdrant (vector database) - **image exists**
- 🔄 PostgreSQL - **image exists**  
- ❌ `claude-guardian-mcp` - **MISSING DOCKER IMAGE**
- 🔄 `init-service` - **requires custom build**
- 🔄 `prometheus` - **optional monitoring**

**Critical Issue (Line 299):**
```bash
docker compose -f docker-compose.production.yml up -d "${services[@]}"
```

**This FAILS because:**
- References `ghcr.io/yourorg/claude-guardian-mcp:latest` (doesn't exist)
- Expects Go-based MCP service (not built)
- Missing LightRAG entirely

**Default Services Started (Line 21):**
```bash
DEFAULT_SERVICES=("qdrant" "postgres")
```

**Reality:** Only starts databases, MCP service fails to start.

---

### **3. `deployments/production/deploy.sh` (Line 115: `docker compose -f "$COMPOSE_FILE" up -d`)**

**Claims:** "Production Deployment Script"

**Attempts to Spawn (via docker-compose.production.yml):**
- 🔄 Qdrant - **works**
- ❌ LightRAG - **MISSING IMAGE** `ghcr.io/yourorg/lightrag-api:latest`
- 🔄 PostgreSQL - **works**
- 🔄 init-service - **custom build required**
- ❌ claude-guardian-mcp - **MISSING IMAGE** `ghcr.io/yourorg/claude-guardian-mcp:latest`
- 🔄 prometheus - **optional**

**Test Commands (Lines 154-174):**
```bash
curl -f -s "http://127.0.0.1:8083/health"  # FAILS - MCP container doesn't exist
curl -f -s "http://localhost:6333/readyz"   # Works - Qdrant is real
```

**Reality:** Deployment fails because core images don't exist.

---

### **4. `easy-setup.sh` (Line 52: `python3 scripts/start-mcp-service.py`)**

**Claims:** "Easy Setup (No Dependencies Required)"

**Actually Spawns:**
- ✅ Python MCP service only
- ✅ Works completely standalone
- ✅ No Docker, no databases, no complexity

**Reality:** This is the **only** script that actually works end-to-end.

---

## 🚨 **Critical Gaps Between Claims and Reality**

### **What Scripts CLAIM to Start:**
```
┌─────────────────────────────────────────┐
│ Claude Guardian "Full Stack":           │
│ • LightRAG (AI retrieval)              │  
│ • Qdrant (vector database)             │
│ • PostgreSQL (audit logs)              │
│ • Go MCP Server (production)           │
│ • Prometheus (monitoring)              │
│ • Init Service (bootstrapping)         │
└─────────────────────────────────────────┘
```

### **What Actually Gets Started:**
```
┌─────────────────────────────────────────┐
│ Reality Check:                          │
│ ✅ Qdrant (works)                       │
│ ✅ PostgreSQL (works)                   │ 
│ ❌ LightRAG (missing image)             │
│ ❌ Go MCP Server (missing image)        │
│ ✅ Python MCP (standalone only)         │
│ 🔄 Init Service (build required)        │
│ 🔄 Prometheus (optional)                │
└─────────────────────────────────────────┘
```

---

## 📊 **Service Spawn Success Rate**

| Script | Claims | Actually Starts | Success Rate |
|--------|--------|----------------|-------------|
| `guardian-mcp` | 1 service | 1 service | **100%** ✅ |
| `guardian-backend` | 5 services | 2 services | **40%** ⚠️ |
| `deploy.sh` | 6 services | 2-3 services | **33%** ❌ |
| `easy-setup.sh` | 1 service | 1 service | **100%** ✅ |

---

## 🔍 **Detailed Service Analysis**

### **Services That Actually Work:**
1. **Qdrant** (qdrant/qdrant:latest) - ✅ Standard Docker image
2. **PostgreSQL** (postgres:17-alpine) - ✅ Standard Docker image
3. **Python MCP** (scripts/start-mcp-service.py) - ✅ No dependencies

### **Services That FAIL to Start:**
1. **LightRAG** (`ghcr.io/yourorg/lightrag-api:latest`) - ❌ Image doesn't exist
2. **Go MCP Server** (`ghcr.io/yourorg/claude-guardian-mcp:latest`) - ❌ Image doesn't exist
3. **Production Integration** - ❌ No connection between services

---

## 💡 **Key Insights**

### **1. Honest vs Dishonest Scripts:**
- **Honest:** `guardian-mcp`, `easy-setup.sh` - Do exactly what they claim
- **Dishonest:** `guardian-backend`, `deploy.sh` - Promise more than they deliver

### **2. Docker Image Reality:**
```bash
# What's promised in Docker Compose:
ghcr.io/yourorg/lightrag-api:latest        # ❌ 404 Not Found
ghcr.io/yourorg/claude-guardian-mcp:latest # ❌ 404 Not Found

# What actually exists:
qdrant/qdrant:latest                       # ✅ Works
postgres:17-alpine                         # ✅ Works  
```

### **3. Service Dependencies Mismatch:**
- **Backend scripts** try to start integrated services
- **Python MCP** runs completely standalone
- **No actual integration** between database and MCP services

### **4. LightRAG Status:**
- **Referenced everywhere** in Docker configs
- **Implementation exists** in dev-scripts/lightrag_integration.py
- **Never actually deployed** by any lifecycle script
- **Missing from production** entirely

---

## ✅ **Recommendations**

### **1. Fix guardian-backend Script:**
```bash
# Current broken approach:
SERVICES=("qdrant" "postgres" "claude-guardian-mcp" "init-service" "prometheus")

# Honest working approach:
SERVICES=("qdrant" "postgres")  # Only start what actually works
```

### **2. Update deploy.sh:**
- Remove references to non-existent images
- Focus on database-only deployment  
- Separate MCP service as standalone Python

### **3. Create Honest Documentation:**
```markdown
# What Guardian Actually Provides:
- Working: Python MCP service (5 basic security tools)
- Working: Database services (Qdrant + PostgreSQL)
- Missing: Integration between services
- Missing: LightRAG implementation
- Missing: Production Docker images
```

---

## 🎯 **Bottom Line**

**Most lifecycle scripts promise a sophisticated integrated security platform but actually deliver disconnected database services with no functional MCP integration.**

Only `guardian-mcp` and `easy-setup.sh` are honest about their capabilities and actually work as advertised.

The others create an illusion of a complete system while delivering broken deployments and missing core components.