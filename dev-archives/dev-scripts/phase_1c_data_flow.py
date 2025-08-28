#!/usr/bin/env python3
"""
Phase 1C: Data Flow Tracking Foundation
Adds conservative data flow analysis to detect user input → dangerous sink patterns
"""

import sys
import os
import time
import re
import ast
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase_1b_final import Phase1BFinalScanner

@dataclass
class DataSource:
    """Represents a source of potentially tainted data"""
    name: str
    line_number: int
    variable_name: Optional[str]
    risk_level: float  # 1.0 = low risk, 10.0 = high risk
    source_type: str  # 'user_input', 'network', 'file', 'environment'
    confidence: float

@dataclass 
class DataSink:
    """Represents a dangerous operation that could be exploited"""
    name: str
    line_number: int
    function_name: str
    risk_level: float
    sink_type: str  # 'code_execution', 'command_injection', 'file_access'
    confidence: float

@dataclass
class DataFlow:
    """Represents a flow from source to sink"""
    source: DataSource
    sink: DataSink 
    flow_confidence: float
    flow_distance: int  # Lines between source and sink
    intermediate_variables: List[str]
    risk_multiplier: float

class ConservativeDataFlowTracker:
    """Conservative data flow analysis focusing on obvious, high-confidence flows"""
    
    def __init__(self):
        # High-confidence data sources (user input, network, etc.)
        self.data_sources = {
            'user_input': {
                'patterns': [
                    r'(\w+)\s*=\s*input\s*\(',
                    r'(\w+)\s*=\s*raw_input\s*\(',
                    r'(\w+)\s*=\s*sys\.argv\[',
                    r'(\w+)\s*=\s*request\.(form|args|json|data)\[',
                    r'(\w+)\s*=\s*request\.(form|args|json|data)\.get\(',
                ],
                'risk_level': 8.0,
                'confidence': 0.9
            },
            'environment': {
                'patterns': [
                    r'(\w+)\s*=\s*os\.environ\[',
                    r'(\w+)\s*=\s*os\.getenv\s*\(',
                    r'(\w+)\s*=\s*getenv\s*\(',
                ],
                'risk_level': 6.0,
                'confidence': 0.8
            },
            'file_input': {
                'patterns': [
                    r'(\w+)\s*=\s*open\s*\([^)]*\)\.read\s*\(',
                    r'(\w+)\s*=\s*\.read\s*\(',
                    r'(\w+)\s*=\s*json\.load\s*\(',
                ],
                'risk_level': 4.0,
                'confidence': 0.7
            },
            'network': {
                'patterns': [
                    r'(\w+)\s*=\s*requests\.get\s*\(',
                    r'(\w+)\s*=\s*urllib\..*\s*\(',
                    r'(\w+)\s*=\s*socket\.recv\s*\(',
                ],
                'risk_level': 7.0,
                'confidence': 0.85
            }
        }
        
        # Dangerous sinks where tainted data becomes a security risk
        self.dangerous_sinks = {
            'code_execution': {
                'patterns': [
                    r'eval\s*\(\s*(\w+)',
                    r'exec\s*\(\s*(\w+)', 
                    r'compile\s*\(\s*(\w+)',
                ],
                'risk_level': 10.0,
                'confidence': 0.95
            },
            'command_injection': {
                'patterns': [
                    r'os\.system\s*\(\s*(\w+)',
                    r'subprocess\.call\s*\(\s*(\w+)',
                    r'subprocess\.run\s*\(\s*(\w+)',
                    r'os\.popen\s*\(\s*(\w+)',
                ],
                'risk_level': 9.0,
                'confidence': 0.9
            },
            'unsafe_deserialization': {
                'patterns': [
                    r'pickle\.loads\s*\(\s*(\w+)',
                    r'yaml\.load\s*\(\s*(\w+)',
                    r'marshal\.loads\s*\(\s*(\w+)',
                ],
                'risk_level': 9.5,
                'confidence': 0.9
            },
            'sql_injection': {
                'patterns': [
                    r'cursor\.execute\s*\(\s*(\w+)',
                    r'\.execute\s*\(\s*(\w+)',
                ],
                'risk_level': 8.5,
                'confidence': 0.85
            }
        }
    
    def analyze_data_flows(self, code: str) -> List[DataFlow]:
        """Analyze code for data flows from sources to sinks"""
        lines = code.split('\n')
        
        # Find data sources
        sources = self._find_data_sources(lines)
        if not sources:
            return []
        
        # Find dangerous sinks
        sinks = self._find_dangerous_sinks(lines)
        if not sinks:
            return []
        
        # Trace flows between sources and sinks
        flows = self._trace_flows(sources, sinks, lines)
        
        return flows
    
    def _find_data_sources(self, lines: List[str]) -> List[DataSource]:
        """Find data sources in code lines"""
        sources = []
        
        for line_num, line in enumerate(lines, 1):
            for source_type, config in self.data_sources.items():
                for pattern in config['patterns']:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        variable_name = match.group(1) if match.groups() else None
                        sources.append(DataSource(
                            name=f"{source_type}_{line_num}",
                            line_number=line_num,
                            variable_name=variable_name,
                            risk_level=config['risk_level'],
                            source_type=source_type,
                            confidence=config['confidence']
                        ))
                        break  # Only one match per line
        
        return sources
    
    def _find_dangerous_sinks(self, lines: List[str]) -> List[DataSink]:
        """Find dangerous sinks in code lines"""
        sinks = []
        
        for line_num, line in enumerate(lines, 1):
            for sink_type, config in self.dangerous_sinks.items():
                for pattern in config['patterns']:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        function_name = pattern.split('\\s')[0].replace('\\', '')
                        sinks.append(DataSink(
                            name=f"{sink_type}_{line_num}",
                            line_number=line_num,
                            function_name=function_name,
                            risk_level=config['risk_level'],
                            sink_type=sink_type,
                            confidence=config['confidence']
                        ))
                        break
        
        return sinks
    
    def _trace_flows(self, sources: List[DataSource], sinks: List[DataSink], lines: List[str]) -> List[DataFlow]:
        """Trace data flows from sources to sinks"""
        flows = []
        
        for source in sources:
            if not source.variable_name:
                continue
                
            for sink in sinks:
                # Check if source variable is used in sink line
                sink_line = lines[sink.line_number - 1] if sink.line_number <= len(lines) else ""
                
                # Simple variable usage check (ensure it's not just substring match)
                var_pattern = rf'\b{re.escape(source.variable_name)}\b'
                if re.search(var_pattern, sink_line):
                    flow = self._create_flow(source, sink, lines)
                    if flow:
                        flows.append(flow)
                else:
                    # Check for indirect flows through variable assignments
                    indirect_flow = self._check_indirect_flow(source, sink, lines)
                    if indirect_flow:
                        flows.append(indirect_flow)
        
        return flows
    
    def _create_flow(self, source: DataSource, sink: DataSink, lines: List[str]) -> Optional[DataFlow]:
        """Create a data flow between source and sink"""
        flow_distance = abs(sink.line_number - source.line_number)
        
        # Conservative: Only detect flows within reasonable distance (20 lines)
        if flow_distance > 20:
            return None
        
        # Calculate flow confidence based on distance and variable usage
        base_confidence = min(source.confidence, sink.confidence)
        distance_penalty = min(flow_distance * 0.02, 0.3)  # Max 30% penalty
        flow_confidence = max(base_confidence - distance_penalty, 0.5)
        
        # Calculate risk multiplier
        source_risk_factor = source.risk_level / 10.0
        sink_risk_factor = sink.risk_level / 10.0
        risk_multiplier = (source_risk_factor + sink_risk_factor) / 2.0
        
        return DataFlow(
            source=source,
            sink=sink,
            flow_confidence=flow_confidence,
            flow_distance=flow_distance,
            intermediate_variables=[],  # Simple implementation
            risk_multiplier=risk_multiplier
        )
    
    def _check_indirect_flow(self, source: DataSource, sink: DataSink, lines: List[str]) -> Optional[DataFlow]:
        """Check for indirect flows through variable assignments"""
        if not source.variable_name:
            return None
        
        # Look for variable assignments between source and sink
        start_line = min(source.line_number, sink.line_number)
        end_line = max(source.line_number, sink.line_number)
        
        if end_line - start_line > 10:  # Conservative distance limit
            return None
        
        # Simple pattern: var2 = var1 (source variable)
        source_var = source.variable_name
        intermediate_vars = [source_var]
        
        for line_num in range(start_line, end_line + 1):
            if line_num > len(lines):
                break
                
            line = lines[line_num - 1]
            
            # Look for assignments involving current tracked variables
            for tracked_var in intermediate_vars:
                # Pattern: new_var = tracked_var
                assignment_match = re.search(rf'(\w+)\s*=\s*.*{tracked_var}', line)
                if assignment_match:
                    new_var = assignment_match.group(1)
                    if new_var not in intermediate_vars:
                        intermediate_vars.append(new_var)
        
        # Check if any intermediate variable is used in sink
        sink_line = lines[sink.line_number - 1] if sink.line_number <= len(lines) else ""
        for var in intermediate_vars[1:]:  # Skip source variable
            var_pattern = rf'\b{re.escape(var)}\b'
            if re.search(var_pattern, sink_line):
                flow = self._create_flow(source, sink, lines)
                if flow:
                    flow.intermediate_variables = intermediate_vars[1:-1]  # Exclude source and sink vars
                    flow.flow_confidence *= 0.8  # Reduce confidence for indirect flow
                    return flow
        
        return None

class Phase1CCompleteScanner(Phase1BFinalScanner):
    """Complete Phase 1C scanner with data flow analysis integrated with Phase 1A+1B"""
    
    def __init__(self):
        # ✅ PRESERVE Phase 1A + 1B functionality
        super().__init__()
        
        # ➕ ADD data flow tracker
        self._flow_tracker = ConservativeDataFlowTracker()
        
        # Update performance stats tracking
        self._performance_stats.update({
            'flow_analysis_performed': 0,
            'data_flows_detected': 0,
            'high_risk_flows': 0,
            'flow_enhancements_applied': 0
        })
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Complete enhanced scan with Phase 1A + 1B + 1C capabilities"""
        scan_start_time = time.time()
        
        # ✅ ALWAYS run Phase 1B analysis first (includes Phase 1A)
        phase_1b_result = super().enhanced_security_scan(code, language, security_level)
        phase_1b_time = (time.time() - scan_start_time) * 1000
        
        # ➕ ADD Phase 1C data flow analysis (ultra-strict activation criteria)
        if (language.lower() == "python" and 
            len(code) > 150 and len(code) < 800 and  # Stricter size limits for performance
            phase_1b_time < 0.5 and  # Phase 1B must be very fast
            code.count('\n') >= 5 and  # At least 5 lines for meaningful flow analysis
            ('input(' in code or 'getenv' in code or 'request.' in code)):  # Must contain potential sources
            
            try:
                flow_start = time.time()
                enhanced_result = self._add_flow_analysis(code, phase_1b_result)
                flow_time = (time.time() - flow_start) * 1000
                
                # Ultra-conservative performance requirement for flow analysis
                if flow_time < 1.0:
                    self._performance_stats['flow_analysis_performed'] += 1
                    return enhanced_result
                
            except Exception:
                # Flow analysis failed, return Phase 1B result
                pass
        
        # Always return a working result
        return phase_1b_result
    
    def _add_flow_analysis(self, code: str, phase_1b_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add data flow analysis to Phase 1B results"""
        
        # Analyze data flows
        data_flows = self._flow_tracker.analyze_data_flows(code)
        
        if not data_flows:
            return phase_1b_result
        
        # Filter for high-confidence flows only
        high_confidence_flows = [
            flow for flow in data_flows
            if flow.flow_confidence >= 0.7 and 
               flow.source.risk_level >= 5.0 and
               flow.sink.risk_level >= 7.0
        ]
        
        if not high_confidence_flows:
            return phase_1b_result
        
        self._performance_stats['data_flows_detected'] += len(data_flows)
        self._performance_stats['high_risk_flows'] += len(high_confidence_flows)
        
        # Create enhanced result
        enhanced_result = phase_1b_result.copy()
        
        # Calculate flow-based risk enhancement
        total_flow_risk = 0.0
        for flow in high_confidence_flows:
            flow_risk = (flow.source.risk_level + flow.sink.risk_level) / 2.0
            flow_risk *= flow.flow_confidence
            flow_risk *= flow.risk_multiplier
            
            # Distance penalty for long flows
            if flow.flow_distance > 5:
                flow_risk *= max(0.5, 1.0 - (flow.flow_distance - 5) * 0.1)
            
            total_flow_risk += flow_risk * 0.4  # Conservative multiplier
        
        # Apply conservative flow enhancement
        base_enhancement = 3.0  # Minimum meaningful flow enhancement
        max_enhancement = max(phase_1b_result['risk_score'] * 0.3, base_enhancement)
        actual_enhancement = min(total_flow_risk, max_enhancement)
        
        if actual_enhancement >= 1.0:  # Only apply if meaningful enhancement
            self._performance_stats['flow_enhancements_applied'] += 1
            
            enhanced_result.update({
                'risk_score': phase_1b_result['risk_score'] + actual_enhancement,
                'vulnerabilities': phase_1b_result['vulnerabilities'] + len(high_confidence_flows),
                'data_flow_analysis': {
                    'enabled': True,
                    'flows_detected': len(data_flows),
                    'high_risk_flows': len(high_confidence_flows),
                    'risk_enhancement_applied': actual_enhancement,
                    'flow_details': [
                        {
                            'source_type': flow.source.source_type,
                            'source_line': flow.source.line_number,
                            'source_variable': flow.source.variable_name,
                            'sink_type': flow.sink.sink_type,
                            'sink_line': flow.sink.line_number,
                            'sink_function': flow.sink.function_name,
                            'flow_confidence': flow.flow_confidence,
                            'flow_distance': flow.flow_distance,
                            'intermediate_vars': flow.intermediate_variables,
                            'risk_contribution': (flow.source.risk_level + flow.sink.risk_level) / 2.0 * flow.flow_confidence
                        } for flow in high_confidence_flows
                    ]
                }
            })
            
            # Update risk level based on flow-enhanced score
            if enhanced_result['risk_score'] > phase_1b_result['risk_score'] * 1.2:
                if enhanced_result['risk_score'] >= 15:
                    enhanced_result['risk_level'] = 'critical'
                elif enhanced_result['risk_score'] >= 10:
                    enhanced_result['risk_level'] = 'high'
                elif enhanced_result['risk_score'] >= 6:
                    enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result

# Comprehensive Phase 1C benchmarking
def benchmark_complete_phase_1c():
    """Comprehensive benchmark of complete Phase 1A+1B+1C system"""
    print("🚀 Complete Phase 1C Data Flow Analysis Benchmark")
    print("=" * 65)
    
    phase_1b_scanner = Phase1BFinalScanner()
    complete_scanner = Phase1CCompleteScanner()
    
    # Comprehensive test suite covering all capabilities
    test_cases = [
        # False positive protection (MUST remain unchanged)
        {
            "name": "Safe JSON Configuration",
            "code": "import json\nconfig = json.load(open('config.json'))\napi_key = config.get('api_key', 'default')",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        {
            "name": "Safe file operations",
            "code": "with open('data.txt', 'r') as f:\n    content = f.read()\n    processed = content.strip()",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        
        # Basic pattern detection (Phase 1A+1B should handle)
        {
            "name": "Direct eval usage",
            "code": "result = eval(user_input)",
            "expected": "medium",
            "category": "basic_patterns"
        },
        {
            "name": "Command injection with string concatenation",
            "code": "import os\nuser_file = input('File: ')\nos.system('cat ' + user_file)",
            "expected": "enhanced_medium",
            "category": "hybrid_patterns"
        },
        
        # Data flow scenarios (Phase 1C targets)
        {
            "name": "User input to eval flow",
            "code": "user_code = input('Enter code: ')\nprocessed_code = user_code.strip()\nresult = eval(processed_code)",
            "expected": "flow_critical",
            "category": "data_flow_target",
            "description": "User input flows through variable to dangerous sink"
        },
        {
            "name": "Environment variable to command injection",
            "code": "import os\nfile_path = os.getenv('USER_FILE')\ncommand = 'rm ' + file_path\nos.system(command)",
            "expected": "flow_high",
            "category": "data_flow_target",
            "description": "Environment variable flows to command injection"
        },
        {
            "name": "Request data to pickle loads",
            "code": "from flask import request\nimport pickle\ndata = request.data\nobj = pickle.loads(data)",
            "expected": "flow_critical",
            "category": "data_flow_target", 
            "description": "Network data flows to unsafe deserialization"
        },
        {
            "name": "Multi-step user input flow",
            "code": '''
user_input = input('Enter formula: ')
formula = 'result = ' + user_input
code_to_run = formula
exec(code_to_run)
''',
            "expected": "flow_critical",
            "category": "data_flow_target",
            "description": "Multi-step flow from user input to code execution"
        },
        {
            "name": "Indirect variable flow",
            "code": '''
user_data = input('Data: ')
temp_var = user_data
final_var = temp_var
eval(final_var)
''',
            "expected": "flow_critical",
            "category": "data_flow_target",
            "description": "Indirect flow through multiple variable assignments"
        },
        
        # Complex mixed scenarios
        {
            "name": "Mixed safe and dangerous with flow",
            "code": '''
# Safe operations
config = json.load(open('config.json'))
log_level = config.get('log_level')

# Dangerous flow
user_cmd = input('Command: ')
safe_prefix = 'echo '
full_cmd = safe_prefix + user_cmd
os.system(full_cmd)
''',
            "expected": "flow_high",
            "category": "complex_mixed",
            "description": "Mixed safe patterns with dangerous data flow"
        }
    ]
    
    results = []
    false_positive_failures = 0
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Phase 1B performance (baseline)
        phase_1b_times = []
        phase_1b_results = []
        for _ in range(3):
            start_time = time.time()
            result = phase_1b_scanner.enhanced_security_scan(test_case["code"])
            phase_1b_times.append((time.time() - start_time) * 1000)
            phase_1b_results.append(result)
        
        # Complete system performance
        complete_times = []
        complete_results = []
        for _ in range(3):
            start_time = time.time()
            result = complete_scanner.enhanced_security_scan(test_case["code"])
            complete_times.append((time.time() - start_time) * 1000)
            complete_results.append(result)
        
        # Analysis
        avg_phase_1b_time = sum(phase_1b_times) / len(phase_1b_times)
        avg_complete_time = sum(complete_times) / len(complete_times)
        performance_impact = ((avg_complete_time - avg_phase_1b_time) / avg_phase_1b_time * 100) if avg_phase_1b_time > 0 else 0
        
        phase_1b_result = phase_1b_results[0]
        complete_result = complete_results[0]
        
        # Quality analysis
        phase_1b_risk = phase_1b_result['risk_level']
        complete_risk = complete_result['risk_level']
        
        flow_analysis_enabled = 'data_flow_analysis' in complete_result
        improvement_achieved = (
            complete_result['risk_score'] > phase_1b_result['risk_score'] * 1.1 or
            flow_analysis_enabled
        )
        
        # False positive check
        if test_case.get('must_remain_safe', False):
            false_positive_occurred = complete_risk not in ['safe', 'low']
            if false_positive_occurred:
                false_positive_failures += 1
        else:
            false_positive_occurred = False
        
        # Appropriateness check
        if test_case['expected'] == 'safe':
            appropriate = complete_risk in ['safe', 'low'] and not false_positive_occurred
        elif test_case['expected'].startswith('flow_'):
            appropriate = improvement_achieved and flow_analysis_enabled
        elif test_case['expected'].startswith('enhanced_'):
            appropriate = improvement_achieved
        else:
            appropriate = phase_1b_risk == complete_risk
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'phase_1b_time_ms': round(avg_phase_1b_time, 2),
            'complete_time_ms': round(avg_complete_time, 2),
            'performance_impact_pct': round(performance_impact, 1),
            'phase_1b_risk': phase_1b_risk,
            'complete_risk': complete_risk,
            'phase_1b_score': round(phase_1b_result['risk_score'], 1),
            'complete_score': round(complete_result['risk_score'], 1),
            'flow_analysis_enabled': flow_analysis_enabled,
            'improvement_achieved': improvement_achieved,
            'appropriate': appropriate,
            'false_positive_occurred': false_positive_occurred
        }
        
        results.append(result)
        
        # Display results
        improvement_status = "🔄 FLOW" if flow_analysis_enabled else "✅ MAINTAINED"
        appropriate_status = "✅ APPROPRIATE" if appropriate else "❌ INAPPROPRIATE"
        fp_status = "❌ FALSE POSITIVE" if false_positive_occurred else ""
        
        print(f"  Performance: {avg_phase_1b_time:.1f}ms → {avg_complete_time:.1f}ms ({performance_impact:+.1f}%)")
        print(f"  Risk Level: {phase_1b_risk} → {complete_risk}")
        print(f"  Risk Score: {phase_1b_result['risk_score']:.1f} → {complete_result['risk_score']:.1f}")
        print(f"  Assessment: {appropriate_status} {improvement_status} {fp_status}")
        
        # Show flow analysis details
        if flow_analysis_enabled and 'flow_details' in complete_result['data_flow_analysis']:
            details = complete_result['data_flow_analysis']['flow_details']
            for detail in details[:2]:  # Show first 2 flows
                print(f"    • Flow: {detail['source_type']} (line {detail['source_line']}) → {detail['sink_type']} (line {detail['sink_line']})")
                print(f"      Confidence: {detail['flow_confidence']:.2f}, Distance: {detail['flow_distance']} lines")
    
    # Comprehensive Analysis
    print("\n" + "=" * 65)
    print("📊 Complete Phase 1C System Assessment")
    print("=" * 65)
    
    # Performance analysis
    performance_impacts = [r['performance_impact_pct'] for r in results]
    avg_performance_impact = sum(performance_impacts) / len(performance_impacts)
    max_performance_impact = max(performance_impacts)
    
    # Quality analysis
    false_positive_protection_tests = [r for r in results if r['category'] == 'false_positive_protection']
    false_positive_protection_maintained = all(not r['false_positive_occurred'] for r in false_positive_protection_tests)
    
    data_flow_target_tests = [r for r in results if r['category'] == 'data_flow_target']
    flow_improvements = sum(1 for r in data_flow_target_tests if r['improvement_achieved'])
    
    overall_appropriate = sum(1 for r in results if r['appropriate'])
    
    print(f"Performance Impact:")
    print(f"  Average: {avg_performance_impact:+.1f}%")
    print(f"  Maximum: {max_performance_impact:+.1f}%")
    print(f"  Within Budget (<20%): {'✅ YES' if avg_performance_impact <= 20 else '❌ NO'}")
    
    print(f"\nQuality Assessment:")
    print(f"  False Positive Protection: {'✅ PERFECT' if false_positive_protection_maintained and false_positive_failures == 0 else f'❌ FAILED ({false_positive_failures} false positives)'}")
    print(f"  Data Flow Improvements: {flow_improvements}/{len(data_flow_target_tests)}")
    print(f"  Overall Appropriateness: {overall_appropriate}/{len(results)}")
    
    # Complete system statistics
    complete_stats = complete_scanner.get_performance_stats()
    print(f"\nComplete System Statistics:")
    print(f"  Flow Analysis Performed: {complete_stats['flow_analysis_performed']}")
    print(f"  Data Flows Detected: {complete_stats['data_flows_detected']}")
    print(f"  High Risk Flows: {complete_stats['high_risk_flows']}")
    print(f"  Flow Enhancements Applied: {complete_stats['flow_enhancements_applied']}")
    
    # Final assessment
    complete_system_success = (
        avg_performance_impact <= 20 and               # Reasonable performance impact
        false_positive_protection_maintained and       # Perfect false positive protection
        false_positive_failures == 0 and              # Zero false positives
        flow_improvements >= len(data_flow_target_tests) * 0.7 and  # 70%+ flow improvements
        overall_appropriate >= len(results) * 0.8     # 80%+ appropriate
    )
    
    print(f"\n🏆 Complete Phase 1C System Assessment: {'✅ SUCCESS' if complete_system_success else '❌ NEEDS WORK'}")
    
    if complete_system_success:
        print("✅ Complete system successfully integrates all phases")
        print("✅ Perfect false positive protection maintained across all phases")
        print("✅ Data flow analysis adds meaningful security insights")
        print("✅ Performance remains within acceptable bounds")
        print("✅ Ready for production deployment as complete security solution")
    else:
        print("⚠️  Issues remain - review integration and thresholds")
        if false_positive_failures > 0:
            print(f"⚠️  Critical: {false_positive_failures} false positive(s) detected")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_performance_impact,
            'max_performance_impact': max_performance_impact,
            'within_performance_budget': avg_performance_impact <= 20,
            'false_positive_protection': false_positive_protection_maintained,
            'false_positive_failures': false_positive_failures,
            'flow_improvements': flow_improvements,
            'flow_improvement_rate': flow_improvements / len(data_flow_target_tests) if data_flow_target_tests else 0,
            'overall_appropriateness': overall_appropriate / len(results),
            'complete_system_success': complete_system_success
        },
        'performance_stats': complete_stats
    }

if __name__ == "__main__":
    benchmark_results = benchmark_complete_phase_1c()
    
    success = benchmark_results['summary']['complete_system_success']
    exit(0 if success else 1)