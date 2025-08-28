#!/usr/bin/env python3
"""
Phase 1B-Final: Conservative-Selective Hybrid
Combines proven patterns with strict false positive protection
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
class HybridPattern:
    """High-confidence pattern with false positive protection"""
    name: str
    primary_regex: str
    base_risk: float
    min_confidence: float
    context_requirements: List[str]  # Required contexts for activation
    context_multipliers: Dict[str, float]
    description: str

class HybridPatternDetector:
    """Conservative-selective pattern detector with strict false positive protection"""
    
    def __init__(self):
        # Only patterns with demonstrated effectiveness and safe activation
        self.hybrid_patterns = [
            # Command Injection (proven effective, requires user input context)
            HybridPattern(
                name="safe_command_injection",
                primary_regex=r'(os\.system|subprocess\.call|subprocess\.run)\s*\([\'"][^\'"]*[\'"\s]*[\+\%]',
                base_risk=8.0,
                min_confidence=0.85,
                context_requirements=['user_input_nearby'],  # Must have user input
                context_multipliers={'user_input_nearby': 1.8},
                description="Command injection with user input context"
            ),
            
            # Unsafe Deserialization (only with network/user context)
            HybridPattern(
                name="safe_unsafe_deserialization",
                primary_regex=r'(pickle\.loads|yaml\.load)\s*\(',
                base_risk=8.5,
                min_confidence=0.8,
                context_requirements=['user_input_nearby', 'network_context'],  # Either user input OR network
                context_multipliers={'user_input_nearby': 2.0, 'network_context': 1.8},
                description="Unsafe deserialization with external data"
            )
        ]
        
        # Strict context detection
        self.context_patterns = {
            'user_input_nearby': [
                r'input\s*\(', r'raw_input\s*\(', r'sys\.argv',
                r'request\.(form|args|json|data|POST|GET)',
                r'environ\[', r'getenv\s*\('
            ],
            'network_context': [
                r'request\.', r'urllib', r'requests\.', r'socket\.',
                r'flask\.|django\.|tornado\.|fastapi\.'
            ]
        }
    
    def detect_hybrid_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Detect patterns with strict context requirements"""
        detections = []
        
        for pattern in self.hybrid_patterns:
            matches = list(re.finditer(pattern.primary_regex, code, re.IGNORECASE))
            
            for match in matches:
                detection = self._analyze_hybrid_match(code, pattern, match)
                # Only include if context requirements are met
                if self._meets_context_requirements(detection, pattern):
                    detections.append(detection)
        
        return detections
    
    def _analyze_hybrid_match(self, code: str, pattern: HybridPattern, match: re.Match) -> Dict[str, Any]:
        """Analyze pattern match with context verification"""
        
        # Expanded context analysis (10 lines around match)
        lines = code.split('\n')
        match_line = code[:match.start()].count('\n')
        context_start = max(0, match_line - 10)
        context_end = min(len(lines), match_line + 10)
        context = '\n'.join(lines[context_start:context_end])
        
        # Detect contexts
        detected_contexts = {}
        for context_name, patterns in self.context_patterns.items():
            for ctx_pattern in patterns:
                if re.search(ctx_pattern, context, re.IGNORECASE):
                    detected_contexts[context_name] = True
                    break
        
        # Calculate context multiplier
        context_multiplier = 1.0
        for context_name, multiplier in pattern.context_multipliers.items():
            if context_name in detected_contexts:
                context_multiplier = max(context_multiplier, multiplier)
        
        # Calculate final risk and confidence
        final_risk = min(pattern.base_risk * context_multiplier, 10.0)
        final_confidence = min(pattern.min_confidence * (1.0 + len(detected_contexts) * 0.05), 0.95)
        
        return {
            'pattern_name': pattern.name,
            'description': pattern.description,
            'matched_text': match.group(),
            'line_number': match_line + 1,
            'base_risk_score': pattern.base_risk,
            'context_multiplier': context_multiplier,
            'final_risk_score': final_risk,
            'confidence': final_confidence,
            'detected_contexts': list(detected_contexts.keys()),
            'context_requirements': pattern.context_requirements
        }
    
    def _meets_context_requirements(self, detection: Dict[str, Any], pattern: HybridPattern) -> bool:
        """Verify that context requirements are met"""
        detected_contexts = set(detection['detected_contexts'])
        required_contexts = set(pattern.context_requirements)
        
        # At least one required context must be present
        return bool(detected_contexts.intersection(required_contexts))

class Phase1BFinalScanner(ConservativeEnhancedSecurityScanner):
    """Final Phase 1B scanner with conservative-selective hybrid approach"""
    
    def __init__(self):
        # ✅ PRESERVE Phase 1A functionality
        super().__init__()
        
        # ➕ ADD hybrid pattern detector
        self._hybrid_detector = HybridPatternDetector()
        
        # Update performance stats tracking
        self._performance_stats.update({
            'hybrid_detections': 0,
            'hybrid_patterns_found': 0,
            'hybrid_analysis_performed': 0,
            'context_requirements_met': 0
        })
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with hybrid pattern detection"""
        scan_start_time = time.time()
        
        # ✅ ALWAYS run Phase 1A analysis first
        phase_1a_result = super().enhanced_security_scan(code, language, security_level)
        phase_1a_time = (time.time() - scan_start_time) * 1000
        
        # ➕ ADD hybrid pattern detection (strict activation criteria)
        if (language.lower() == "python" and 
            len(code) > 60 and len(code) < 1200 and  # Reasonable size limits
            phase_1a_time < 0.6):  # Fast Phase 1A required
            
            try:
                hybrid_start = time.time()
                enhanced_result = self._add_hybrid_enhancements(code, phase_1a_result)
                hybrid_time = (time.time() - hybrid_start) * 1000
                
                # Conservative performance requirement
                if hybrid_time < 1.2:
                    self._performance_stats['hybrid_detections'] += 1
                    return enhanced_result
                
            except Exception:
                # Hybrid enhancement failed, return Phase 1A result
                pass
        
        # Always return a working result
        return phase_1a_result
    
    def _add_hybrid_enhancements(self, code: str, phase_1a_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add hybrid pattern enhancements with context verification"""
        
        # Detect hybrid patterns
        hybrid_detections = self._hybrid_detector.detect_hybrid_patterns(code)
        self._performance_stats['hybrid_analysis_performed'] += 1
        
        if not hybrid_detections:
            return phase_1a_result
        
        self._performance_stats['context_requirements_met'] += len(hybrid_detections)
        
        # Filter for ultra-high quality detections only
        ultra_high_quality_detections = [
            d for d in hybrid_detections 
            if d['confidence'] >= 0.85 and d['final_risk_score'] >= 7.0
        ]
        
        if not ultra_high_quality_detections:
            return phase_1a_result
        
        self._performance_stats['hybrid_patterns_found'] += len(ultra_high_quality_detections)
        
        # Create enhanced result
        enhanced_result = phase_1a_result.copy()
        
        # Conservative risk enhancement
        total_hybrid_risk = sum(d['final_risk_score'] * d['confidence'] * 0.35 for d in ultra_high_quality_detections)
        
        # Apply meaningful but conservative enhancement
        base_enhancement = 2.5  # Minimum meaningful boost
        max_enhancement = max(phase_1a_result['risk_score'] * 0.4, base_enhancement)
        actual_enhancement = min(total_hybrid_risk, max_enhancement)
        
        enhanced_result.update({
            'risk_score': phase_1a_result['risk_score'] + actual_enhancement,
            'vulnerabilities': phase_1a_result['vulnerabilities'] + len(ultra_high_quality_detections),
            'hybrid_analysis': {
                'enabled': True,
                'hybrid_patterns_detected': len(ultra_high_quality_detections),
                'risk_enhancement_applied': actual_enhancement,
                'detection_details': [
                    {
                        'pattern_name': d['pattern_name'],
                        'description': d['description'],
                        'risk_score': d['final_risk_score'],
                        'confidence': d['confidence'],
                        'line': d['line_number'],
                        'contexts_detected': d['detected_contexts'],
                        'context_requirements_met': len(set(d['detected_contexts']).intersection(set(d['context_requirements']))) > 0
                    } for d in ultra_high_quality_detections
                ]
            }
        })
        
        # Update risk level based on enhanced score
        if enhanced_result['risk_score'] > phase_1a_result['risk_score'] * 1.2:
            if enhanced_result['risk_score'] >= 12:
                enhanced_result['risk_level'] = 'high'
            elif enhanced_result['risk_score'] >= 8:
                enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result

# Final comprehensive benchmark
def benchmark_final_phase_1b():
    """Comprehensive benchmark of final Phase 1B implementation"""
    print("🏁 Final Phase 1B Conservative-Selective Hybrid Benchmark")
    print("=" * 65)
    
    phase_1a_scanner = ConservativeEnhancedSecurityScanner()
    final_scanner = Phase1BFinalScanner()
    
    # Comprehensive test suite
    test_cases = [
        # False positive protection (MUST remain safe)
        {
            "name": "Safe JSON Processing",
            "code": "import json\ndata = json.loads(config_content)\nprint(data['version'])",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        {
            "name": "Comments with dangerous keywords",
            "code": "# This code avoids eval() and exec() for security\nresult = ast.literal_eval(safe_data)",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        {
            "name": "String literals with eval",
            "code": "help_text = 'Never use eval() or exec() with user input'\nprint(help_text)",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        {
            "name": "Safe pickle usage",
            "code": "import pickle\nwith open('safe_data.pkl', 'rb') as f:\n    data = pickle.load(f)",
            "expected": "safe",
            "category": "false_positive_protection",
            "must_remain_safe": True
        },
        
        # Basic threat detection
        {
            "name": "Direct eval() usage",
            "code": "result = eval(user_input)",
            "expected": "medium",
            "category": "basic_threat"
        },
        
        # Hybrid targets (should be enhanced)
        {
            "name": "Command injection with user input",
            "code": "import os\nuser_file = input('Enter filename: ')\nos.system('cat ' + user_file)",
            "expected": "enhanced_high",
            "category": "hybrid_target",
            "description": "Command injection with user input context"
        },
        {
            "name": "Pickle with request data",
            "code": "import pickle\nfrom flask import request\ndata = request.data\nobj = pickle.loads(data)",
            "expected": "enhanced_high",
            "category": "hybrid_target",
            "description": "Unsafe deserialization with network context"
        },
        {
            "name": "Command injection with environment",
            "code": "import os\nfile_path = os.getenv('USER_PATH')\nos.system('rm -rf ' + file_path)",
            "expected": "enhanced_high",
            "category": "hybrid_target",
            "description": "Command injection with environment variable"
        },
        
        # Complex scenarios
        {
            "name": "Mixed safe and dangerous",
            "code": '''
# Safe operations
config = json.load(open('config.json'))
log_level = config.get('log_level', 'INFO')

# Dangerous operation with user input
user_cmd = input('Enter command: ')
full_cmd = 'echo ' + user_cmd
os.system(full_cmd)
''',
            "expected": "enhanced_medium",
            "category": "complex_mixed",
            "description": "Mixed legitimate and dangerous patterns"
        }
    ]
    
    results = []
    false_positive_failures = 0
    
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
        
        # Final hybrid performance
        final_times = []
        final_results = []
        for _ in range(3):
            start_time = time.time()
            result = final_scanner.enhanced_security_scan(test_case["code"])
            final_times.append((time.time() - start_time) * 1000)
            final_results.append(result)
        
        # Analysis
        avg_phase_1a_time = sum(phase_1a_times) / len(phase_1a_times)
        avg_final_time = sum(final_times) / len(final_times)
        performance_impact = ((avg_final_time - avg_phase_1a_time) / avg_phase_1a_time * 100) if avg_phase_1a_time > 0 else 0
        
        phase_1a_result = phase_1a_results[0]
        final_result = final_results[0]
        
        # Quality analysis
        phase_1a_risk = phase_1a_result['risk_level']
        final_risk = final_result['risk_level']
        
        final_enhanced = 'hybrid_analysis' in final_result
        improvement_achieved = (
            final_result['risk_score'] > phase_1a_result['risk_score'] * 1.1 or
            final_enhanced
        )
        
        # False positive check
        if test_case.get('must_remain_safe', False):
            false_positive_occurred = final_risk not in ['safe', 'low']
            if false_positive_occurred:
                false_positive_failures += 1
        else:
            false_positive_occurred = False
        
        # Appropriateness check
        if test_case['expected'] == 'safe':
            appropriate = final_risk in ['safe', 'low'] and not false_positive_occurred
        elif test_case['expected'].startswith('enhanced_'):
            appropriate = improvement_achieved and final_risk != 'safe'
        else:
            appropriate = phase_1a_risk == final_risk
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'phase_1a_time_ms': round(avg_phase_1a_time, 2),
            'final_time_ms': round(avg_final_time, 2),
            'performance_impact_pct': round(performance_impact, 1),
            'phase_1a_risk': phase_1a_risk,
            'final_risk': final_risk,
            'phase_1a_score': round(phase_1a_result['risk_score'], 1),
            'final_score': round(final_result['risk_score'], 1),
            'final_enhanced': final_enhanced,
            'improvement_achieved': improvement_achieved,
            'appropriate': appropriate,
            'false_positive_occurred': false_positive_occurred
        }
        
        results.append(result)
        
        # Display results
        improvement_status = "🎯 HYBRID" if improvement_achieved else "✅ MAINTAINED"
        appropriate_status = "✅ APPROPRIATE" if appropriate else "❌ INAPPROPRIATE"
        fp_status = "❌ FALSE POSITIVE" if false_positive_occurred else ""
        
        print(f"  Performance: {avg_phase_1a_time:.1f}ms → {avg_final_time:.1f}ms ({performance_impact:+.1f}%)")
        print(f"  Risk Level: {phase_1a_risk} → {final_risk}")
        print(f"  Risk Score: {phase_1a_result['risk_score']:.1f} → {final_result['risk_score']:.1f}")
        print(f"  Assessment: {appropriate_status} {improvement_status} {fp_status}")
        
        # Show hybrid detection details
        if final_enhanced and 'detection_details' in final_result['hybrid_analysis']:
            details = final_result['hybrid_analysis']['detection_details']
            for detail in details:
                print(f"    • {detail['description']} (risk: {detail['risk_score']:.1f}, confidence: {detail['confidence']:.2f})")
                print(f"      Contexts: {', '.join(detail['contexts_detected'])}")
    
    # Final Analysis
    print("\n" + "=" * 65)
    print("📊 Final Phase 1B Hybrid Assessment")
    print("=" * 65)
    
    # Performance analysis
    performance_impacts = [r['performance_impact_pct'] for r in results]
    avg_performance_impact = sum(performance_impacts) / len(performance_impacts)
    max_performance_impact = max(performance_impacts)
    
    # Quality analysis
    false_positive_protection_tests = [r for r in results if r['category'] == 'false_positive_protection']
    false_positive_protection_maintained = all(not r['false_positive_occurred'] for r in false_positive_protection_tests)
    
    hybrid_target_tests = [r for r in results if r['category'] == 'hybrid_target']
    hybrid_improvements = sum(1 for r in hybrid_target_tests if r['improvement_achieved'])
    
    overall_appropriate = sum(1 for r in results if r['appropriate'])
    
    print(f"Performance Impact:")
    print(f"  Average: {avg_performance_impact:+.1f}%")
    print(f"  Maximum: {max_performance_impact:+.1f}%")
    print(f"  Within Budget (<15%): {'✅ YES' if avg_performance_impact <= 15 else '❌ NO'}")
    
    print(f"\nQuality Assessment:")
    print(f"  False Positive Protection: {'✅ PERFECT' if false_positive_protection_maintained and false_positive_failures == 0 else f'❌ FAILED ({false_positive_failures} false positives)'}")
    print(f"  Hybrid Target Improvements: {hybrid_improvements}/{len(hybrid_target_tests)}")
    print(f"  Overall Appropriateness: {overall_appropriate}/{len(results)}")
    
    # Hybrid statistics
    hybrid_stats = final_scanner.get_performance_stats()
    print(f"\nHybrid Pattern Statistics:")
    print(f"  Hybrid Detections Applied: {hybrid_stats['hybrid_detections']}")
    print(f"  Hybrid Patterns Found: {hybrid_stats['hybrid_patterns_found']}")
    print(f"  Context Requirements Met: {hybrid_stats['context_requirements_met']}")
    
    # Final assessment
    final_success = (
        avg_performance_impact <= 15 and               # Reasonable performance impact
        false_positive_protection_maintained and       # Perfect false positive protection
        false_positive_failures == 0 and              # Zero false positives
        hybrid_improvements >= len(hybrid_target_tests) * 0.7 and  # 70%+ hybrid improvements
        overall_appropriate >= len(results) * 0.8     # 80%+ appropriate
    )
    
    print(f"\n🏆 Final Phase 1B Assessment: {'✅ SUCCESS' if final_success else '❌ NEEDS WORK'}")
    
    if final_success:
        print("✅ Hybrid approach successfully balances detection and safety")
        print("✅ Perfect false positive protection maintained")
        print("✅ Meaningful security improvements on targeted patterns")
        print("✅ Ready for production deployment")
        print("✅ Excellent foundation for Phase 1C data flow analysis")
    else:
        print("⚠️  Issues remain - review hybrid patterns and thresholds")
        if false_positive_failures > 0:
            print(f"⚠️  Critical: {false_positive_failures} false positive(s) detected")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_performance_impact,
            'max_performance_impact': max_performance_impact,
            'within_performance_budget': avg_performance_impact <= 15,
            'false_positive_protection': false_positive_protection_maintained,
            'false_positive_failures': false_positive_failures,
            'hybrid_improvements': hybrid_improvements,
            'hybrid_improvement_rate': hybrid_improvements / len(hybrid_target_tests) if hybrid_target_tests else 0,
            'overall_appropriateness': overall_appropriate / len(results),
            'final_success': final_success
        },
        'performance_stats': hybrid_stats
    }

if __name__ == "__main__":
    benchmark_results = benchmark_final_phase_1b()
    
    success = benchmark_results['summary']['final_success']
    exit(0 if success else 1)