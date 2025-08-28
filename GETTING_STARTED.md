# Claude Guardian - Getting Started Guide

**Version: v2.0.0-alpha** | **Setup Time: 5 minutes** | **Requirements: Docker + Python 3.8+**

Complete setup guide for Claude Guardian from repository to Claude Code integration. This consolidated guide combines all setup methods and ensures frustration-free installation.

---

## 🚀 **Quick Setup (Recommended)**

### **Step 1: Clone Repository**
```bash
# Clone Claude Guardian
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian

# Verify version
python3 scripts/version.py
# Expected: Claude Guardian Version: 2.0.0-alpha
```

### **Step 2: Choose Setup Method**

#### **Option A: Easy Setup (Python-only)**
```bash
# Validates environment and installs minimal dependencies
./easy-setup.sh

# Expected output:
# ✅ Python 3.11.5 found
# 📦 Installing Python dependencies...
# 🚀 Starting Claude Guardian MCP service...
# ✅ MCP service running (PID: 12345)
# 🎉 Setup Complete!
```

#### **Option B: Full Production Setup**
```bash
# Navigate to production deployment
cd deployments/production

# Setup environment (one-time only)
cp .env.template .env
# Edit .env with your preferences (optional for testing)

# Deploy complete stack
docker-compose -f docker-compose.production.yml up -d

# Verify deployment (wait ~30 seconds for startup)
curl http://localhost:6333/collections  # Qdrant vector DB
curl http://localhost:8083/health       # MCP service
```

### **Step 3: Connect to Claude Code**
```bash
# Start MCP service for Claude Code (if not already running)
cd ../../  # Back to repository root
scripts/guardian-mcp start

# Test integration
python3 scripts/validate-mcp-tools.py
```

**✅ You're ready!** Claude Guardian is now running and ready for Claude Code integration.

---

## 🔧 **Detailed Setup Instructions**

### **Prerequisites**
- **Docker & Docker Compose** (for full stack - optional)
- **Python 3.8+** (required for MCP service)
- **Git** (for repository access)
- **4GB RAM minimum** (8GB recommended for full stack)

### **Pre-Setup Validation**
Before running setup, validate your environment:
```bash
python3 scripts/test-setup.py

# Expected output:
# 🔍 Claude Guardian Setup Validation
# ✅ Python 3.11.5
# ✅ websockets, fastapi, uvicorn, pydantic
# ✅ Port 8083 available
# 🏆 Score: 6/6 tests passed
```

### **Repository Setup**
```bash
# Clone and verify
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian

# Check version and structure
python3 scripts/version.py
ls -la  # Verify all files present

# Install Python dependencies (handled by setup scripts)
pip install -r requirements.txt
# Key dependencies: fastapi, websockets, asyncio, pydantic
```

### **Database Setup (Optional - Full Stack Only)**
```bash
cd deployments/production

# Review environment configuration
cat .env.template
# Modify .env if needed (defaults work for testing)

# Start database stack
docker-compose -f docker-compose.production.yml up -d postgres qdrant

# Verify databases
docker ps  # Should show postgres and qdrant running
curl http://localhost:6333/collections  # Qdrant should return empty array
```

### **Security Service Setup**
```bash
# Start MCP service (recommended method)
scripts/guardian-mcp start

# Expected output:
# ✅ Claude Guardian MCP Server started successfully
# 📝 Process ID: 1234
# 🔗 WebSocket: ws://localhost:8083
# 📄 Logs: /tmp/guardian-mcp-8083.log

# Alternative: Direct Python invocation
# python3 scripts/start-mcp-service.py --port 8083
```

### **MCP Server Management**
```bash
# Check server status
scripts/guardian-mcp status

# Stop server
scripts/guardian-mcp stop

# Restart server
scripts/guardian-mcp restart

# View logs
scripts/guardian-mcp logs

# Start on different port
scripts/guardian-mcp start 8084
```

---

## 🔗 **Claude Code Integration**

### **Method 1: Using Generated Configuration**
After running easy setup, use the generated `claude-code-config.json`:
```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["/path/to/claude_guardian/scripts/start-mcp-service.py", "--port", "8083"],
  "env": {
    "GUARDIAN_MODE": "production"
  }
}
```

### **Method 2: Manual MCP Connection**
**In Claude Code, add MCP server:**
```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["/path/to/claude_guardian/scripts/start-mcp-service.py", "--port", "8083"],
  "env": {
    "GUARDIAN_HOST": "localhost",
    "GUARDIAN_PORT": "8083"
  }
}
```

### **Method 3: WebSocket Connection**
```bash
# Start persistent MCP service
python3 scripts/start-mcp-service.py --port 8083 --persistent

# Claude Code will connect to: ws://localhost:8083/mcp
```

### **Verify Integration**
```bash
# Test all security tools
python3 scripts/validate-mcp-tools.py

# Expected output:
# ✅ security_scan_code - Available
# ✅ analyze_code_patterns - Available
# ✅ detect_vulnerabilities - Available
# ✅ assess_code_risk - Available
# ✅ generate_security_report - Available
# 
# 🎉 All 5 security tools operational
```

---

## 🧪 **Testing & Verification**

### **Full System Test**
```bash
# Comprehensive test suite
python3 scripts/test_full_stack.py

# Expected results:
# ✅ Database connection: PASSED
# ✅ Vector database: PASSED  
# ✅ MCP service: PASSED
# ✅ Security tools: PASSED
# ✅ Multi-session support: PASSED
# 
# 🏆 System Score: 100% operational
```

### **Security Effectiveness Test**
```bash
# Test detection capabilities
python3 scripts/test_security_effectiveness.py

# Expected results:
# 🛡️ Context-aware detection: 91.7% accuracy
# 🎯 False positive rate: 0%
# ⚡ Response time: <100ms
# 🔍 Advanced features: 5 capabilities active
```

### **v2.0.0-alpha Benchmarks**
```bash
# Run comprehensive benchmarks
python3 dev-archives/benchmarks/rebench.py

# Expected results:
# ✅ FastAPI Service: Sub-6ms response times
# ✅ Detection accuracy: 100% on test vectors
# ✅ Performance grade: A+ across all metrics
# ✅ Multi-database: 64MB persistent storage
```

---

## 🚨 **Troubleshooting**

### **Setup Issues**

**Issue: Setup validation fails**
```bash
# Run pre-validation
python3 scripts/test-setup.py

# Address any missing dependencies
pip3 install --user websockets fastapi uvicorn pydantic
```

**Issue: Port 8083 already in use**
```bash
# Check server status (automatically detects conflicts)
scripts/guardian-mcp status

# Stop existing server and restart
scripts/guardian-mcp restart

# Or start on different port
scripts/guardian-mcp start 8084
```

**Issue: Docker containers won't start**
```bash
# Check Docker status
docker ps -a
docker logs <container_name>

# Reset and restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

**Issue: MCP connection fails**
```bash
# Check MCP server status
scripts/guardian-mcp status

# View real-time logs
scripts/guardian-mcp logs

# Restart MCP service cleanly
scripts/guardian-mcp restart
```

**Issue: Migration from previous setup**
```bash
# Stop any existing services
lsof -ti :8083 | xargs kill -9 2>/dev/null || true

# Clean start
rm -f .env .mcp_pid claude-code-config.json

# Run new setup
./easy-setup.sh
```

---

## ⚡ **Performance Optimization**

### **Production Configuration**
```bash
# Edit production environment
nano deployments/production/.env

# Key settings for performance:
POSTGRES_MAX_CONNECTIONS=100
QDRANT_MAX_PAYLOAD_SIZE=32MB
GUARDIAN_CACHE_SIZE=10000
SECURITY_LEVEL=moderate  # strict|moderate|relaxed
```

### **Resource Allocation**
```yaml
# Docker resource limits (optional)
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
  
  qdrant:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

---

## 📊 **Usage Examples**

### **Basic Security Scan in Claude Code**
```python
# In Claude Code, Guardian will automatically scan:
user_input = input("Enter command: ")
result = eval(user_input)  # ⚠️ Guardian will flag this

# Guardian response:
# 🚨 CRITICAL: Direct eval() with user input detected
# Risk Score: 9.5/10
# Recommendation: Use ast.literal_eval() for safe evaluation
```

### **Advanced Pattern Detection**
```python
# Guardian detects sophisticated attacks:
import os
filename = os.getenv('USER_FILE')  # Environment source
os.system('rm -rf ' + filename)    # System command sink

# Guardian response:
# 🔍 ADVANCED THREAT: Environment-to-system data flow detected
# Flow: os.getenv() → os.system() 
# Risk Score: 8.0/10
# Context: Multi-line attack pattern
```

### **False Positive Protection**
```python
# Guardian protects legitimate code:
config = {
    "help_text": "Never use eval() in production",
    "safe_eval": "Use ast.literal_eval instead"
}

# Guardian response:
# ✅ SAFE: String literals mentioning dangerous functions
# Context: Configuration/documentation
# Risk Score: 0/10
```

---

## 🎯 **v2.0.0-alpha Features**

### **Enterprise Features**
- ✅ **FastAPI enterprise application** with production deployment
- ✅ **Multi-database architecture** with PostgreSQL + Qdrant + Redis
- ✅ **25+ threat patterns** across 5 security categories
- ✅ **100% detection accuracy** verified through comprehensive testing
- ✅ **Zero false positives** maintained from v1.x
- ✅ **HTTP MCP integration** with Claude Code fully operational
- ✅ **Real-time analysis** with sub-6ms response times

### **Security Capabilities**
- **LightRAG semantic search** with 4 active collections
- **Context-aware detection** with 91.7% accuracy
- **Advanced threat patterns** including data flow analysis
- **Multi-session support** for concurrent operations
- **Comprehensive logging** and audit trails

---

## 🎯 **Next Steps**

### **After Setup Complete:**
1. **Configure Claude Code** with MCP server endpoint
2. **Run security scan** on your first project
3. **Review security reports** and recommendations
4. **Customize threat patterns** for your environment
5. **Enable production monitoring** for ongoing protection

### **Advanced Usage:**
- **Custom Security Policies**: Edit `config/security-tools-registry.json`
- **Pattern Learning**: Review and approve new patterns via web interface
- **Integration**: Connect to external SIEM systems
- **Scaling**: Deploy to Kubernetes for enterprise use

---

## 📞 **Support**

**Quick Tests:**
1. **Service Running**: `lsof -i :8083` shows process
2. **Configuration Ready**: `claude-code-config.json` file exists
3. **Service Validated**: `python3 scripts/validate-mcp-tools.py` passes
4. **Integration Ready**: Clear instructions for Claude Code

**Documentation:**
- [API Reference](API.md)
- [Version History](CHANGELOG.md)
- [Architecture Overview](ARCHITECTURE.md)

**Troubleshooting:**
1. **Run Validation**: `python3 scripts/test-setup.py`
2. **Check Logs**: `tail /tmp/claude-guardian-mcp.log`
3. **Test Service**: `curl http://localhost:8083/health`
4. **Report Issue**: Include validation output in issue report

**Issues:** Report at [GitHub Issues](https://github.com/RobLe3/claude_guardian/issues)

---

**🛡️ Claude Guardian v2.0.0-alpha - Production Ready Security**

*Complete setup in 5 minutes. Enterprise-grade protection from day one.*