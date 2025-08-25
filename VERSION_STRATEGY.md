# Claude Guardian Semantic Versioning Strategy

## Version Mapping for Development Stages

Based on our development evolution, here's the proposed semantic versioning:

### **v1.0.0 - Enhanced Security Scanner (Baseline)**
- **Release Date**: Initial implementation
- **Features**: Context-aware detection, 91.7% accuracy baseline
- **Status**: Foundation system with zero false positives
- **Performance**: 0.16ms average processing time

### **v1.1.0 - Phase 1A Conservative AST Foundation**
- **Release Date**: AST foundation implementation  
- **Features**: + Ultra-conservative AST analysis with performance budgeting
- **Status**: Performance optimization (-8.1% improvement!)
- **New Capabilities**: High-value pattern detection, conservative enhancement

### **v1.2.0 - Phase 1B Context-Required Hybrid Patterns**
- **Release Date**: Hybrid pattern implementation
- **Features**: + Context-required pattern detection, advanced threat analysis
- **Status**: Revolutionary false positive protection with advanced detection
- **New Capabilities**: Command injection + deserialization with context verification

### **v1.3.0 - Phase 1C Complete Data Flow System**  
- **Release Date**: Complete system implementation
- **Features**: + Simplified data flow analysis, source-to-sink detection
- **Status**: Production-ready complete advanced security system
- **New Capabilities**: Multi-line attack detection, flow-based vulnerability analysis

### **Future Versioning Strategy**

#### **v1.x.y - Patch Releases**
- Bug fixes and minor improvements
- Performance optimizations
- Documentation updates
- No new major features

#### **v2.0.0 - Machine Learning Integration (Future)**
- Major architectural change
- ML-based pattern learning
- Breaking changes to API
- Advanced anomaly detection

#### **v2.1.0 - Advanced Flow Analysis (Future)**  
- Inter-procedural flow analysis
- Complex control flow detection
- Library-specific security patterns

## Version Tagging Strategy

### Git Tag Format
- **Release Tags**: `v1.0.0`, `v1.1.0`, `v1.2.0`, `v1.3.0`
- **Pre-release Tags**: `v1.3.0-beta.1`, `v1.3.0-rc.1`
- **Development Tags**: `v1.3.0-dev.20250825`

### Version Identification in Code
Each scanner implementation should include version metadata for tracking and compatibility.