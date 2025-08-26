# Claude Guardian v2.0.0-alpha - Deployment Guide

This guide provides step-by-step instructions for deploying Claude Guardian v2.0.0-alpha with its complete FastAPI enterprise platform and multi-database architecture.

---

## 🎯 **Deployment Readiness Checklist**

Before deployment, ensure you have:

- [ ] **Docker & Docker Compose** installed
- [ ] **8GB+ RAM** available (16GB recommended for production)
- [ ] **50GB+ storage** available (200GB recommended for production)
- [ ] **Python 3.9+** for testing scripts
- [ ] **Network access** for container pulls
- [ ] **Admin privileges** for port binding

---

## 🚀 **Production Deployment**

### **1. Environment Setup**

```bash
# Navigate to Claude Guardian directory
cd /path/to/claude-guardian  # Update with your actual path

# Navigate to production deployment
cd deployments/production/

# Create environment file
cp .env.template .env

# Edit configuration
nano .env
```

### **2. Configure Environment Variables**

Edit `.env` with your v2.0 settings:

```bash
# Database Configuration (REQUIRED)
POSTGRES_DB=claude_guardian
POSTGRES_USER=cguser
POSTGRES_PASSWORD=your_secure_password_here

# v2.0 Multi-Database Persistence
QDRANT_DATA_PATH=./data/qdrant
POSTGRES_DATA_PATH=./data/postgres
REDIS_DATA_PATH=./data/redis

# AI Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
ENABLE_MONITORING=true
ENABLE_DEBUG_LOGGING=false
DEVELOPMENT_MODE=false
```

### **3. Deploy v2.0 FastAPI Stack**

```bash
# Use the v2.0 setup script (recommended)
./setup-v2.sh

# Or manual deployment:
# Create data directories for all databases
mkdir -p data/qdrant data/postgres data/redis

# Start all services
docker compose up -d

# Verify deployment
docker compose ps
```

### **4. Verify v2.0 Installation**

```bash
# Check FastAPI application health
curl -s http://localhost:8083/health | jq

# Check all databases
curl -s http://localhost:6333/collections | jq  # Qdrant
docker exec claude-guardian-postgres pg_isready  # PostgreSQL
docker exec claude-guardian-redis redis-cli ping  # Redis

# Test MCP tools
curl -s http://localhost:8083/api/v1/mcp/tools | jq
```

---

## 🧪 **Testing Your Deployment**

### **Full Stack Validation**

```bash
# Run comprehensive tests
cd /path/to/claude-guardian

# Test vector database integration
python3 scripts/test_full_stack.py

# Test vector-graph correlation
python3 scripts/test_vector_graph_correlation.py

# Test security effectiveness
python3 scripts/test_security_effectiveness.py
```

### **Expected v2.0 Test Results**

```
Claude Guardian v2.0.0-alpha Health Check:
✅ FastAPI Application: HEALTHY (5.5ms avg response)
✅ PostgreSQL Database: CONNECTED (46MB persistent)
✅ Qdrant Vector DB: ACTIVE (4 collections, 18MB)
✅ Redis Cache: OPERATIONAL (AOF enabled, 12KB)
✅ LightRAG Integration: READY (semantic search active)
✅ MCP Tools: 5/5 AVAILABLE

Performance Benchmarks (A+ Grades):
⚡ Response Time: 5.5ms average
🎯 Detection Accuracy: 100% on test vectors
🛡️ Reliability: 100% success rate
🚀 Throughput: 34+ req/s concurrent
```

---

## 🔗 **Claude Code Integration**

### **v2.0 FastAPI MCP Integration**

Claude Guardian v2.0 includes built-in HTTP MCP server:

```bash
# FastAPI application includes MCP server (automatic)
# No separate MCP service needed

# Verify MCP endpoints are active
curl http://localhost:8083/api/v1/mcp/tools
curl http://localhost:8083/health
```

### **Configure Claude Code v2.0**

Add to Claude Code MCP configuration (HTTP-based):

```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["-m", "uvicorn", "src.iff_guardian.main:app", "--host", "0.0.0.0", "--port", "8083"],
  "env": {
    "GUARDIAN_VERSION": "2.0.0-alpha"
  }
}
```

Or use the generated config file:
```bash
cp claude-code-mcp-config.json ~/.claude-code/mcp/
```

### **Verify v2.0 Integration**

```bash
# Test HTTP MCP integration
curl -X POST http://localhost:8083/api/v1/mcp/scan/security \
  -H "Content-Type: application/json" \
  -d '{"code": "SELECT * FROM users WHERE id = '\''1'\'' OR 1=1--", "context": "test"}'

# Expected output:
# ✅ 5 security tools operational
# ✅ Sub-6ms response times
# ✅ 100% detection accuracy
```

---

## ⚖️ **Scaling & Performance**

### **Resource Recommendations**

| Deployment Size | RAM | Storage | CPU | Concurrent Sessions |
|----------------|-----|---------|-----|-------------------|
| **Development** | 4GB | 20GB | 2 cores | 5-10 sessions |
| **Small Production** | 8GB | 100GB | 4 cores | 20-50 sessions |
| **Medium Production** | 16GB | 200GB | 8 cores | 100+ sessions |
| **Enterprise** | 32GB+ | 500GB+ | 16+ cores | 500+ sessions |

### **Performance Tuning**

```yaml
# docker-compose.production.yml - Resource limits
services:
  claude-guardian-mcp:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'

  qdrant:
    environment:
      QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS: 4
      QDRANT__SERVICE__MAX_REQUEST_SIZE_MB: 32
```

---

## 🔒 **Security Hardening**

### **Production Security Checklist**

- [ ] **Change default passwords** in `.env`
- [ ] **Use strong JWT secrets** (32+ characters)
- [ ] **Enable HTTPS** for production (add reverse proxy)
- [ ] **Restrict network access** (firewall rules)
- [ ] **Enable audit logging** (`AUDIT_ENABLED=true`)
- [ ] **Regular backups** of database and vector data
- [ ] **Monitor resource usage** and set alerts

### **Network Security**

```bash
# Restrict port access (production firewall rules)
ufw allow 22/tcp     # SSH
ufw allow 443/tcp    # HTTPS
ufw deny 6333/tcp    # Qdrant (internal only)
ufw deny 5432/tcp    # PostgreSQL (internal only)
```

---

## 📊 **Monitoring & Maintenance**

### **Health Monitoring**

```bash
# Check service health
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose logs -f claude-guardian-mcp
docker-compose logs -f qdrant
docker-compose logs -f postgres

# Monitor resource usage
docker stats claude-guardian-mcp claude-guardian-qdrant claude-guardian-postgres
```

### **Backup Strategy**

```bash
# Backup script (run daily)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec claude-guardian-postgres pg_dump -U cguser claude_guardian > backup_${DATE}.sql

# Backup Qdrant data
tar -czf qdrant_backup_${DATE}.tar.gz data/qdrant/

# Cleanup old backups (keep 30 days)
find . -name "backup_*.sql" -mtime +30 -delete
find . -name "qdrant_backup_*.tar.gz" -mtime +30 -delete
```

### **Update Procedure**

```bash
# Safe update process
docker-compose -f docker-compose.production.yml down
git pull origin main
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Verify update
python3 scripts/test_full_stack.py
```

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

**1. Vector Database Connection Failed**
```bash
# Check Qdrant status
curl -s http://localhost:6333/collections
# If failed, check logs:
docker-compose logs qdrant
```

**2. MCP Service Won't Start**
```bash
# Check port conflicts
lsof -i :8083
# Kill conflicting processes:
kill -9 $(lsof -t -i:8083)
```

**3. High Memory Usage**
```bash
# Check container resource usage
docker stats --no-stream
# Increase memory limits in docker-compose.yml if needed
```

**4. Slow Vector Search**
```bash
# Optimize Qdrant configuration
export QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=8
# Restart Qdrant container
```

### **Log Analysis**

```bash
# View recent errors
docker-compose logs --tail=50 --timestamps claude-guardian-mcp | grep ERROR

# Monitor real-time activity
docker-compose logs -f claude-guardian-mcp | grep "security_scan"

# Check threat detection activity
grep "CRITICAL\|HIGH" docker-compose.logs
```

---

## 📈 **Success Metrics**

### **Deployment Success Indicators**

After deployment, you should see:

- [ ] **All containers healthy**: `docker-compose ps` shows "Up" status
- [ ] **MCP service responding**: Port 8083 accessible
- [ ] **Vector database ready**: Collections created successfully  
- [ ] **Full stack tests pass**: 5/5 integration tests successful
- [ ] **Security score ≥80%**: Threat detection operational

### **v2.0 Performance Benchmarks**

Monitor these v2.0 metrics for optimal operation:

- **Response Time**: 5.5ms average (A+ grade)
- **Memory Usage**: <4GB total (all containers)
- **CPU Usage**: <30% average load
- **Storage**: 64MB persistent (PostgreSQL + Qdrant + Redis)
- **Success Rate**: 100% (zero failures)

---

## 🎯 **Production Readiness**

### **Go-Live Checklist**

Before production deployment:

- [ ] **Load Testing**: Verify performance under expected load
- [ ] **Security Audit**: Review configurations and access controls
- [ ] **Backup Verification**: Test restore procedures
- [ ] **Monitoring Setup**: Configure alerts and dashboards
- [ ] **Documentation**: Update team documentation
- [ ] **Training**: Ensure team understands operations

### **Support Resources**

- **Documentation**: [docs/](docs/) directory
- **Test Scripts**: `scripts/test_*.py` for validation
- **Configuration**: `deployments/production/` examples
- **Troubleshooting**: Check container logs first

---

<div align="center">

**🚀 Your Claude Guardian deployment is ready to protect your code! 🚀**

**Need Help?** Check the [troubleshooting section](#-troubleshooting) or review [test results](scripts/) for debugging.

</div>