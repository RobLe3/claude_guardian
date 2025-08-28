# Claude Code Integration Guide

**Claude Guardian v2.0.0-alpha** - Complete integration guide for HTTP/WebSocket-based MCP connection with Claude Code.

**🚀 5-Minute Setup | No Docker Required | Works with Fresh Claude Code**

---

## 🔗 **Quick Integration (2 minutes)**

### **Step 1: Start Claude Guardian v2.0**

#### **Option A: Easy Setup (Recommended)**
```bash
# Clone and quick setup
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian
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
# Use the setup script (for full stack)
./setup-v2.sh

# Expected output:
# ✅ Claude Guardian v2.0.0-alpha started successfully
# 🚀 FastAPI Application: Running on configured port (default 8000)
# 🗺️ PostgreSQL: Database connection established
# 🗄️ Redis: Cache service connected
# 🎯 Qdrant: Vector database configured (minimal usage)
# ✅ MCP Server: WebSocket protocol ready for Claude Code

# Alternative: Manual startup
# python3 -m uvicorn src.claude_guardian.main:app --host 0.0.0.0 --port 8000
```

#### **Option C: Manual Dependencies Setup**
```bash
# Install minimal dependencies
pip3 install --user websockets fastapi uvicorn pydantic

# Start MCP service
python3 scripts/start-mcp-service.py --port 8083
```

### **Step 2: Configure Claude Code MCP Integration**

**Method 1: Use Generated Configuration (Easy Setup)**
After running easy-setup.sh, use the generated configuration:
```bash
# Copy the generated config
cp claude-code-config.json ~/.claude-code/mcp/
```

**Method 2: Manual Configuration (Custom Setup)**
Add to your Claude Code MCP configuration:

```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": [
    "-m", "uvicorn", "src.claude_guardian.main:app", 
    "--host", "0.0.0.0", "--port", "8083"
  ],
  "env": {
    "GUARDIAN_VERSION": "2.0.0-alpha",
    "PYTHONPATH": "/full/path/to/claude_guardian"
  }
}
```

**Replace `/full/path/to/claude_guardian/` with your actual path.**

### **Step 3: Verify v2.0 Connection**
In Claude Code, you should see:
- ✅ **5 security tools** available via HTTP MCP
- ✅ **claude-guardian v2.0.0-alpha** server connected
- ✅ **Real-time analysis** via MCP WebSocket protocol
- ✅ **Pattern-based detection** for common security threats

---

## 🛠️ **Detailed Configuration**

### **v2.0 HTTP MCP Configuration**

**Location:** Usually in Claude Code settings or `~/.claude-code/mcp-servers.json`

```json
{
  "servers": {
    "claude-guardian": {
      "command": "python3",
      "args": [
        "-m", "uvicorn", "src.claude_guardian.main:app",
        "--host", "0.0.0.0", "--port", "8000"
      ],
      "env": {
        "GUARDIAN_VERSION": "2.0.0-alpha",
        "PYTHONPATH": "/Users/yourusername/path/to/claude_guardian"
      }
    }
  }
}
```

### **Environment Variables**

```bash
# Optional environment configuration
export GUARDIAN_HOST="localhost"
export GUARDIAN_PORT="8083"
export GUARDIAN_LOG_LEVEL="INFO"
export GUARDIAN_CACHE_SIZE="10000"
```

---

## 🔧 **Available v2.0 Security Tools**

When connected via HTTP MCP, Claude Code will have access to these enhanced tools:

### **1. scan_code_security** (v2.0 Enhanced)
```json
{
  "name": "security_scan_code",
  "description": "Scans code for security vulnerabilities and dangerous patterns",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "description": "Code to analyze for security issues"
      },
      "language": {
        "type": "string", 
        "description": "Programming language (python, javascript, etc.)"
      }
    }
  }
}
```

### **2. analyze_code_patterns**
```json
{
  "name": "analyze_code_patterns",
  "description": "Analyzes code for attack patterns and security anti-patterns",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {"type": "string"},
      "context": {"type": "string", "description": "Code context (production, testing, etc.)"}
    }
  }
}
```

### **3. detect_vulnerabilities**
```json
{
  "name": "detect_vulnerabilities",
  "description": "Detects specific vulnerability types in code",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {"type": "string"},
      "vulnerability_types": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Types to check: injection, xss, path_traversal, etc."
      }
    }
  }
}
```

### **4. assess_code_risk**
```json
{
  "name": "assess_code_risk",
  "description": "Provides comprehensive risk assessment of code",
  "inputSchema": {
    "type": "object", 
    "properties": {
      "code": {"type": "string"},
      "environment": {"type": "string", "description": "deployment environment"}
    }
  }
}
```

### **5. generate_security_report**
```json
{
  "name": "generate_security_report",
  "description": "Generates detailed security analysis report",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {"type": "string"},
      "include_recommendations": {"type": "boolean", "default": true}
    }
  }
}
```

---

## 🧪 **Testing Integration**

### **v2.0 Connection Test**
```bash
# Start Claude Guardian v2.0 (if not already running)
./setup-v2.sh

# Test HTTP MCP connection
curl -s http://localhost:8083/health | jq
curl -s http://localhost:8083/api/v1/mcp/tools | jq

# Expected output:
# ✅ FastAPI Server: Healthy (claude-guardian v2.0.0-alpha)
# ✅ MCP Tools Available: 5/5 via HTTP protocol
# ✅ Response Time: <6ms average
# ✅ Database Status: All 3 databases healthy
```

### **Security Tool Test**
In Claude Code, try asking:
```
"Please scan this code for security issues:
user_input = input('Enter command: ')
result = eval(user_input)
print(result)
"
```

**Expected v2.0 Guardian Response (Enhanced):**
```
🚨 CRITICAL SECURITY ISSUE DETECTED (v2.0.0-alpha)

Threat Analysis Results:
- Threat Level: HIGH
- Confidence Score: 95%
- Response Time: 4.2ms
- Detection Pattern: Direct eval() with user input

Vulnerability Details:
- Pattern Type: Code Injection (eval_with_user_input)
- Risk Score: 9.8/10 (CRITICAL)
- Attack Vector: Malicious code execution via eval()
- Potential Impact: Complete system compromise

ML-Enhanced Recommendations:
1. ⚡ Immediate: Replace eval() with ast.literal_eval()
2. 🛡️ Validate: Implement input sanitization
3. 🔒 Secure: Use JSON parsing for data handling
4. 🎯 Best Practice: Implement allowlisting patterns

Secure Code Example:
import ast, json
try:
    # For Python literals
    result = ast.literal_eval(user_input)
except (ValueError, SyntaxError):
    # For JSON data
    try:
        result = json.loads(user_input)
    except json.JSONDecodeError:
        print("Invalid input format")
        
Detection powered by: LightRAG + 25 threat patterns + ML analysis
```

---

## 🛠️ **Alternative Configuration Methods**

### **Method 1: Direct Script Execution**
```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["/full/path/to/claude_guardian/scripts/start-mcp-service.py", "--port", "8083"],
  "env": {
    "GUARDIAN_MODE": "production",
    "SECURITY_LEVEL": "moderate"
  }
}
```

### **Method 2: Using Management Script**
```json
{
  "name": "claude-guardian", 
  "command": "/full/path/to/claude_guardian/scripts/guardian-mcp",
  "args": ["start", "8083"],
  "env": {
    "GUARDIAN_VERSION": "2.0.0-alpha"
  }
}
```

### **Method 3: WebSocket Connection**
```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["/full/path/to/claude_guardian/scripts/start-mcp-service.py", "--port", "8083", "--persistent"],
  "env": {
    "GUARDIAN_HOST": "localhost",
    "GUARDIAN_PORT": "8083"
  }
}
```

---

## ⚙️ **Configuration Options**

### **Security Levels**
- `strict`: Maximum security detection
- `moderate`: Balanced detection (default)
- `relaxed`: Minimal false positives

### **Environment Variables**
```bash
export GUARDIAN_MODE=production
export SECURITY_LEVEL=moderate
export MCP_PORT=8083
export GUARDIAN_DEBUG=false
```

### **Performance Tuning**
```bash
# For large codebases
export GUARDIAN_CACHE_SIZE=10000
export GUARDIAN_TIMEOUT=30

# For faster responses
export GUARDIAN_ASYNC_MODE=true
export GUARDIAN_PARALLEL_SCAN=true
```

---

## 🔄 **Service Management**

### **Start/Stop Service**
```bash
# Start
python3 scripts/start-mcp-service.py --port 8083

# Stop (find and kill process)
lsof -ti :8083 | xargs kill

# Status check
lsof -i :8083 && echo "Running" || echo "Stopped"

# Using management script
scripts/guardian-mcp start
scripts/guardian-mcp stop
scripts/guardian-mcp status
scripts/guardian-mcp restart
```

### **Automatic Startup**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias guardian-start="cd /path/to/claude_guardian && python3 scripts/start-mcp-service.py --port 8083 &"
```

---

## 🚨 **Troubleshooting**

### **MCP Service Won't Start**
```bash
# Check Python dependencies
pip3 install websockets fastapi uvicorn pydantic

# Check port conflicts
lsof -i :8083
# Kill conflicting process if needed

# Start with debugging
python3 scripts/start-mcp-service.py --port 8083 --debug
```

### **Claude Code Can't Connect**
```bash
# Verify service is running
curl http://localhost:8083/health
# Should return: {"status": "healthy"}

# Check configuration path
# Ensure full absolute paths in Claude Code config
```

### **Tools Not Available in Claude Code**
```bash
# Test MCP tools directly
python3 scripts/validate-mcp-tools.py

# Check Claude Code MCP settings
# Restart Claude Code after config changes
```

### **Claude Code can't find MCP server**

**Check path configuration:**
```bash
# Verify Guardian path
ls -la /full/path/to/claude_guardian/scripts/start-mcp-service.py

# Test manual execution
cd /full/path/to/claude_guardian
python3 scripts/start-mcp-service.py --port 8083
```

**Update MCP config with absolute paths:**
```json
{
  "command": "/usr/bin/python3",  // Full Python path
  "args": [
    "/Users/username/claude_guardian/scripts/start-mcp-service.py",
    "--port", "8083"
  ]
}
```

### **Connection refused errors**

**Check if port is available:**
```bash
# Check port usage
lsof -i :8083

# Try different port
python3 scripts/start-mcp-service.py --port 8084

# Update Claude Code config accordingly
```

### **Tools not appearing in Claude Code**

**Verify tool registration:**
```bash
# Test tool discovery
curl -X POST http://localhost:8083/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list", "params": {}}'

# Should return list of 5 security tools
```

**Restart both services:**
```bash
# Restart Guardian MCP service cleanly
scripts/guardian-mcp restart

# Check status
scripts/guardian-mcp status

# Restart Claude Code MCP connection if needed
# (Restart Claude Code application)
```

### **Performance issues**

**Check system resources:**
```bash
# Monitor resource usage
top -p $(pgrep -f "start-mcp-service.py")

# Check Guardian logs
tail -f mcp-service.log
```

**Optimize configuration:**
```bash
# Use performance mode
python3 scripts/start-mcp-service.py --port 8083 --cache-size 5000
```

---

## ⚡ **Advanced Configuration**

### **Custom Security Policies**
```bash
# Edit security tool registry
nano config/security-tools-registry.json

# Add custom threat patterns
nano config/custom-patterns.json

# Restart MCP service to load changes
```

### **Multi-Instance Setup**
```bash
# Run multiple Guardian instances
python3 scripts/start-mcp-service.py --port 8083 --instance primary
python3 scripts/start-mcp-service.py --port 8084 --instance secondary

# Configure Claude Code to use primary instance
```

### **Enterprise Integration**
```bash
# Start with production database
cd deployments/production
docker-compose -f docker-compose.production.yml up -d

# Connect MCP service to production backend
python3 scripts/start-mcp-service.py --port 8083 --production
```

---

## 🎯 **Usage in Claude Code**

### **Security Scanning**
```
User: "Scan this code for security issues"
Claude: [Uses Guardian to detect vulnerabilities, provides detailed analysis]
```

### **Pattern Analysis**
```
User: "Check if this function has any security anti-patterns"
Claude: [Uses Guardian to analyze code patterns and security risks]
```

### **Risk Assessment**
```
User: "What's the security risk level of this API endpoint?"
Claude: [Uses Guardian to assess and score security risks]
```

### **Report Generation**
```
User: "Generate a security report for this project"
Claude: [Uses Guardian to create comprehensive security assessment]
```

## 🎉 **Success Indicators**

When everything works correctly, you should see:

1. **MCP Service**: Running on port 8083
2. **Claude Code**: Shows "claude-guardian" in MCP servers list
3. **Tools Available**: 5 security tools accessible in Claude
4. **Validation**: `validate-mcp-tools.py` shows all green checkmarks
5. **Functionality**: Security scans work in Claude Code conversations

---

## 📊 **Usage Examples**

### **Real-time Code Analysis**
When you write code in Claude Code, Guardian automatically:
- **Scans every code block** for security vulnerabilities
- **Provides instant feedback** with risk scores
- **Suggests secure alternatives** for dangerous patterns
- **Maintains context awareness** to avoid false positives

### **Interactive Security Review**
```python
# Guardian analyzes this automatically:
import subprocess
user_cmd = input("Enter command: ")
subprocess.run(user_cmd, shell=True)  # Security issue detected

# Guardian provides:
# 🚨 Command injection vulnerability detected
# Risk: 8.5/10 - User input to system command
# Fix: Use subprocess.run(['cmd', 'arg1', 'arg2']) instead
```

### **False Positive Protection**
```python
# Guardian recognizes safe patterns:
config = {
    "warning": "Never use eval() with user input",
    "docs": "Use ast.literal_eval() for safety"
}

# Guardian responds:
# ✅ Safe configuration detected
# Context: Documentation/string literals
# No security concerns
```

---

## 🎯 **Best Practices**

### **For Daily Development**
1. **Keep Guardian running** during all coding sessions
2. **Review security feedback** before committing code  
3. **Use Guardian's suggestions** to improve code security
4. **Test with different risk levels** (strict/moderate/relaxed)

### **For Team Integration**
1. **Share MCP configuration** across team members
2. **Standardize security policies** via configuration files
3. **Document security exceptions** for special cases
4. **Regular security reviews** using Guardian reports

### **For Production**
1. **Use production database** for persistent threat learning
2. **Enable monitoring** for security event tracking
3. **Configure alerts** for critical security issues
4. **Regular updates** to threat patterns and policies

---

**🔗 Claude Code + 🛡️ Claude Guardian = Secure Development**

*Real-time security analysis integrated into your development workflow.*