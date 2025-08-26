# Development Archives

This directory contains historical development artifacts, logs, and legacy documentation from Claude Guardian's evolution from v1.x to v2.0.0.

---

## 📁 Directory Structure

### **`benchmarks/`**
Performance testing and benchmark results:
- `benchmark-suite.py` - Comprehensive benchmarking framework  
- `rebench.py` - Quick performance validation script
- `REBENCH_SUMMARY.md` - Latest benchmark results (A+ grades)
- `CLAUDE_GUARDIAN_FINAL_REPORT.md` - Complete performance assessment
- `PERSISTENCE_STATUS.md` - Database persistence verification

### **`logs/`**
Development and testing logs:
- `mcp-service.log` - MCP service development logs
- `mcp-service-fixed.log` - Fixed service implementation logs  
- `mcp-stack-test.log` - Stack integration testing logs

### **`legacy-reports/`**
Historical analysis and phase reports:
- Phase completion reports from v1.x development
- System verification and compliance documents
- MCP integration test results
- Security alignment verification reports
- Lessons learned and protection analysis

### **`documentation-drafts/`**
Draft analysis and system design documents:
- Framework analysis documents
- Reality checks and system assessments  
- Go integration assessments
- LightRAG correlation analysis
- Version 2.0 roadmap drafts

---

## 🚀 Key Achievements Tracked

### **Performance Evolution**
- **v1.3.1**: 91.7% detection accuracy, <100ms response time
- **v2.0.0**: 100% detection accuracy, 5.5ms response time (95% faster)

### **Architecture Evolution**  
- **v1.x**: WebSocket-based MCP with separate services
- **v2.0**: Unified FastAPI application with HTTP MCP protocol

### **Database Evolution**
- **v1.x**: Single PostgreSQL with limited persistence
- **v2.0**: Multi-database (PostgreSQL + Qdrant + Redis) with full persistence

---

## 📊 Historical Benchmarks

### **Response Time Improvements**
```
v1.3.1: ~100ms average
v2.0.0: 5.5ms average (95% improvement)
```

### **Detection Accuracy**
```
v1.3.1: 91.7% accuracy, 0% false positives
v2.0.0: 100% accuracy, 0% false positives maintained
```

### **Reliability**
```
v1.3.1: 80% multi-session success rate
v2.0.0: 100% success rate under all conditions
```

---

## 🔍 Archive Usage

### **For Researchers**
Historical data showing security system evolution, performance optimization techniques, and architectural decisions.

### **For Developers** 
Reference implementations, test methodologies, and lessons learned during the v1 to v2 transition.

### **For Auditing**
Complete development history, test results, and compliance verification documentation.

---

## ⚠️ Archive Note

These files are preserved for historical reference and should not be used in production. For current documentation and implementation, see the main project files and `docs/` directory.

**Current Production Version**: Claude Guardian v2.0.0-alpha  
**Archive Period**: Development phases through August 2025