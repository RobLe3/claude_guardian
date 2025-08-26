# 🛡️ Claude Guardian - Improved Setup

**Fixed all major setup issues identified in fresh Claude Code instances**

## 🚀 What's New

### ✅ Issues Fixed
- **Directory Navigation**: No more confusing `cd` errors
- **Go Dependencies**: Python-only setup option (no Go required)
- **Environment Config**: Automatic `.env` generation
- **Claude Code Integration**: Clear, copy-paste instructions

### 🎯 New Setup Options

#### Option 1: Easy Setup (Recommended)
```bash
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian
./easy-setup.sh
```

#### Option 2: Validation First
```bash
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian
python3 scripts/test-setup.py  # Validate before setup
./easy-setup.sh  # Run setup if validation passes
```

#### Option 3: Manual Setup
See [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md) for detailed instructions.

## 📋 Pre-Setup Validation

Before running setup, validate your environment:
```bash
python3 scripts/test-setup.py
```

Expected output:
```
🔍 Claude Guardian Setup Validation
==================================================
📋 Python Environment
🐍 Testing Python environment...
✅ Python 3.11.5

📋 Dependencies  
📦 Testing dependencies...
✅ websockets
✅ fastapi
✅ uvicorn
✅ pydantic

📋 Port Availability
🔌 Testing port 8083...
✅ Port 8083 available

🏆 Score: 6/6 tests passed
🎉 All tests passed! Setup is ready.
```

## 🎯 Setup Results

After running `./easy-setup.sh`:

```
🛡️  Claude Guardian - Easy Setup
Python-only setup for Claude Code integration

✅ Python 3.11.5 found
📦 Installing Python dependencies...
⚙️  Creating MCP configuration...
🚀 Starting Claude Guardian MCP service...
✅ MCP service running (PID: 12345)

🎉 Setup Complete!

Next Steps:
1. Copy this configuration to Claude Code:

{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["/path/to/claude_guardian/scripts/start-mcp-service.py", "--port", "8083"],
  "env": {
    "GUARDIAN_MODE": "production"
  }
}

2. Or use this file: claude-code-config.json
3. Restart Claude Code to load Claude Guardian

Test with: 'scan this code for security issues'
```

## 🔧 What Each Setup Script Does

### `easy-setup.sh`
- ✅ Validates Python 3.8+
- ✅ Installs minimal dependencies (`pip3 install --user websockets fastapi uvicorn pydantic`)
- ✅ Creates minimal `.env` configuration
- ✅ Starts MCP service on port 8083
- ✅ Generates Claude Code configuration
- ✅ Provides clear next steps

### `setup-claude-guardian.sh` (Full Setup)
- ✅ Checks all dependencies (Python, Docker, Git, Go)
- ✅ Handles missing dependencies gracefully
- ✅ Clones repository if needed
- ✅ Sets up Docker stack (if available)
- ✅ Configures environment with secure defaults
- ✅ Validates complete installation

### `test-setup.py`
- ✅ Pre-validates environment before setup
- ✅ Checks Python version and dependencies
- ✅ Tests port availability
- ✅ Validates MCP service can start
- ✅ Tests configuration generation
- ✅ Provides clear pass/fail results

## 🎉 Success Metrics

After setup, you should have:

1. **MCP Service Running**: `lsof -i :8083` shows process
2. **Configuration Ready**: `claude-code-config.json` file created
3. **Service Validated**: `python3 scripts/validate-mcp-tools.py` passes
4. **Integration Path**: Clear instructions for Claude Code

## 📞 Support

If setup still fails:

1. **Run Validation**: `python3 scripts/test-setup.py`
2. **Check Logs**: `tail /tmp/claude-guardian-mcp.log`
3. **Test Service**: `curl http://localhost:8083/health`
4. **Report Issue**: Include validation output in issue report

## 🔄 Migration from Previous Setup

If you had setup issues before:

```bash
# Stop any existing services
lsof -ti :8083 | xargs kill -9 2>/dev/null || true

# Clean start
rm -f .env .mcp_pid claude-code-config.json

# Run new setup
./easy-setup.sh
```

---

**🛡️ Claude Guardian - Now with frustration-free setup!**