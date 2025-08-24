# Claude Guardian - Deployment Guide

This guide provides step-by-step instructions for deploying Claude Guardian in various environments with verified configurations and realistic expectations.

---

## 🎯 **Deployment Readiness Checklist**

Before deployment, ensure you have:

- [ ] **Docker & Docker Compose** installed
- [ ] **4GB+ RAM** available (8GB recommended)
- [ ] **20GB+ storage** available (100GB recommended)
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

Edit `.env` with your settings:

```bash
# Database Configuration (REQUIRED)
POSTGRES_DB=claude_guardian
POSTGRES_USER=cguser
POSTGRES_PASSWORD=your_secure_password_here

# Security Configuration (REQUIRED)
JWT_SECRET=your_jwt_secret_key_minimum_32_characters_long
SECURITY_LEVEL=moderate  # Options: strict, moderate, relaxed

# Optional: Data persistence paths
QDRANT_DATA_PATH=./data/qdrant
POSTGRES_DATA_PATH=./data/postgres

# Optional: Feature flags
DEVELOPMENT_MODE=false
ENABLE_MONITORING=false
```

### **3. Deploy Full Stack**

```bash
# Create data directories
mkdir -p data/qdrant data/postgres

# Start all services
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
```

### **4. Verify Installation**

```bash
# Check Qdrant vector database
curl -s http://localhost:6333/collections | jq

# Check PostgreSQL connection
docker exec claude-guardian-postgres pg_isready

# Test MCP service (if using Python implementation)
python3 ../../scripts/validate-mcp-tools.py
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

### **Expected Test Results**

```
Full Stack Test Results:
✅ Vector Database: PASSED
✅ Vector Search: PASSED  
✅ MCP Integration: PASSED
✅ Threat Analysis Pipeline: PASSED
✅ Information Storage & Retrieval: PASSED
Overall Success Rate: 100%

Security Effectiveness Results:
🔒 Overall Security Score: 84%
📊 Threat Detection: 60-95% accuracy
🛡️ Mitigation Effectiveness: 97%
🔍 Circumvention Resistance: 100%
```

---

## 🔗 **Claude Code Integration**

### **MCP Service Setup**

For Claude Code integration, you need the MCP service running:

```bash
# Start Python MCP service
python3 scripts/start-mcp-service.py --port 8083 --verbose

# Or use the Go service (if available)
./services/mcp-service/mcp-service --port 8083
```

### **Configure Claude Code**

Add to Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "claude-guardian": {
      "command": "websocket",
      "args": ["ws://localhost:8083"]
    }
  }
}
```

### **Verify Integration**

```bash
# Test MCP tools discovery
python3 scripts/test_claude_code_integration.py

# Expected output:
# ✅ 5 security tools discovered
# ✅ Real-time threat analysis operational
# ✅ Cross-session learning enabled
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

### **Performance Benchmarks**

Monitor these metrics for optimal operation:

- **Response Time**: <100ms for security scans
- **Memory Usage**: <2GB per container
- **CPU Usage**: <50% average load
- **Storage Growth**: <1GB per week (typical)
- **Error Rate**: <1% of requests

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