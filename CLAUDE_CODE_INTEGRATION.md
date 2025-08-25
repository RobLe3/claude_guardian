# Claude Code Integration Guide

**Claude Guardian v1.3.1** - Complete integration guide for Claude Code MCP connection.

---

## 🔗 **Quick Integration (2 minutes)**

### **Step 1: Start Claude Guardian**
```bash
# From Claude Guardian repository root
python3 scripts/start-mcp-service.py --port 8083

# Expected output:
# INFO - Claude Guardian MCP Server running on ws://localhost:8083
# INFO - Server info: claude-guardian v1.3.1
# INFO - 5 security tools loaded
```

### **Step 2: Configure Claude Code MCP**

**Add to your Claude Code MCP configuration:**

```json
{
  "name": "claude-guardian",
  "command": "python3",
  "args": [
    "/full/path/to/claude_guardian/scripts/start-mcp-service.py",
    "--port", "8083"
  ],
  "env": {
    "GUARDIAN_VERSION": "1.3.1"
  }
}
```

**Replace `/full/path/to/claude_guardian/` with your actual path.**

### **Step 3: Verify Connection**
In Claude Code, you should see:
- ✅ **5 security tools** available
- ✅ **claude-guardian v1.3.1** server connected
- ✅ **Real-time code analysis** active

---

## 🛠️ **Detailed Configuration**

### **MCP Server Configuration File**

**Location:** Usually in Claude Code settings or `~/.claude-code/mcp-servers.json`

```json
{
  "servers": {
    "claude-guardian": {
      "command": "python3",
      "args": [
        "/Users/yourusername/path/to/claude_guardian/scripts/start-mcp-service.py",
        "--port", "8083",
        "--verbose"
      ],
      "env": {
        "GUARDIAN_VERSION": "1.3.1",
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

## 🔧 **Available Security Tools**

When connected, Claude Code will have access to these tools:

### **1. security_scan_code**
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

### **Basic Connection Test**
```bash
# In terminal 1: Start Claude Guardian
python3 scripts/start-mcp-service.py --port 8083

# In terminal 2: Test connection
python3 scripts/validate-mcp-tools.py

# Expected output:
# ✅ MCP Server: Connected (claude-guardian v1.3.1)
# ✅ Tools Available: 5/5
# ✅ Connection Status: Operational
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

**Expected Guardian Response:**
```
🚨 CRITICAL SECURITY ISSUE DETECTED

Vulnerability: Direct eval() with user input
Risk Score: 9.5/10
Severity: CRITICAL

Issue Details:
- Line 2: eval(user_input) - Direct evaluation of user input
- Attack Vector: Code injection via malicious input
- Potential Impact: Remote code execution

Recommendations:
1. Replace eval() with ast.literal_eval() for safe evaluation
2. Validate and sanitize all user input
3. Use allowlisting for acceptable input patterns
4. Consider using json.loads() for data parsing

Example Fix:
import ast
try:
    result = ast.literal_eval(user_input)
except (ValueError, SyntaxError):
    print("Invalid input format")
```

---

## 🚨 **Troubleshooting**

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
# Kill existing MCP service
pkill -f "start-mcp-service.py"

# Restart Claude Code MCP connection
# (Restart Claude Code application)

# Start Guardian MCP service
python3 scripts/start-mcp-service.py --port 8083
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