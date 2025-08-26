# Claude Guardian → Claude Code Integration Guide

**🚀 5-Minute Setup | No Docker Required | Works with Fresh Claude Code**

---

## ⚡ Quick Start (Recommended)

### Step 1: Get Claude Guardian
```bash
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian
```

### Step 2: Run Easy Setup
```bash
./easy-setup.sh
```

### Step 3: Add to Claude Code
Copy the generated configuration and add it to Claude Code's MCP settings.

**✅ Done!** Test with: _"scan this code for security issues"_

---

## 🔧 Manual Setup (Alternative)

### Prerequisites
- Python 3.8+ (`python3 --version`)
- Claude Code installed

### Setup Steps

1. **Install Dependencies**
   ```bash
   pip3 install --user websockets fastapi uvicorn pydantic
   ```

2. **Start MCP Service**
   ```bash
   python3 scripts/start-mcp-service.py --port 8083
   ```

3. **Configure Claude Code**
   Add this MCP server configuration:
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

4. **Test Integration**
   ```bash
   python3 scripts/validate-mcp-tools.py
   ```

---

## 🛡️ Claude Code MCP Configuration Examples

### Method 1: Direct Script Execution
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

### Method 2: Using Management Script
```json
{
  "name": "claude-guardian", 
  "command": "/full/path/to/claude_guardian/scripts/guardian-mcp",
  "args": ["start", "8083"],
  "env": {
    "GUARDIAN_VERSION": "1.3.2"
  }
}
```

### Method 3: WebSocket Connection
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

## 🧪 Testing & Verification

### Basic Functionality Test
```bash
# Check MCP service is running
lsof -i :8083

# Validate all security tools
python3 scripts/validate-mcp-tools.py

# Expected: ✅ All 5 security tools operational
```

### Claude Code Integration Test
In Claude Code, try these commands:
- _"scan this code for security issues"_
- _"analyze this file for vulnerabilities"_ 
- _"check for security patterns in my code"_
- _"generate a security report"_
- _"assess risk level of this function"_

Expected: Claude Guardian should respond with detailed security analysis.

---

## 🚨 Troubleshooting

### Issue: MCP Service Won't Start
```bash
# Check Python dependencies
pip3 install websockets fastapi uvicorn

# Check port conflicts
lsof -i :8083
# Kill conflicting process if needed

# Start with debugging
python3 scripts/start-mcp-service.py --port 8083 --debug
```

### Issue: Claude Code Can't Connect
```bash
# Verify service is running
curl http://localhost:8083/health
# Should return: {"status": "healthy"}

# Check configuration path
# Ensure full absolute paths in Claude Code config
```

### Issue: Tools Not Available in Claude Code
```bash
# Test MCP tools directly
python3 scripts/validate-mcp-tools.py

# Check Claude Code MCP settings
# Restart Claude Code after config changes
```

---

## 🎯 Usage in Claude Code

### Security Scanning
```
User: "Scan this code for security issues"
Claude: [Uses Guardian to detect vulnerabilities, provides detailed analysis]
```

### Pattern Analysis
```
User: "Check if this function has any security anti-patterns"
Claude: [Uses Guardian to analyze code patterns and security risks]
```

### Risk Assessment
```
User: "What's the security risk level of this API endpoint?"
Claude: [Uses Guardian to assess and score security risks]
```

### Report Generation
```
User: "Generate a security report for this project"
Claude: [Uses Guardian to create comprehensive security assessment]
```

---

## ⚙️ Configuration Options

### Security Levels
- `strict`: Maximum security detection
- `moderate`: Balanced detection (default)
- `relaxed`: Minimal false positives

### Environment Variables
```bash
export GUARDIAN_MODE=production
export SECURITY_LEVEL=moderate
export MCP_PORT=8083
export GUARDIAN_DEBUG=false
```

### Performance Tuning
```bash
# For large codebases
export GUARDIAN_CACHE_SIZE=10000
export GUARDIAN_TIMEOUT=30

# For faster responses
export GUARDIAN_ASYNC_MODE=true
export GUARDIAN_PARALLEL_SCAN=true
```

---

## 🔄 Service Management

### Start/Stop Service
```bash
# Start
python3 scripts/start-mcp-service.py --port 8083

# Stop (find and kill process)
lsof -ti :8083 | xargs kill

# Status check
lsof -i :8083 && echo "Running" || echo "Stopped"
```

### Automatic Startup
```bash
# Add to ~/.bashrc or ~/.zshrc
alias guardian-start="cd /path/to/claude_guardian && python3 scripts/start-mcp-service.py --port 8083 &"
```

---

## 🎉 Success Indicators

When everything works correctly, you should see:

1. **MCP Service**: Running on port 8083
2. **Claude Code**: Shows "claude-guardian" in MCP servers list
3. **Tools Available**: 5 security tools accessible in Claude
4. **Validation**: `validate-mcp-tools.py` shows all green checkmarks
5. **Functionality**: Security scans work in Claude Code conversations

---

## 📞 Support

**Quick Help:**
- Service logs: `/tmp/claude-guardian-mcp.log`
- Test command: `python3 scripts/validate-mcp-tools.py`
- Health check: `curl http://localhost:8083/health`

**Documentation:**
- [Full Setup Guide](QUICKSTART.md)
- [Troubleshooting](docs/troubleshooting.md)
- [GitHub Issues](https://github.com/RobLe3/claude_guardian/issues)

---

**🛡️ Claude Guardian + Claude Code = Secure Development**