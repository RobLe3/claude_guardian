#!/usr/bin/env python3
"""
Phase 1A-Conservative: Ultra-Conservative AST Foundation
Only enhances detection when high-value patterns are detected with minimal performance impact
"""

import sys
import os
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner

@dataclass
class HighValuePattern:
    """High-value security pattern worth the performance cost"""
    regex: str
    risk_enhancement: float
    confidence: float
    description: str

class ConservativeEnhancementEngine:
    """Ultra-conservative enhancement engine - only acts on highest-value patterns"""
    
    def __init__(self):
        # Only the most critical patterns that justify performance cost
        self.high_value_patterns = [
            HighValuePattern(
                regex=r'(\w+)\s*=\s*(eval|exec)\s*[;\n]',  # Variable assignment to dangerous functions
                risk_enhancement=3.0,
                confidence=0.9,
                description="Indirect execution via variable assignment"
            ),
            HighValuePattern(
                regex=r'os\.system\s*\(\s*[\'"][^\'\"]*\'\s*\+\s*\w+',  # String concatenation in system calls
                risk_enhancement=4.0,
                confidence=0.85,
                description="Command injection via string concatenation"
            ),
            HighValuePattern(
                regex=r'(input\(|sys\.argv|request\.)\w*.*\s*(eval|exec|system)',  # User input to dangerous functions  
                risk_enhancement=5.0,
                confidence=0.95,
                description="Direct user input to dangerous function"
            ),
            HighValuePattern(
                regex=r'(eval|exec)\s*\(\s*[\'"].*\+.*[\'"]',  # Dynamic code construction
                risk_enhancement=3.5,
                confidence=0.8,
                description="Dynamic code construction pattern"
            )
        ]
        
        # Patterns that indicate safe context (never enhance these)
        self.safe_context_patterns = [
            r'#.*eval',                    # Comments
            r'[\'"].*eval.*[\'"]',         # String literals
            r'logger\.|print\(',           # Logging
            r'json\.loads?\s*\(',          # JSON operations
            r'ast\.literal_eval',          # Safe alternatives
        ]
    
    def should_enhance(self, code: str) -> bool:
        """Determine if code is worth enhancing based on quick pattern check"""
        # First, check if code is in safe context
        for safe_pattern in self.safe_context_patterns:
            if re.search(safe_pattern, code, re.IGNORECASE):
                return False
        
        # Check if any high-value patterns are present
        for pattern in self.high_value_patterns:
            if re.search(pattern.regex, code, re.IGNORECASE):
                return True
        
        return False
    
    def analyze_high_value_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Analyze only high-value patterns"""
        detected_patterns = []
        
        for pattern in self.high_value_patterns:
            matches = list(re.finditer(pattern.regex, code, re.IGNORECASE))
            for match in matches:
                detected_patterns.append({
                    'pattern_type': 'high_value_detection',
                    'description': pattern.description,
                    'risk_enhancement': pattern.risk_enhancement,
                    'confidence': pattern.confidence,
                    'matched_text': match.group(),
                    'line_number': code[:match.start()].count('\\n') + 1
                })
        
        return detected_patterns

class ConservativeEnhancedSecurityScanner(EnhancedSecurityScanner):
    """Ultra-conservative enhanced scanner - minimal performance impact, maximum safety"""
    
    def __init__(self):
        # ✅ PRESERVE existing initialization
        super().__init__()
        
        # ➕ ADD minimal enhancement engine
        self._enhancement_engine = ConservativeEnhancementEngine()
        
        # Performance tracking
        self._performance_stats = {
            'total_scans': 0,
            'enhancement_candidates': 0,
            'enhancements_applied': 0,
            'enhancements_skipped': 0
        }
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with ultra-conservative enhancements"""
        scan_start_time = time.time()
        self._performance_stats['total_scans'] += 1
        
        # ✅ ALWAYS run base analysis first (guaranteed to work)
        base_result = super().enhanced_security_scan(code, language, security_level)
        base_processing_time = (time.time() - scan_start_time) * 1000
        
        # ➕ ONLY enhance if high-value patterns detected and Python code
        if (language.lower() == "python" and 
            len(code) > 20 and len(code) < 2000 and  # Reasonable size limits
            base_processing_time < 1.0):  # Base scan was fast
            
            # Quick check: is enhancement worth it?
            if self._enhancement_engine.should_enhance(code):
                self._performance_stats['enhancement_candidates'] += 1
                
                try:
                    enhancement_start = time.time()
                    enhanced_result = self._apply_conservative_enhancement(code, base_result)
                    enhancement_time = (time.time() - enhancement_start) * 1000
                    
                    # Only apply if enhancement was very fast (<1ms)
                    if enhancement_time < 1.0:
                        self._performance_stats['enhancements_applied'] += 1
                        return enhanced_result
                    else:
                        self._performance_stats['enhancements_skipped'] += 1
                        
                except Exception:
                    # Enhancement failed, use base result
                    self._performance_stats['enhancements_skipped'] += 1
        
        # Always return base result if no enhancement applied
        return base_result
    
    def _apply_conservative_enhancement(self, code: str, base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ultra-conservative enhancements"""
        
        # Get high-value pattern detections
        detections = self._enhancement_engine.analyze_high_value_patterns(code)
        
        if not detections:
            return base_result
        
        # Calculate conservative risk enhancement
        enhanced_result = base_result.copy()
        total_risk_enhancement = 0.0
        
        for detection in detections:
            # Apply conservative risk enhancement
            risk_boost = detection['risk_enhancement'] * detection['confidence'] * 0.4  # Conservative multiplier
            total_risk_enhancement += risk_boost
        
        # Apply enhancement with caps
        max_enhancement = base_result['risk_score'] * 0.6  # Max 60% increase
        actual_enhancement = min(total_risk_enhancement, max_enhancement)
        
        enhanced_result.update({
            'risk_score': base_result['risk_score'] + actual_enhancement,
            'vulnerabilities': base_result['vulnerabilities'] + len(detections),
            'conservative_analysis': {
                'enabled': True,
                'high_value_patterns_detected': len(detections),
                'risk_enhancement_applied': actual_enhancement,
                'detection_details': [
                    {
                        'description': d['description'],
                        'confidence': d['confidence'],
                        'line': d['line_number']
                    } for d in detections
                ]
            }
        })
        
        # Update risk level if significantly enhanced
        if enhanced_result['risk_score'] > base_result['risk_score'] * 1.3:
            if enhanced_result['risk_score'] >= 12:
                enhanced_result['risk_level'] = 'high'
            elif enhanced_result['risk_score'] >= 6:
                enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self._performance_stats.copy()
        
        if stats['total_scans'] > 0:
            stats['enhancement_candidate_rate'] = stats['enhancement_candidates'] / stats['total_scans']
            stats['enhancement_success_rate'] = stats['enhancements_applied'] / stats['enhancement_candidates'] if stats['enhancement_candidates'] > 0 else 0
        
        return stats

# Comprehensive testing and benchmarking
def comprehensive_benchmark_phase_1a():
    """Comprehensive benchmark of Phase 1A conservative implementation"""
    print("🚀 Comprehensive Phase 1A Conservative Scanner Benchmark")
    print("=" * 65)
    
    baseline_scanner = EnhancedSecurityScanner()
    conservative_scanner = ConservativeEnhancedSecurityScanner()
    
    # Expanded test cases
    test_cases = [
        {
            "name": "JSON Processing (Safe)",
            "code": "import json; data = json.loads(user_input); print(data['name'])",
            "expected": "safe",
            "category": "false_positive_test"
        },
        {
            "name": "eval() in Comment (Safe)",
            "code": "# Never use eval() in production\\nresult = ast.literal_eval(data)",
            "expected": "safe",
            "category": "false_positive_test"
        },
        {
            "name": "String with eval() (Safe)",
            "code": "warning = 'Avoid eval() function for security'",
            "expected": "safe",
            "category": "false_positive_test"
        },
        {
            "name": "Direct eval() Usage",
            "code": "result = eval(user_input)",
            "expected": "medium",
            "category": "basic_threat"
        },
        {
            "name": "Indirect eval() Assignment",
            "code": "dangerous_func = eval\\nresult = dangerous_func(user_code)",
            "expected": "enhanced",
            "category": "advanced_threat"
        },
        {
            "name": "Command Injection Pattern",
            "code": "os.system('rm -rf ' + user_path)",
            "expected": "enhanced",
            "category": "advanced_threat"
        },
        {
            "name": "User Input to eval()",
            "code": "user_data = input('Code: ')\\nexec(user_data)",
            "expected": "enhanced",
            "category": "advanced_threat"
        },
        {
            "name": "Safe File Operations",
            "code": "with open('config.json', 'r') as f: config = json.load(f)",
            "expected": "safe",
            "category": "false_positive_test"
        },
        {
            "name": "Parameterized Query (Safe)",
            "code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            "expected": "safe",
            "category": "false_positive_test"
        },
        {
            "name": "Complex Mixed Code",
            "code": '''
# Configuration
config_path = os.getenv('CONFIG_PATH', 'default.json')

# Safe operations
def process_data(data):
    return json.loads(data)

# Potential risk - variable assignment  
risky_func = eval
result = risky_func('2 + 2')  # This should be detected
''',
            "expected": "enhanced",
            "category": "complex_mixed"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\nTesting: {test_case['name']}")
        
        # Baseline performance (5 runs for accuracy)
        baseline_times = []
        baseline_results = []
        for _ in range(5):
            start_time = time.time()
            result = baseline_scanner.enhanced_security_scan(test_case["code"])
            baseline_times.append((time.time() - start_time) * 1000)
            baseline_results.append(result)
        
        # Conservative scanner performance (5 runs)
        conservative_times = []
        conservative_results = []
        for _ in range(5):
            start_time = time.time()
            result = conservative_scanner.enhanced_security_scan(test_case["code"])
            conservative_times.append((time.time() - start_time) * 1000)
            conservative_results.append(result)
        
        # Analysis
        avg_baseline_time = sum(baseline_times) / len(baseline_times)
        avg_conservative_time = sum(conservative_times) / len(conservative_times)
        performance_impact = ((avg_conservative_time - avg_baseline_time) / avg_baseline_time * 100) if avg_baseline_time > 0 else 0
        
        baseline_result = baseline_results[0]
        conservative_result = conservative_results[0]
        
        # Quality analysis
        baseline_risk = baseline_result['risk_level']
        conservative_risk = conservative_result['risk_level']
        enhanced_analysis = 'conservative_analysis' in conservative_result
        
        # Check if enhancement was appropriate
        if test_case['expected'] == 'enhanced':
            enhancement_appropriate = (
                conservative_result['risk_score'] > baseline_result['risk_score'] or 
                enhanced_analysis
            )
        elif test_case['expected'] == 'safe':
            enhancement_appropriate = conservative_risk in ['safe', 'low']
        else:
            enhancement_appropriate = baseline_risk == conservative_risk
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'baseline_time_ms': round(avg_baseline_time, 3),
            'conservative_time_ms': round(avg_conservative_time, 3),
            'performance_impact_pct': round(performance_impact, 1),
            'baseline_risk': baseline_risk,
            'conservative_risk': conservative_risk,
            'baseline_score': round(baseline_result['risk_score'], 2),
            'conservative_score': round(conservative_result['risk_score'], 2),
            'enhanced_analysis': enhanced_analysis,
            'enhancement_appropriate': enhancement_appropriate,
            'quality_maintained': conservative_risk == baseline_risk or (baseline_risk == 'safe' and conservative_risk in ['safe', 'low'])
        }
        
        results.append(result)
        
        # Display result
        quality_status = "✅ APPROPRIATE" if enhancement_appropriate else "❌ INAPPROPRIATE"
        enhancement_status = "🚀 ENHANCED" if enhanced_analysis else "✅ MAINTAINED"
        
        print(f"  Performance: {avg_baseline_time:.2f}ms → {avg_conservative_time:.2f}ms ({performance_impact:+.1f}%)")
        print(f"  Risk Level: {baseline_risk} → {conservative_risk}")
        print(f"  Risk Score: {baseline_result['risk_score']:.1f} → {conservative_result['risk_score']:.1f}")
        print(f"  Quality: {quality_status} {enhancement_status}")
        
        if enhanced_analysis and 'detection_details' in conservative_result['conservative_analysis']:
            details = conservative_result['conservative_analysis']['detection_details']
            for detail in details[:2]:  # Show first 2 detections
                print(f"    • {detail['description']} (confidence: {detail['confidence']:.2f})")
    
    # Comprehensive Summary
    print("\\n" + "=" * 65)
    print("📊 Phase 1A Conservative Implementation Assessment")
    print("=" * 65)
    
    # Performance analysis
    performance_impacts = [r['performance_impact_pct'] for r in results]
    avg_performance_impact = sum(performance_impacts) / len(performance_impacts)
    max_performance_impact = max(performance_impacts)
    
    # Quality analysis
    quality_maintained_count = sum(1 for r in results if r['quality_maintained'])
    enhancement_appropriate_count = sum(1 for r in results if r['enhancement_appropriate'])
    enhanced_analysis_count = sum(1 for r in results if r['enhanced_analysis'])
    
    # False positive analysis
    false_positive_tests = [r for r in results if r['category'] == 'false_positive_test']
    false_positive_maintained = all(r['conservative_risk'] in ['safe', 'low'] for r in false_positive_tests)
    
    # Advanced threat detection analysis
    advanced_threat_tests = [r for r in results if r['category'] == 'advanced_threat']
    advanced_threat_improvements = sum(1 for r in advanced_threat_tests if r['enhanced_analysis'])
    
    print(f"Performance Analysis:")
    print(f"  Average Impact: {avg_performance_impact:+.1f}%")
    print(f"  Maximum Impact: {max_performance_impact:+.1f}%")
    print(f"  Within Budget (<20%): {'✅ YES' if avg_performance_impact <= 20 else '❌ NO'}")
    
    print(f"\\nQuality Analysis:")
    print(f"  Quality Maintained: {quality_maintained_count}/{len(results)} tests")
    print(f"  Enhancements Appropriate: {enhancement_appropriate_count}/{len(results)} tests")
    print(f"  False Positive Prevention: {'✅ MAINTAINED' if false_positive_maintained else '❌ BROKEN'}")
    print(f"  Advanced Threat Detection: {advanced_threat_improvements}/{len(advanced_threat_tests)} improved")
    
    # Get performance stats
    perf_stats = conservative_scanner.get_performance_stats()
    print(f"\\nEnhancement Statistics:")
    print(f"  Enhancement Candidates: {perf_stats['enhancement_candidates']}/{perf_stats['total_scans']}")
    print(f"  Successful Enhancements: {perf_stats['enhancements_applied']}")
    print(f"  Enhancement Success Rate: {perf_stats.get('enhancement_success_rate', 0):.1%}")
    
    # Final assessment
    phase_1a_success = (
        avg_performance_impact <= 20 and           # Within performance budget
        false_positive_maintained and              # No false positives introduced
        quality_maintained_count >= len(results) * 0.9 and  # 90%+ quality maintained
        advanced_threat_improvements >= 2          # At least 2 advanced threats improved
    )
    
    print(f"\\n🎯 Phase 1A Final Assessment: {'✅ SUCCESS' if phase_1a_success else '❌ NEEDS WORK'}")
    
    if phase_1a_success:
        print("✅ Ready to proceed to Phase 1B implementation")
        print("✅ Conservative enhancements working within performance budget")
        print("✅ False positive protection maintained")
        print("✅ Advanced threat detection capability demonstrated")
    else:
        print("⚠️  Address identified issues before proceeding to Phase 1B")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_performance_impact,
            'max_performance_impact': max_performance_impact,
            'within_performance_budget': avg_performance_impact <= 20,
            'quality_maintained_rate': quality_maintained_count / len(results),
            'false_positive_prevention': false_positive_maintained,
            'advanced_threat_improvements': advanced_threat_improvements,
            'phase_1a_success': phase_1a_success
        },
        'performance_stats': perf_stats
    }

if __name__ == "__main__":
    benchmark_results = comprehensive_benchmark_phase_1a()
    
    success = benchmark_results['summary']['phase_1a_success']
    exit(0 if success else 1)