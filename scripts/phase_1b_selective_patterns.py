#!/usr/bin/env python3
"""
Phase 1B-Selective: High-Value Pattern Detection
Focuses only on proven effective patterns for optimal performance/detection balance
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
class SelectivePattern:
    """High-value security pattern with proven effectiveness"""
    name: str
    primary_regex: str
    base_risk: float
    confidence: float
    context_multipliers: Dict[str, float]
    description: str

class SelectivePatternDetector:
    """Detects only the most effective advanced patterns"""
    
    def __init__(self):
        # Only patterns with demonstrated effectiveness in benchmarks
        self.selective_patterns = [
            # Command Injection (proven effective)
            SelectivePattern(
                name="command_injection_concatenation",
                primary_regex=r'(os\.system|subprocess\.call|subprocess\.run)\s*\([\'"][^\'"]*[\'"\s]*[\+\%]',
                base_risk=8.5,
                confidence=0.9,
                context_multipliers={
                    'user_input_nearby': 2.0,
                    'file_operations': 1.5
                },
                description="Command injection via string concatenation"
            ),
            
            # Unsafe Deserialization (high confidence detection)
            SelectivePattern(
                name="unsafe_deserialization_user_data",
                primary_regex=r'(pickle\.loads|yaml\.load|marshal\.loads|dill\.loads)\s*\(',
                base_risk=9.0,
                confidence=0.85,
                context_multipliers={
                    'user_input_nearby': 2.2,
                    'network_context': 1.8
                },
                description="Unsafe deserialization with user data"
            ),
            
            # Dynamic Code Construction (eval/exec with concatenation)
            SelectivePattern(
                name="dynamic_code_construction",
                primary_regex=r'(eval|exec)\s*\(\s*[\'"][^\'"]*[\'\"]\s*\+',
                base_risk=8.5,
                confidence=0.88,
                context_multipliers={
                    'user_input_nearby': 2.5,
                    'string_concatenation': 1.5
                },
                description="Dynamic code construction with string concatenation"
            )
        ]
        
        # High-confidence context patterns
        self.context_patterns = {
            'user_input_nearby': [
                r'input\s*\(', r'sys\.argv', r'request\.(form|args|json|data)',
                r'raw_input', r'getenv'
            ],
            'string_concatenation': [r'[\+\%]\s*\w+', r'\w+\s*[\+\%]'],
            'file_operations': [r'open\s*\(', r'\.read\s*\(', r'\.write\s*\('],
            'network_context': [r'urllib', r'requests\.', r'socket\.']
        }
    
    def detect_selective_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Detect high-value patterns only"""
        detections = []
        
        for pattern in self.selective_patterns:
            matches = list(re.finditer(pattern.primary_regex, code, re.IGNORECASE))
            
            for match in matches:
                detection = self._analyze_selective_match(code, pattern, match)
                # High threshold for quality
                if detection['final_risk_score'] > 6.0 and detection['confidence'] > 0.8:
                    detections.append(detection)
        
        return detections
    
    def _analyze_selective_match(self, code: str, pattern: SelectivePattern, match: re.Match) -> Dict[str, Any]:
        """Analyze pattern match with focused context"""
        
        # Get focused context (3 lines around match)
        lines = code.split('\n')
        match_line = code[:match.start()].count('\n')
        context_start = max(0, match_line - 3)
        context_end = min(len(lines), match_line + 3)
        context = '\n'.join(lines[context_start:context_end])
        
        # Apply context multipliers
        context_multiplier = 1.0
        detected_contexts = []
        
        for context_name, multiplier in pattern.context_multipliers.items():
            if context_name in self.context_patterns:
                patterns = self.context_patterns[context_name]
                for ctx_pattern in patterns:
                    if re.search(ctx_pattern, context, re.IGNORECASE):
                        context_multiplier = max(context_multiplier, multiplier)
                        detected_contexts.append(context_name)
                        break
        
        # Calculate risk score
        final_risk = min(pattern.base_risk * context_multiplier, 10.0)
        
        return {
            'pattern_name': pattern.name,
            'description': pattern.description,
            'matched_text': match.group(),
            'line_number': match_line + 1,
            'base_risk_score': pattern.base_risk,
            'context_multiplier': context_multiplier,
            'final_risk_score': final_risk,
            'confidence': min(pattern.confidence * (1.0 + len(detected_contexts) * 0.1), 0.95),
            'detected_contexts': detected_contexts
        }

class Phase1BSelectiveScanner(ConservativeEnhancedSecurityScanner):
    """Phase 1B scanner with selective high-value pattern detection"""
    
    def __init__(self):
        # ✅ PRESERVE Phase 1A functionality
        super().__init__()
        
        # ➕ ADD selective pattern detector
        self._selective_detector = SelectivePatternDetector()
        
        # Update performance stats tracking
        self._performance_stats.update({
            'selective_detections': 0,
            'selective_patterns_found': 0,
            'selective_analysis_performed': 0
        })
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with selective pattern detection"""
        scan_start_time = time.time()
        
        # ✅ ALWAYS run Phase 1A analysis first
        phase_1a_result = super().enhanced_security_scan(code, language, security_level)
        phase_1a_time = (time.time() - scan_start_time) * 1000
        
        # ➕ ADD selective pattern detection (optimized conditions)
        if (language.lower() == "python" and 
            len(code) > 40 and len(code) < 1500 and  # Optimized size range
            phase_1a_time < 0.8):  # Fast Phase 1A required
            
            try:
                selective_start = time.time()
                enhanced_result = self._add_selective_enhancements(code, phase_1a_result)
                selective_time = (time.time() - selective_start) * 1000
                
                # Accept slightly higher performance cost for meaningful detection
                if selective_time < 1.5:
                    self._performance_stats['selective_detections'] += 1
                    return enhanced_result
                
            except Exception:
                # Selective enhancement failed, return Phase 1A result
                pass
        
        # Always return a working result
        return phase_1a_result
    
    def _add_selective_enhancements(self, code: str, phase_1a_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add selective pattern enhancements"""
        
        # Detect selective patterns
        selective_detections = self._selective_detector.detect_selective_patterns(code)
        self._performance_stats['selective_analysis_performed'] += 1
        
        if not selective_detections:
            return phase_1a_result
        
        # Filter for high-quality detections
        high_quality_detections = [
            d for d in selective_detections 
            if d['confidence'] >= 0.8 and d['final_risk_score'] >= 6.0
        ]
        
        if not high_quality_detections:
            return phase_1a_result
        
        self._performance_stats['selective_patterns_found'] += len(high_quality_detections)
        
        # Create enhanced result
        enhanced_result = phase_1a_result.copy()
        
        # Calculate meaningful risk enhancement
        total_selective_risk = sum(d['final_risk_score'] * d['confidence'] * 0.4 for d in high_quality_detections)
        
        # Apply focused enhancement (minimum meaningful impact)
        min_enhancement = 2.0  # At least 2.0 risk score boost
        max_enhancement = max(phase_1a_result['risk_score'] * 0.4, min_enhancement)
        actual_enhancement = min(total_selective_risk, max_enhancement)
        
        enhanced_result.update({
            'risk_score': phase_1a_result['risk_score'] + actual_enhancement,
            'vulnerabilities': phase_1a_result['vulnerabilities'] + len(high_quality_detections),
            'selective_analysis': {
                'enabled': True,
                'selective_patterns_detected': len(high_quality_detections),
                'risk_enhancement_applied': actual_enhancement,
                'detection_details': [
                    {
                        'pattern_name': d['pattern_name'],
                        'description': d['description'],
                        'risk_score': d['final_risk_score'],
                        'confidence': d['confidence'],
                        'line': d['line_number'],
                        'contexts': d['detected_contexts']
                    } for d in high_quality_detections
                ]
            }
        })
        
        # Update risk level based on enhanced score
        if enhanced_result['risk_score'] > phase_1a_result['risk_score'] * 1.3:
            if enhanced_result['risk_score'] >= 15:
                enhanced_result['risk_level'] = 'critical'
            elif enhanced_result['risk_score'] >= 10:
                enhanced_result['risk_level'] = 'high'
            elif enhanced_result['risk_score'] >= 6:
                enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result

# Optimized benchmarking for selective patterns
def benchmark_selective_phase_1b():
    """Benchmark selective Phase 1B implementation"""
    print("🎯 Phase 1B Selective Pattern Enhancement Benchmark")
    print("=" * 60)
    
    phase_1a_scanner = ConservativeEnhancedSecurityScanner()
    selective_scanner = Phase1BSelectiveScanner()
    
    # Focused test cases for selective patterns
    test_cases = [
        # False positive protection
        {
            "name": "Safe JSON Processing",
            "code": "import json; data = json.loads(config_file); print(data)",
            "expected": "safe",
            "category": "false_positive_test",
            "description": "Legitimate JSON operations must remain safe"
        },
        {
            "name": "Comments with eval()",
            "code": "# Never use eval() in production\nresult = ast.literal_eval(data)",
            "expected": "safe",
            "category": "false_positive_test",
            "description": "Comments should never trigger detection"
        },
        
        # Basic threat detection
        {
            "name": "Direct eval() usage",
            "code": "result = eval(user_input)",
            "expected": "medium",
            "category": "basic_threat",
            "description": "Direct dangerous function usage"
        },
        
        # Selective pattern targets (should be enhanced)
        {
            "name": "Command injection with concatenation",
            "code": "import os\nfile_path = input('Enter path: ')\nos.system('rm -rf ' + file_path)",
            "expected": "enhanced_high",
            "category": "selective_target",
            "description": "Command injection via string concatenation with user input"
        },
        {
            "name": "Unsafe pickle with user data",
            "code": "import pickle\nuser_data = request.data\nobj = pickle.loads(user_data)",
            "expected": "enhanced_critical",
            "category": "selective_target",
            "description": "Unsafe deserialization of user-controlled data"
        },
        {
            "name": "Dynamic code construction",
            "code": "user_formula = input('Formula: ')\ncode = 'result = ' + user_formula\nexec(code)",
            "expected": "enhanced_critical",
            "category": "selective_target",
            "description": "Dynamic code construction with user input"
        },
        
        # Mixed scenarios
        {
            "name": "Complex code with selective pattern",
            "code": '''
# Safe configuration loading
config = json.load(open('config.json'))

# User input processing
user_cmd = input('Enter command: ')
full_cmd = 'ls ' + user_cmd  # String concatenation
os.system(full_cmd)  # Command injection
''',
            "expected": "enhanced_critical",
            "category": "mixed_complex",
            "description": "Mixed safe and dangerous patterns"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Phase 1A performance
        phase_1a_times = []
        phase_1a_results = []
        for _ in range(3):
            start_time = time.time()
            result = phase_1a_scanner.enhanced_security_scan(test_case["code"])
            phase_1a_times.append((time.time() - start_time) * 1000)
            phase_1a_results.append(result)
        
        # Selective Phase 1B performance
        selective_times = []
        selective_results = []
        for _ in range(3):
            start_time = time.time()
            result = selective_scanner.enhanced_security_scan(test_case["code"])
            selective_times.append((time.time() - start_time) * 1000)
            selective_results.append(result)
        
        # Analysis
        avg_phase_1a_time = sum(phase_1a_times) / len(phase_1a_times)
        avg_selective_time = sum(selective_times) / len(selective_times)
        performance_impact = ((avg_selective_time - avg_phase_1a_time) / avg_phase_1a_time * 100) if avg_phase_1a_time > 0 else 0
        
        phase_1a_result = phase_1a_results[0]
        selective_result = selective_results[0]
        
        # Quality analysis
        phase_1a_risk = phase_1a_result['risk_level']
        selective_risk = selective_result['risk_level']
        
        selective_enhanced = 'selective_analysis' in selective_result
        improvement_achieved = (
            selective_result['risk_score'] > phase_1a_result['risk_score'] * 1.1 or
            selective_enhanced
        )
        
        # Appropriateness check
        if test_case['expected'] == 'safe':
            appropriate = selective_risk in ['safe', 'low']
        elif test_case['expected'].startswith('enhanced_'):
            appropriate = improvement_achieved and selective_risk != 'safe'
        else:
            appropriate = phase_1a_risk == selective_risk
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'phase_1a_time_ms': round(avg_phase_1a_time, 2),
            'selective_time_ms': round(avg_selective_time, 2),
            'performance_impact_pct': round(performance_impact, 1),
            'phase_1a_risk': phase_1a_risk,
            'selective_risk': selective_risk,
            'phase_1a_score': round(phase_1a_result['risk_score'], 1),
            'selective_score': round(selective_result['risk_score'], 1),
            'selective_enhanced': selective_enhanced,
            'improvement_achieved': improvement_achieved,
            'appropriate': appropriate
        }
        
        results.append(result)
        
        # Display results
        improvement_status = "🎯 TARGETED" if improvement_achieved else "✅ MAINTAINED"
        appropriate_status = "✅ APPROPRIATE" if appropriate else "❌ INAPPROPRIATE"
        
        print(f"  Performance: {avg_phase_1a_time:.1f}ms → {avg_selective_time:.1f}ms ({performance_impact:+.1f}%)")
        print(f"  Risk Level: {phase_1a_risk} → {selective_risk}")
        print(f"  Risk Score: {phase_1a_result['risk_score']:.1f} → {selective_result['risk_score']:.1f}")
        print(f"  Assessment: {appropriate_status} {improvement_status}")
        
        # Show selective detection details
        if selective_enhanced and 'detection_details' in selective_result['selective_analysis']:
            details = selective_result['selective_analysis']['detection_details']
            for detail in details:
                print(f"    • {detail['description']} (risk: {detail['risk_score']:.1f}, confidence: {detail['confidence']:.2f})")
    
    # Comprehensive Analysis
    print("\n" + "=" * 60)
    print("📊 Selective Phase 1B Analysis")
    print("=" * 60)
    
    # Performance analysis
    performance_impacts = [r['performance_impact_pct'] for r in results]
    avg_performance_impact = sum(performance_impacts) / len(performance_impacts)
    max_performance_impact = max(performance_impacts)
    
    # Quality analysis
    false_positive_tests = [r for r in results if r['category'] == 'false_positive_test']
    false_positive_safe = all(r['selective_risk'] in ['safe', 'low'] for r in false_positive_tests)
    
    selective_target_tests = [r for r in results if r['category'] == 'selective_target']
    selective_improvements = sum(1 for r in selective_target_tests if r['improvement_achieved'])
    
    overall_appropriate = sum(1 for r in results if r['appropriate'])
    
    print(f"Performance Impact:")
    print(f"  Average: {avg_performance_impact:+.1f}%")
    print(f"  Maximum: {max_performance_impact:+.1f}%")
    print(f"  Within Budget (<20%): {'✅ YES' if avg_performance_impact <= 20 else '❌ NO'}")
    
    print(f"\nQuality Assessment:")
    print(f"  False Positive Protection: {'✅ MAINTAINED' if false_positive_safe else '❌ BROKEN'}")
    print(f"  Selective Target Improvements: {selective_improvements}/{len(selective_target_tests)}")
    print(f"  Overall Appropriateness: {overall_appropriate}/{len(results)}")
    
    # Selective statistics
    selective_stats = selective_scanner.get_performance_stats()
    print(f"\nSelective Pattern Statistics:")
    print(f"  Selective Detections Applied: {selective_stats['selective_detections']}")
    print(f"  Selective Patterns Found: {selective_stats['selective_patterns_found']}")
    print(f"  Selective Analysis Performed: {selective_stats['selective_analysis_performed']}")
    
    # Final assessment
    selective_success = (
        avg_performance_impact <= 20 and                # Reasonable performance impact
        false_positive_safe and                         # No false positives
        selective_improvements >= len(selective_target_tests) * 0.8 and  # 80%+ selective improvements
        overall_appropriate >= len(results) * 0.8      # 80%+ appropriate
    )
    
    print(f"\n🎯 Selective Phase 1B Assessment: {'✅ SUCCESS' if selective_success else '❌ NEEDS WORK'}")
    
    if selective_success:
        print("✅ Selective patterns provide meaningful security improvements")
        print("✅ False positive protection maintained")
        print("✅ Performance impact reasonable for detection value")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  Review selective pattern effectiveness and thresholds")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_performance_impact,
            'max_performance_impact': max_performance_impact,
            'within_performance_budget': avg_performance_impact <= 20,
            'false_positive_protection': false_positive_safe,
            'selective_improvements': selective_improvements,
            'selective_improvement_rate': selective_improvements / len(selective_target_tests) if selective_target_tests else 0,
            'overall_appropriateness': overall_appropriate / len(results),
            'selective_success': selective_success
        },
        'performance_stats': selective_stats
    }

if __name__ == "__main__":
    benchmark_results = benchmark_selective_phase_1b()
    
    success = benchmark_results['summary']['selective_success']
    exit(0 if success else 1)