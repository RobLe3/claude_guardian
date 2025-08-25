#!/usr/bin/env python3
"""
Phase 1B: Targeted Pattern Enhancement
Builds on Phase 1A by adding specific high-value pattern detection for advanced threats
"""

import sys
import os
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from phase_1a_conservative_scanner import ConservativeEnhancedSecurityScanner

@dataclass
class TargetedPattern:
    """Enhanced pattern definition with context-aware scoring"""
    name: str
    primary_regex: str
    secondary_regex: Optional[str]  # For two-step patterns
    base_risk: float
    context_multipliers: Dict[str, float]
    description: str
    examples: List[str]

class AdvancedPatternDetector:
    """Detects sophisticated attack patterns that bypass basic detection"""
    
    def __init__(self):
        self.targeted_patterns = [
            # Indirect Execution Patterns
            TargetedPattern(
                name="indirect_eval_execution",
                primary_regex=r'(\w+)\s*=\s*(eval|exec|compile|__import__)',
                secondary_regex=r'\1\s*\(',  # Variable used later
                base_risk=7.0,
                context_multipliers={
                    'user_input_nearby': 2.0,
                    'string_concatenation': 1.5,
                    'loop_context': 1.3
                },
                description="Indirect execution via variable assignment",
                examples=[
                    "func = eval; func(user_input)",
                    "dangerous = exec; dangerous(malicious_code)"
                ]
            ),
            
            # Dynamic Code Construction
            TargetedPattern(
                name="dynamic_code_construction",
                primary_regex=r'(eval|exec)\s*\(\s*[\'"][^\'\"]*\'\s*\+',
                secondary_regex=None,
                base_risk=8.0,
                context_multipliers={
                    'user_input_nearby': 2.5,
                    'web_context': 1.8,
                    'loop_context': 1.4
                },
                description="Dynamic code construction with string concatenation",
                examples=[
                    "eval('result = ' + user_formula)",
                    "exec('import ' + user_module)"
                ]
            ),
            
            # Command Injection Enhancement  
            TargetedPattern(
                name="enhanced_command_injection",
                primary_regex=r'(os\.system|subprocess\.call|subprocess\.run)\s*\([\'"][^\'\"]*\'\s*[\+\%]',
                secondary_regex=None,
                base_risk=8.5,
                context_multipliers={
                    'user_input_nearby': 2.0,
                    'file_operations': 1.6,
                    'network_context': 1.4
                },
                description="Command injection via string formatting or concatenation",
                examples=[
                    "os.system('rm -rf ' + user_path)",
                    "subprocess.call('wget %s' % user_url, shell=True)"
                ]
            ),
            
            # Serialization Vulnerabilities
            TargetedPattern(
                name="unsafe_deserialization",
                primary_regex=r'(pickle\.loads|yaml\.load|marshal\.loads|dill\.loads)\s*\(',
                secondary_regex=None,
                base_risk=9.0,
                context_multipliers={
                    'user_input_nearby': 2.2,
                    'network_context': 1.8,
                    'file_input': 1.5
                },
                description="Unsafe deserialization of untrusted data",
                examples=[
                    "pickle.loads(user_data)",
                    "yaml.load(request.data)"
                ]
            ),
            
            # Template Injection
            TargetedPattern(
                name="template_injection",
                primary_regex=r'(template\.render|jinja2\.Template|\.format)\s*\([^)]*\*\*',
                secondary_regex=None,
                base_risk=7.5,
                context_multipliers={
                    'user_input_nearby': 2.0,
                    'web_context': 1.7,
                    'dict_expansion': 1.5
                },
                description="Template injection via uncontrolled data expansion",
                examples=[
                    "template.render(**user_data)",
                    "jinja2.Template(template_str).render(**request.json)"
                ]
            ),
            
            # SQL Injection Enhancement
            TargetedPattern(
                name="enhanced_sql_injection",
                primary_regex=r'(cursor\.execute|query|SELECT|INSERT|UPDATE|DELETE).*[\'\"][^\'\"]*[\'\"].*[\+\%]',
                secondary_regex=None,
                base_risk=8.0,
                context_multipliers={
                    'user_input_nearby': 2.1,
                    'web_context': 1.8,
                    'string_formatting': 1.6
                },
                description="SQL injection via dynamic query construction",
                examples=[
                    "cursor.execute('SELECT * FROM users WHERE name = \"' + user_name + '\"')",
                    "query = 'DELETE FROM %s WHERE id = %d' % (table, user_id)"
                ]
            )
        ]
        
        # Context detection patterns
        self.context_patterns = {
            'user_input_nearby': [
                r'input\s*\(', r'sys\.argv', r'request\.(form|args|json|data)',
                r'os\.environ', r'getenv', r'raw_input'
            ],
            'string_concatenation': [r'[\+\%]\s*\w+', r'\w+\s*[\+\%]', r'\.format\s*\('],
            'loop_context': [r'for\s+\w+\s+in', r'while\s+\w+'],
            'web_context': [r'request\.', r'flask\.', r'django\.', r'@app\.route'],
            'file_operations': [r'open\s*\(', r'file\s*\(', r'\.read\s*\(', r'\.write\s*\('],
            'network_context': [r'urllib', r'requests\.', r'socket\.', r'http'],
            'dict_expansion': [r'\*\*\w+', r'\.items\s*\(', r'\.keys\s*\(']
        }
    
    def detect_advanced_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Detect advanced attack patterns with context analysis"""
        detections = []
        
        for pattern in self.targeted_patterns:
            # Check primary pattern
            primary_matches = list(re.finditer(pattern.primary_regex, code, re.IGNORECASE))
            
            for match in primary_matches:
                detection = self._analyze_pattern_match(code, pattern, match)
                # Stricter threshold to prevent false positives
                if detection['final_risk_score'] > 6.0 and detection['confidence'] > 0.8:
                    detections.append(detection)
        
        return detections
    
    def _analyze_pattern_match(self, code: str, pattern: TargetedPattern, match: re.Match) -> Dict[str, Any]:
        """Analyze a pattern match with context awareness"""
        
        # Get surrounding context (5 lines before and after)
        lines = code.split('\\n')
        match_line = code[:match.start()].count('\\n')
        context_start = max(0, match_line - 5)
        context_end = min(len(lines), match_line + 5)
        context = '\\n'.join(lines[context_start:context_end])
        
        # Analyze context for risk multipliers
        risk_multipliers = self._analyze_context(context, pattern.context_multipliers)
        
        # Calculate final risk score
        base_risk = pattern.base_risk
        context_multiplier = max(risk_multipliers.values()) if risk_multipliers else 1.0
        final_risk = min(base_risk * context_multiplier, 10.0)  # Cap at 10
        
        # Check for secondary pattern if defined
        secondary_pattern_found = False
        if pattern.secondary_regex:
            # Replace captured group references
            secondary_regex = pattern.secondary_regex
            if '\\\\1' in secondary_regex and match.groups():
                secondary_regex = secondary_regex.replace('\\\\1', re.escape(match.group(1)))
            
            secondary_pattern_found = bool(re.search(secondary_regex, code, re.IGNORECASE))
            
            if secondary_pattern_found:
                final_risk *= 1.3  # 30% bonus for two-step patterns
        
        return {
            'pattern_name': pattern.name,
            'description': pattern.description,
            'matched_text': match.group(),
            'line_number': match_line + 1,
            'base_risk_score': base_risk,
            'context_multiplier': context_multiplier,
            'final_risk_score': final_risk,
            'risk_multipliers': risk_multipliers,
            'secondary_pattern_found': secondary_pattern_found,
            'confidence': min(0.9, 0.6 + (final_risk / 20))  # Higher risk = higher confidence
        }
    
    def _analyze_context(self, context: str, multiplier_patterns: Dict[str, float]) -> Dict[str, float]:
        """Analyze context for risk multipliers"""
        detected_multipliers = {}
        
        for multiplier_name, multiplier_value in multiplier_patterns.items():
            if multiplier_name in self.context_patterns:
                patterns = self.context_patterns[multiplier_name]
                for pattern in patterns:
                    if re.search(pattern, context, re.IGNORECASE):
                        detected_multipliers[multiplier_name] = multiplier_value
                        break
        
        return detected_multipliers

class Phase1BEnhancedScanner(ConservativeEnhancedSecurityScanner):
    """Phase 1B scanner with targeted pattern enhancements building on Phase 1A"""
    
    def __init__(self):
        # ✅ PRESERVE Phase 1A functionality
        super().__init__()
        
        # ➕ ADD Phase 1B targeted pattern detector
        self._pattern_detector = AdvancedPatternDetector()
        
        # Update performance stats tracking
        self._performance_stats.update({
            'phase_1b_detections': 0,
            'advanced_patterns_found': 0,
            'context_analysis_performed': 0
        })
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with Phase 1A + Phase 1B capabilities"""
        scan_start_time = time.time()
        
        # ✅ ALWAYS run Phase 1A analysis first
        phase_1a_result = super().enhanced_security_scan(code, language, security_level)
        phase_1a_time = (time.time() - scan_start_time) * 1000
        
        # ➕ ADD Phase 1B targeted pattern detection (ultra-conservative)
        if (language.lower() == "python" and 
            len(code) > 100 and len(code) < 1000 and  # Very tight size limits
            phase_1a_time < 0.5 and  # Phase 1A must be extremely fast
            phase_1a_result['risk_level'] in ['medium', 'high', 'critical']):  # Only on risky code
            
            try:
                phase_1b_start = time.time()
                enhanced_result = self._add_phase_1b_enhancements(code, phase_1a_result)
                phase_1b_time = (time.time() - phase_1b_start) * 1000
                
                # Stricter performance requirement (<1ms)
                if phase_1b_time < 1.0:
                    self._performance_stats['phase_1b_detections'] += 1
                    return enhanced_result
                
            except Exception:
                # Phase 1B failed, return Phase 1A result
                pass
        
        # Always return a working result
        return phase_1a_result
    
    def _add_phase_1b_enhancements(self, code: str, phase_1a_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add Phase 1B targeted pattern enhancements"""
        
        # Conservative: Only enhance if Phase 1A already found medium+ risk
        if phase_1a_result['risk_level'] in ['safe', 'low']:
            return phase_1a_result
        
        # Detect advanced patterns
        advanced_detections = self._pattern_detector.detect_advanced_patterns(code)
        self._performance_stats['context_analysis_performed'] += 1
        
        if not advanced_detections:
            return phase_1a_result
        
        # Very strict filtering for false positive prevention
        high_confidence_detections = [
            d for d in advanced_detections 
            if d['confidence'] >= 0.85 and d['final_risk_score'] >= 6.5  # Stricter thresholds
        ]
        
        if not high_confidence_detections:
            return phase_1a_result
        
        self._performance_stats['advanced_patterns_found'] += len(high_confidence_detections)
        
        # Create enhanced result
        enhanced_result = phase_1a_result.copy()
        
        # Calculate risk enhancement
        total_phase_1b_risk = sum(d['final_risk_score'] * d['confidence'] * 0.3 for d in high_confidence_detections)
        
        # Apply conservative enhancement (max 80% increase over Phase 1A)
        max_enhancement = phase_1a_result['risk_score'] * 0.8
        actual_enhancement = min(total_phase_1b_risk, max_enhancement)
        
        enhanced_result.update({
            'risk_score': phase_1a_result['risk_score'] + actual_enhancement,
            'vulnerabilities': phase_1a_result['vulnerabilities'] + len(high_confidence_detections),
            'phase_1b_analysis': {
                'enabled': True,
                'advanced_patterns_detected': len(high_confidence_detections),
                'risk_enhancement_applied': actual_enhancement,
                'detection_details': [
                    {
                        'pattern_name': d['pattern_name'],
                        'description': d['description'],
                        'risk_score': d['final_risk_score'],
                        'confidence': d['confidence'],
                        'line': d['line_number'],
                        'context_multipliers': list(d['risk_multipliers'].keys())
                    } for d in high_confidence_detections
                ]
            }
        })
        
        # Update risk level based on enhanced score
        if enhanced_result['risk_score'] > phase_1a_result['risk_score'] * 1.5:
            if enhanced_result['risk_score'] >= 15:
                enhanced_result['risk_level'] = 'critical'
            elif enhanced_result['risk_score'] >= 10:
                enhanced_result['risk_level'] = 'high'
            elif enhanced_result['risk_score'] >= 6:
                enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result

# Comprehensive Phase 1B benchmarking
def comprehensive_benchmark_phase_1b():
    """Comprehensive benchmark comparing Phase 1A vs Phase 1B capabilities"""
    print("🚀 Phase 1B Targeted Pattern Enhancement Benchmark")
    print("=" * 60)
    
    phase_1a_scanner = ConservativeEnhancedSecurityScanner()
    phase_1b_scanner = Phase1BEnhancedScanner()
    
    # Test cases targeting Phase 1B improvements
    test_cases = [
        # False positive protection (must remain safe)
        {
            "name": "JSON Processing (Safe)",
            "code": "import json; data = json.loads(user_input); print(data)",
            "expected": "safe",
            "category": "false_positive_test",
            "description": "Basic legitimate operations must remain safe"
        },
        {
            "name": "Comments with dangerous keywords",
            "code": "# Never use eval() or exec()\\nresult = ast.literal_eval(data)",
            "expected": "safe", 
            "category": "false_positive_test",
            "description": "Comments should never be flagged"
        },
        
        # Basic threats (should be caught by Phase 1A)
        {
            "name": "Direct eval() usage",
            "code": "result = eval(user_input)",
            "expected": "medium",
            "category": "basic_threat",
            "description": "Direct dangerous function calls"
        },
        
        # Advanced threats (Phase 1B improvements)
        {
            "name": "Indirect eval() execution",
            "code": "dangerous_func = eval\\nuser_input = input('Code: ')\\nresult = dangerous_func(user_input)",
            "expected": "enhanced_high",
            "category": "advanced_threat",
            "description": "Indirect execution with user input"
        },
        {
            "name": "Dynamic code construction",
            "code": "formula = 'result = ' + user_formula\\nexec(formula)",
            "expected": "enhanced_high",
            "category": "advanced_threat", 
            "description": "Dynamic code construction patterns"
        },
        {
            "name": "Command injection with concatenation",
            "code": "import os\\nfile_path = input('Path: ')\\nos.system('rm -rf ' + file_path)",
            "expected": "enhanced_high",
            "category": "advanced_threat",
            "description": "Command injection via string concatenation"
        },
        {
            "name": "Unsafe deserialization",
            "code": "import pickle\\ndata = request.data\\nobj = pickle.loads(data)",
            "expected": "enhanced_critical",
            "category": "advanced_threat",
            "description": "Unsafe deserialization of user data"
        },
        {
            "name": "Template injection",
            "code": "from jinja2 import Template\\ntemplate.render(**user_data)",
            "expected": "enhanced_high",
            "category": "advanced_threat",
            "description": "Template injection via uncontrolled expansion"
        },
        {
            "name": "SQL injection with formatting",
            "code": "query = 'SELECT * FROM users WHERE name = \\\"%s\\\"' % user_name\\ncursor.execute(query)",
            "expected": "enhanced_high",
            "category": "advanced_threat",
            "description": "SQL injection via string formatting"
        },
        
        # Complex mixed scenarios
        {
            "name": "Mixed legitimate and dangerous",
            "code": '''
# Configuration loading
config = json.load(open('config.json'))

# User input processing  
user_code = input('Enter formula: ')
formula = 'result = ' + user_code  # Dangerous concatenation
exec(formula)  # Dangerous execution
''',
            "expected": "enhanced_critical",
            "category": "complex_mixed",
            "description": "Mix of safe and dangerous operations"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\nTesting: {test_case['name']}")
        
        # Phase 1A performance
        phase_1a_times = []
        phase_1a_results = []
        for _ in range(3):
            start_time = time.time()
            result = phase_1a_scanner.enhanced_security_scan(test_case["code"])
            phase_1a_times.append((time.time() - start_time) * 1000)
            phase_1a_results.append(result)
        
        # Phase 1B performance
        phase_1b_times = []
        phase_1b_results = []
        for _ in range(3):
            start_time = time.time()
            result = phase_1b_scanner.enhanced_security_scan(test_case["code"])
            phase_1b_times.append((time.time() - start_time) * 1000)
            phase_1b_results.append(result)
        
        # Analysis
        avg_phase_1a_time = sum(phase_1a_times) / len(phase_1a_times)
        avg_phase_1b_time = sum(phase_1b_times) / len(phase_1b_times)
        performance_impact = ((avg_phase_1b_time - avg_phase_1a_time) / avg_phase_1a_time * 100) if avg_phase_1a_time > 0 else 0
        
        phase_1a_result = phase_1a_results[0]
        phase_1b_result = phase_1b_results[0]
        
        # Quality analysis
        phase_1a_risk = phase_1a_result['risk_level']
        phase_1b_risk = phase_1b_result['risk_level']
        
        phase_1b_enhanced = 'phase_1b_analysis' in phase_1b_result
        improvement_achieved = (
            phase_1b_result['risk_score'] > phase_1a_result['risk_score'] * 1.2 or
            phase_1b_enhanced
        )
        
        # Appropriateness check
        if test_case['expected'] == 'safe':
            appropriate = phase_1b_risk in ['safe', 'low']
        elif test_case['expected'].startswith('enhanced_'):
            appropriate = improvement_achieved and phase_1b_risk != 'safe'
        else:
            appropriate = phase_1a_risk == phase_1b_risk
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'phase_1a_time_ms': round(avg_phase_1a_time, 2),
            'phase_1b_time_ms': round(avg_phase_1b_time, 2),
            'performance_impact_pct': round(performance_impact, 1),
            'phase_1a_risk': phase_1a_risk,
            'phase_1b_risk': phase_1b_risk,
            'phase_1a_score': round(phase_1a_result['risk_score'], 1),
            'phase_1b_score': round(phase_1b_result['risk_score'], 1),
            'phase_1b_enhanced': phase_1b_enhanced,
            'improvement_achieved': improvement_achieved,
            'appropriate': appropriate
        }
        
        results.append(result)
        
        # Display results
        improvement_status = "🚀 ENHANCED" if improvement_achieved else "✅ MAINTAINED"
        appropriate_status = "✅ APPROPRIATE" if appropriate else "❌ INAPPROPRIATE"
        
        print(f"  Performance: {avg_phase_1a_time:.1f}ms → {avg_phase_1b_time:.1f}ms ({performance_impact:+.1f}%)")
        print(f"  Risk Level: {phase_1a_risk} → {phase_1b_risk}")
        print(f"  Risk Score: {phase_1a_result['risk_score']:.1f} → {phase_1b_result['risk_score']:.1f}")
        print(f"  Assessment: {appropriate_status} {improvement_status}")
        
        # Show Phase 1B detection details if present
        if phase_1b_enhanced and 'detection_details' in phase_1b_result['phase_1b_analysis']:
            details = phase_1b_result['phase_1b_analysis']['detection_details']
            for detail in details[:2]:  # Show first 2
                print(f"    • {detail['description']} (risk: {detail['risk_score']:.1f}, confidence: {detail['confidence']:.2f})")
    
    # Comprehensive Analysis
    print("\\n" + "=" * 60)
    print("📊 Phase 1B Enhancement Analysis")
    print("=" * 60)
    
    # Performance analysis
    performance_impacts = [r['performance_impact_pct'] for r in results]
    avg_performance_impact = sum(performance_impacts) / len(performance_impacts)
    max_performance_impact = max(performance_impacts)
    
    # Quality analysis  
    false_positive_tests = [r for r in results if r['category'] == 'false_positive_test']
    false_positive_safe = all(r['phase_1b_risk'] in ['safe', 'low'] for r in false_positive_tests)
    
    advanced_threat_tests = [r for r in results if r['category'] == 'advanced_threat']
    advanced_improvements = sum(1 for r in advanced_threat_tests if r['improvement_achieved'])
    
    overall_appropriate = sum(1 for r in results if r['appropriate'])
    
    print(f"Performance Impact:")
    print(f"  Average: {avg_performance_impact:+.1f}%")
    print(f"  Maximum: {max_performance_impact:+.1f}%")
    print(f"  Within Budget (<25%): {'✅ YES' if avg_performance_impact <= 25 else '❌ NO'}")
    
    print(f"\\nQuality Assessment:")
    print(f"  False Positive Protection: {'✅ MAINTAINED' if false_positive_safe else '❌ BROKEN'}")
    print(f"  Advanced Threat Improvements: {advanced_improvements}/{len(advanced_threat_tests)}")
    print(f"  Overall Appropriateness: {overall_appropriate}/{len(results)}")
    
    # Enhancement statistics
    phase_1b_stats = phase_1b_scanner.get_performance_stats()
    print(f"\\nPhase 1B Statistics:")
    print(f"  Phase 1B Detections Applied: {phase_1b_stats['phase_1b_detections']}")
    print(f"  Advanced Patterns Found: {phase_1b_stats['advanced_patterns_found']}")
    print(f"  Context Analysis Performed: {phase_1b_stats['context_analysis_performed']}")
    
    # Final assessment
    phase_1b_success = (
        avg_performance_impact <= 25 and                    # Reasonable performance impact
        false_positive_safe and                             # No false positives
        advanced_improvements >= len(advanced_threat_tests) * 0.7 and  # 70%+ advanced improvements
        overall_appropriate >= len(results) * 0.8          # 80%+ appropriate
    )
    
    print(f"\\n🎯 Phase 1B Assessment: {'✅ SUCCESS' if phase_1b_success else '❌ NEEDS WORK'}")
    
    if phase_1b_success:
        print("✅ Phase 1B successfully enhances advanced threat detection")
        print("✅ False positive protection maintained from Phase 1A")
        print("✅ Performance impact within acceptable bounds")
        print("✅ Ready for Phase 1C implementation")
    else:
        print("⚠️  Address issues before proceeding to Phase 1C")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_performance_impact,
            'max_performance_impact': max_performance_impact,
            'within_performance_budget': avg_performance_impact <= 25,
            'false_positive_protection': false_positive_safe,
            'advanced_improvements': advanced_improvements,
            'advanced_improvement_rate': advanced_improvements / len(advanced_threat_tests) if advanced_threat_tests else 0,
            'overall_appropriateness': overall_appropriate / len(results),
            'phase_1b_success': phase_1b_success
        },
        'performance_stats': phase_1b_stats
    }

if __name__ == "__main__":
    benchmark_results = comprehensive_benchmark_phase_1b()
    
    success = benchmark_results['summary']['phase_1b_success']
    exit(0 if success else 1)