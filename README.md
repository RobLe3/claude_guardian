# Claude Guardian

**Version: v2.0.0-alpha** | **Status: Production Ready** | **API: v2.0**

**Claude Guardian** is a security pattern detection tool for Claude Code that scans for potentially malicious code patterns using rule-based detection. It provides MCP integration for real-time security scanning of code submitted to Claude Code.

---

## 🎯 **Current Status: Production Ready**

✅ **FastAPI Application** - Basic HTTP server implementation  
✅ **PostgreSQL Database** - Simple data storage for audit logs  
✅ **Real-time Pattern Detection** - Rule-based security scanning  
✅ **Claude Code Integration** - MCP protocol implementation  

---

## 🚀 **Actual Capabilities**

### 🛡️ **Pattern-based Threat Detection**
- **Basic Code Injection Detection**: Simple regex patterns for eval(), exec(), system() calls
- **SQL Injection Patterns**: Basic detection of common SQL injection attempts
- **Path Traversal Detection**: Simple patterns for directory traversal attempts
- **Command Injection**: Basic detection of shell command injection patterns

**Current Implementation:**
- Detection Method: Regular expression pattern matching
- Pattern Count: Basic security patterns implemented
- Response Format: JSON results via REST API
- Integration: MCP protocol for Claude Code

### 🔧 **Technical Implementation**
- **Pattern Storage**: Simple in-memory pattern definitions
- **Scanning Engine**: Synchronous text pattern matching
- **Result Processing**: Basic threat level classification
- **Logging**: Simple audit trail to PostgreSQL database

**Architecture:**
- Database: Single PostgreSQL instance for audit logs
- Containerization: Docker support for deployment
- API: REST endpoints for security scanning
- MCP Integration: HTTP-based protocol server

### 🔗 **MCP Protocol Integration**
- **HTTP Server**: Basic MCP protocol implementation
- **Security Tools**: Code scanning functionality via MCP tools
- **Protocol Support**: Compatible with Claude Code MCP interface
- **Single Session**: Basic request/response handling

**MCP Integration Details:**
- HTTP Server: Running on configurable port
- Tool Availability: Basic security scanning tools
- Response Format: JSON compatible with Claude Code
- Integration: Standard MCP protocol implementation

### 🗄️ **Data Architecture**
- **PostgreSQL**: Simple database for audit logs and scan results
- **Docker Deployment**: Basic containerized deployment
- **Persistent Storage**: Database data persisted via Docker volumes
- **Configuration**: Environment-based configuration management

---

## 📊 **Current Functionality**

### **Claude Guardian Implementation:**
- **Basic Pattern Matching**: Simple regex-based detection
- **Common Threats**: Detection of well-known attack patterns
- **False Positives**: May occur with legitimate code patterns
- **Development Tool**: Suitable for development environment security

### **Detection Coverage:**
✅ **Basic Code Injection**: Simple eval(), exec(), system() patterns  
✅ **SQL Injection**: Common SQL injection string patterns  
✅ **Path Traversal**: Simple directory traversal attempts  
⚠️ **Complex Attacks**: Limited detection of sophisticated threats  

---

## 🏃 **Quick Start**

**⚡ 5-Minute Setup:** See [GETTING_STARTED.md](GETTING_STARTED.md) for comprehensive installation guide.
**🔗 Claude Code:** See [CLAUDE_CODE_INTEGRATION.md](CLAUDE_CODE_INTEGRATION.md) for complete MCP integration.
**📋 API Documentation:** See [API.md](API.md) for complete API reference and endpoints.
**🏗️ Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md) for system design and project structure.
**📊 Performance:** See [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md) for measured performance data.

### **One-Command Setup**

```bash
# Clone and start
git clone https://github.com/RobLe3/claude_guardian.git
cd claude_guardian

# Universal setup with intelligent routing
./setup.sh

# Manage services after setup
./manage.sh status  # Check service health
./manage.sh logs    # View service logs
```

### **Claude Code Integration**

```json
// Use generated configuration file:
cp claude-code-mcp-config.json ~/.claude-code/mcp/

// Or manually add to Claude Code:
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["src.claude_guardian.main:app", "--host", "0.0.0.0", "--port", "8083"]
}
```

**✅ Ready!** Claude Code now has basic security scanning tools available.

---

## 📚 **Architecture**

### **Simple Architecture**
```
┌─────────────┐
│ Claude Code │
└──────┬──────┘
       │
   MCP │ Protocol
       │
┌──────┴──────┐
│ MCP Server  │
│ (FastAPI)   │
└──────┬──────┘
       │
┌──────┴──────┐
│ Security    │
│ Scanner     │
└──────┬──────┘
       │
┌──────┴──────┐
│ PostgreSQL  │
│ Database    │
└─────────────┘
```

### **Core Components**
- **FastAPI Application**: HTTP server implementing MCP protocol
- **Security Scanner**: Basic pattern matching for threat detection
- **PostgreSQL Database**: Simple storage for audit logs and results
- **Pattern Engine**: Regex-based detection of common security threats
- **MCP Protocol Layer**: Basic HTTP-based integration with Claude Code
- **Configuration Manager**: Environment-based application configuration

---

## 🔧 **Configuration**

### **Environment Setup**
```bash
# Basic Environment Configuration
POSTGRES_DB=claude_guardian
POSTGRES_USER=cguser
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DATA_PATH=./data/postgres
MCP_SERVER_PORT=8083
LOG_LEVEL=INFO
```

### **Detection Patterns**
```yaml
# Basic pattern matching for common threats
patterns:
  code_injection: ["eval(", "exec(", "system("]
  sql_injection: ["' OR '1'='1", "UNION SELECT", "DROP TABLE"]
  path_traversal: ["../", "..\\", "/..", "\\..""] 
  command_injection: ["|", "&&", ";", "`", "$("]

# Detection configuration
settings:
  case_sensitive: false
  regex_enabled: true
  logging_enabled: true
```

---

## 🧪 **Testing & Validation**

### **Basic Testing**
```bash
# Run basic tests
python3 -m pytest tests/
# Basic unit tests for pattern matching

# Health check
curl http://localhost:8083/health
# Simple health status endpoint

# MCP tools check
curl http://localhost:8083/api/v1/mcp/tools
# List available MCP tools
```

### **Current Status**
- **Pattern Matching**: ✅ Basic regex patterns working
- **Database Connection**: ✅ PostgreSQL connectivity functional
- **MCP Integration**: ✅ Basic MCP protocol implementation
- **Docker Deployment**: ✅ Container setup working
- **API Endpoints**: ✅ REST API responding to requests

---

## ⚠️ **Current Limitations**

### **Implementation Constraints**
- **Detection Method**: Only basic regex pattern matching (no AI/ML)
- **False Positives**: May flag legitimate code that matches patterns
- **Sophistication**: Cannot detect advanced or obfuscated attacks
- **Context Awareness**: Limited understanding of code context
- **Language Support**: Basic patterns for common languages only

### **NOT Implemented**
- ❌ Machine learning or AI-based analysis
- ❌ Vector database (Qdrant) integration
- ❌ LightRAG or semantic search capabilities
- ❌ Advanced behavioral analysis
- ❌ Complex attack chain detection
- ❌ Real-time threat intelligence feeds
- ❌ Enterprise-grade scalability features
- ❌ Advanced reporting and analytics
- ❌ Custom rule engine or UI
- ❌ SIEM integration

### **Resource Requirements**
- **Minimum**: 2GB RAM, 5GB storage
- **Recommended**: 4GB RAM, 10GB storage
- **Docker**: Single container deployment only

---

## 🎯 **Development Maturity & Future Direction**

### **Current Achievement Level: Basic Security Scanner**

**What We've Actually Built:**
- ✅ **Simple Pattern Detection**: Basic regex matching for common threats
- ✅ **MCP Integration**: Working protocol implementation for Claude Code
- ✅ **Database Storage**: PostgreSQL for basic audit logging
- ✅ **Docker Deployment**: Containerized application setup
- ✅ **REST API**: Basic HTTP endpoints for scanning functionality
- ✅ **Documentation**: Clear setup and usage instructions

### **Where We're Heading**

**Potential Improvements:**
- **Pattern Refinement**: Improve accuracy and reduce false positives
- **Context Analysis**: Add basic code context understanding
- **Language Support**: Expand patterns for more programming languages
- **Performance**: Optimize scanning speed for larger codebases

**Possible Future Features:**
- **Machine Learning**: Implement ML-based threat detection
- **Vector Search**: Add semantic similarity detection
- **Advanced Analysis**: AST-based code analysis
- **Custom Rules**: User-configurable detection patterns

**Integration Ideas:**
- **IDE Plugins**: Real-time scanning in development environments
- **CI/CD Integration**: Automated security checks in build pipelines
- **Reporting**: Enhanced logging and threat analysis reports
- **Configuration**: Web UI for pattern management

### **Community & Support Welcome**

**How You Can Contribute:**
- 🔍 **Security Researchers**: Help identify new attack patterns and evasion techniques
- 💻 **Developers**: Contribute language-specific detection modules
- 🏢 **Enterprise Users**: Share real-world deployment feedback and requirements
- 🧪 **Testing**: Help validate detection accuracy across different environments
- 📚 **Documentation**: Improve guides, tutorials, and best practices

**Good Ideas Always Welcome**: Whether it's new detection algorithms, performance optimizations, or novel security approaches - we're open to innovation and collaboration.

---

## 📈 **Current Implementation Status**

### **Pattern Detection Capabilities**
- **Pattern Coverage**: Basic regex patterns for common threats
- **Detection Types**: Simple code injection, SQL injection, path traversal
- **Database Logging**: Basic audit log storage in PostgreSQL
- **API Integration**: REST endpoints for security scanning
- **System Monitoring**: Basic health check endpoint

### **System Performance**  
- **Response Time**: Variable, depends on input size and pattern complexity
- **Concurrent Requests**: Basic FastAPI concurrency support
- **Database Connection**: Simple PostgreSQL connection management
- **Resource Usage**: Typical for small FastAPI application

### **Integration Capabilities**
- **HTTP API**: Basic REST endpoints for MCP protocol
- **Tool Availability**: Security scanning tools via MCP interface
- **Session Handling**: Simple request/response processing
- **Database Logging**: Basic audit trail functionality

---

## 🤝 **Contributing**

### **Development Setup**
```bash
cd /path/to/claude_guardian  # Navigate to your Claude Guardian installation

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development environment
docker compose up -d
```

### **Contribution Guidelines**
- **Code Quality**: Write tests for new functionality
- **Documentation**: Update README and comments for changes
- **Security**: Follow basic security practices
- **Functionality**: Ensure changes don't break existing features

---

## 📄 **Version & License**

**Current Version**: v2.0.0-alpha (Basic Security Scanner)  
**API Version**: v2.0 (FastAPI-based with HTTP MCP protocol)  
**Release Date**: August 26, 2025  

For complete version history and upgrade guides, see [CHANGELOG.md](CHANGELOG.md).

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Claude Guardian Team

---

## 🎉 **Acknowledgments**

- **Database Layer**: PostgreSQL for basic data storage and logging
- **Pattern Engine**: Simple regex-based pattern matching
- **Web Framework**: FastAPI for HTTP server implementation
- **Container Support**: Docker for application deployment
- **Protocol Integration**: Basic MCP protocol implementation
- **Development Tools**: Testing framework and development utilities

---

<div align="center">

**🛡️ Protect Your Code. Secure Your Future. 🛡️**

**[Getting Started](GETTING_STARTED.md)** • **[Architecture](ARCHITECTURE.md)** • **[Performance](PERFORMANCE_BENCHMARKS.md)** • **[Issues](../../issues)**

[![Development Status](https://img.shields.io/badge/Status-Development-yellow.svg)](#-current-status-development)
[![Basic Patterns](https://img.shields.io/badge/Detection-Basic%20Patterns-orange.svg)](#-current-functionality)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue.svg)](#-mcp-protocol-integration)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](#-quick-start)

</div>