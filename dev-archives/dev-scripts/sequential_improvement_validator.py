#!/usr/bin/env python3
"""
Sequential Improvement Validator for Claude Guardian
Ensures each phase maintains existing functionality while adding new capabilities
"""

import asyncio
import json
import logging
import time
import sys
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner
from ast_foundation_enhancement import EnhancedSecurityScannerWithAST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Container for validation results"""
    phase: str
    test_name: str
    passed: bool
    details: Dict[str, Any]
    performance_impact: float
    compatibility_maintained: bool

class SequentialImprovementValidator:
    """Validates that improvements maintain existing functionality"""
    
    def __init__(self):
        self.baseline_scanner = EnhancedSecurityScanner()
        self.enhanced_scanner = EnhancedSecurityScannerWithAST()
        
        # Test cases that MUST maintain their current behavior
        self.critical_test_cases = [
            {
                "name": "Safe JSON Processing",
                "code": "import json; data = json.loads(user_input); print(data['name'])",
                "expected_risk": "safe",
                "must_not_flag": True,
                "category": "false_positive_prevention"
            },
            {
                "name": "eval() in Comment", 
                "code": "# This function avoids eval() for security\\nresult = ast.literal_eval(data)",
                "expected_risk": "safe",
                "must_not_flag": True,
                "category": "context_awareness"
            },
            {
                "name": "eval() in String Literal",
                "code": "help_text = 'Never use eval() function for user input'",
                "expected_risk": "safe", 
                "must_not_flag": True,
                "category": "context_awareness"
            },
            {
                "name": "Safe Configuration Code",
                "code": "DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite://memory')",
                "expected_risk": "safe",
                "must_not_flag": True,
                "category": "intent_classification"
            },
            {
                "name": "Parameterized Database Query",
                "code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                "expected_risk": "safe",
                "must_not_flag": True,
                "category": "safe_patterns"
            },
            {
                "name": "Direct eval() Usage",
                "code": "result = eval(user_input)",
                "expected_risk": "medium",
                "must_not_flag": False,  # This should be flagged
                "category": "threat_detection"
            },
            {
                "name": "Command Injection",
                "code": "os.system('rm -rf ' + user_path)",
                "expected_risk": "low",  # Current behavior (will improve in Phase 1B)
                "must_not_flag": False,  # This should be flagged
                "category": "threat_detection"
            }
        ]
        
        # Advanced test cases for improvement validation
        self.improvement_test_cases = [
            {
                "name": "Indirect eval() Assignment",
                "code": "func = eval\\nresult = func(user_input)",
                "category": "indirect_execution",
                "phase_target": "1B",
                "improvement_expected": True
            },
            {
                "name": "Variable Function Assignment",
                "code": "dangerous_func = exec\\ndangerous_func('malicious_code')",
                "category": "indirect_execution", 
                "phase_target": "1B",
                "improvement_expected": True
            },
            {
                "name": "Dynamic String Construction",
                "code": "command = 'rm -rf ' + user_input\\nos.system(command)",
                "category": "data_flow",
                "phase_target": "1C",
                "improvement_expected": True
            },
            {
                "name": "User Input to Dangerous Sink",
                "code": "user_data = input('Enter command: ')\\nexec(user_data)",
                "category": "data_flow",
                "phase_target": "1C", 
                "improvement_expected": True
            }
        ]
    
    def validate_backward_compatibility(self) -> List[ValidationResult]:
        """Ensure all existing functionality is preserved"""
        logger.info("🔍 Validating Backward Compatibility...")
        
        results = []
        
        for test_case in self.critical_test_cases:
            # Test with baseline scanner
            baseline_start = time.time()
            baseline_result = self.baseline_scanner.enhanced_security_scan(test_case["code"])
            baseline_time = (time.time() - baseline_start) * 1000
            
            # Test with enhanced scanner
            enhanced_start = time.time() 
            enhanced_result = self.enhanced_scanner.enhanced_security_scan(test_case["code"])
            enhanced_time = (time.time() - enhanced_start) * 1000
            
            # Validate compatibility
            api_compatible = all(key in enhanced_result for key in ['risk_level', 'risk_score', 'message'])
            risk_level_preserved = baseline_result['risk_level'] == enhanced_result['risk_level']
            
            # Validate false positive prevention
            if test_case["must_not_flag"]:
                false_positive_prevented = enhanced_result['risk_level'] in ['safe', 'low']
            else:
                false_positive_prevented = True  # Not applicable
            
            # Validate threat detection maintained  
            if not test_case["must_not_flag"]:  # If should be flagged
                threat_detected = enhanced_result['risk_level'] in ['medium', 'high', 'critical']
            else:
                threat_detected = True  # Not applicable for safe patterns
            
            passed = (api_compatible and risk_level_preserved and 
                     false_positive_prevented and threat_detected)
            
            performance_impact = ((enhanced_time - baseline_time) / baseline_time * 100 
                                if baseline_time > 0 else 0)
            
            results.append(ValidationResult(
                phase="1A",
                test_name=test_case["name"],
                passed=passed,
                details={
                    'baseline_risk': baseline_result['risk_level'],
                    'enhanced_risk': enhanced_result['risk_level'],
                    'baseline_score': baseline_result['risk_score'],
                    'enhanced_score': enhanced_result['risk_score'],
                    'api_compatible': api_compatible,
                    'risk_preserved': risk_level_preserved,
                    'false_positive_prevented': false_positive_prevented,
                    'threat_detected': threat_detected,
                    'has_ast_analysis': 'ast_analysis' in enhanced_result
                },
                performance_impact=performance_impact,
                compatibility_maintained=passed
            ))
            
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {test_case['name']}: {status} "
                       f"({baseline_result['risk_level']} → {enhanced_result['risk_level']})")
        
        return results
    
    def validate_improvement_capabilities(self) -> List[ValidationResult]:
        """Validate that improvements add new detection capabilities"""
        logger.info("🚀 Validating Improvement Capabilities...")
        
        results = []
        
        for test_case in self.improvement_test_cases:
            # Test with baseline (should miss these patterns)
            baseline_result = self.baseline_scanner.enhanced_security_scan(test_case["code"])
            
            # Test with enhanced (should detect more)
            enhanced_result = self.enhanced_scanner.enhanced_security_scan(test_case["code"])
            
            # Analyze improvement
            baseline_risk_score = baseline_result['risk_score']
            enhanced_risk_score = enhanced_result['risk_score']
            
            improvement_detected = enhanced_risk_score > baseline_risk_score
            ast_analysis_present = 'ast_analysis' in enhanced_result
            
            # For Phase 1A, we expect AST insights but not major risk score changes
            # (Major improvements come in 1B and 1C)
            phase_1a_success = ast_analysis_present and enhanced_risk_score >= baseline_risk_score
            
            results.append(ValidationResult(
                phase="1A_improvement",
                test_name=test_case["name"],
                passed=phase_1a_success,
                details={
                    'baseline_score': baseline_risk_score,
                    'enhanced_score': enhanced_risk_score,
                    'improvement_detected': improvement_detected,
                    'ast_analysis_present': ast_analysis_present,
                    'expected_phase': test_case["phase_target"],
                    'category': test_case["category"]
                },
                performance_impact=0,  # Will measure in performance tests
                compatibility_maintained=True
            ))
            
            status = "✅ FOUNDATION" if phase_1a_success else "⚠️ PENDING"
            logger.info(f"  {test_case['name']}: {status} "
                       f"(Score: {baseline_risk_score:.1f} → {enhanced_risk_score:.1f})")
        
        return results
    
    def validate_performance_impact(self) -> Dict[str, Any]:
        """Validate performance impact is acceptable"""
        logger.info("⚡ Validating Performance Impact...")
        
        # Performance test cases
        performance_tests = [
            {"name": "Small Code", "code": "import os\\nprint('test')", "size": "small"},
            {"name": "Medium Code", "code": "def test():\\n    pass\\n" * 25, "size": "medium"},
            {"name": "Large Code", "code": "def test():\\n    pass\\n" * 100, "size": "large"},
            {"name": "Complex Patterns", "code": "eval(exec(compile(user_input, '<string>', 'exec')))", "size": "complex"}
        ]
        
        performance_results = {}
        
        for test in performance_tests:
            # Baseline performance
            baseline_times = []
            for _ in range(5):  # Multiple runs for accuracy
                start_time = time.time()
                self.baseline_scanner.enhanced_security_scan(test["code"])
                baseline_times.append((time.time() - start_time) * 1000)
            
            # Enhanced performance
            enhanced_times = []
            for _ in range(5):
                start_time = time.time()
                self.enhanced_scanner.enhanced_security_scan(test["code"])
                enhanced_times.append((time.time() - start_time) * 1000)
            
            avg_baseline = sum(baseline_times) / len(baseline_times)
            avg_enhanced = sum(enhanced_times) / len(enhanced_times)
            impact_percent = ((avg_enhanced - avg_baseline) / avg_baseline * 100 
                            if avg_baseline > 0 else 0)
            
            performance_results[test["size"]] = {
                'baseline_avg_ms': round(avg_baseline, 3),
                'enhanced_avg_ms': round(avg_enhanced, 3),
                'impact_percent': round(impact_percent, 1),
                'acceptable': impact_percent < 50  # 50% is our threshold
            }
            
            logger.info(f"  {test['name']}: {avg_baseline:.2f}ms → {avg_enhanced:.2f}ms "
                       f"({impact_percent:+.1f}%)")
        
        overall_acceptable = all(result['acceptable'] for result in performance_results.values())
        
        return {
            'results': performance_results,
            'overall_acceptable': overall_acceptable,
            'max_impact_percent': max(r['impact_percent'] for r in performance_results.values())
        }
    
    def validate_error_handling(self) -> List[ValidationResult]:
        """Validate error handling and graceful degradation"""
        logger.info("🛡️ Validating Error Handling...")
        
        error_test_cases = [
            {"name": "Syntax Error", "code": "invalid syntax here ((", "should_not_crash": True},
            {"name": "Empty Code", "code": "", "should_not_crash": True},
            {"name": "Very Long Code", "code": "x = 1\\n" * 1000, "should_not_crash": True},
            {"name": "Unicode Characters", "code": "# 你好世界\\nprint('test')", "should_not_crash": True},
            {"name": "Mixed Languages", "code": "// This is JS\\nconsole.log('test');", "should_handle": True}
        ]
        
        results = []
        
        for test_case in error_test_cases:
            try:
                enhanced_result = self.enhanced_scanner.enhanced_security_scan(test_case["code"])
                
                # Validate result structure
                valid_result = (isinstance(enhanced_result, dict) and 
                              'risk_level' in enhanced_result and
                              'message' in enhanced_result)
                
                results.append(ValidationResult(
                    phase="1A_error_handling",
                    test_name=test_case["name"],
                    passed=valid_result,
                    details={
                        'no_crash': True,
                        'valid_result': valid_result,
                        'result_keys': list(enhanced_result.keys()) if valid_result else []
                    },
                    performance_impact=0,
                    compatibility_maintained=True
                ))
                
                status = "✅ HANDLED" if valid_result else "⚠️ PARTIAL"
                logger.info(f"  {test_case['name']}: {status}")
                
            except Exception as e:
                results.append(ValidationResult(
                    phase="1A_error_handling",
                    test_name=test_case["name"],
                    passed=False,
                    details={'error': str(e), 'crashed': True},
                    performance_impact=0,
                    compatibility_maintained=False
                ))
                
                logger.error(f"  {test_case['name']}: ❌ CRASHED - {e}")
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of sequential improvements"""
        logger.info("🚀 Starting Comprehensive Sequential Improvement Validation")
        logger.info("=" * 70)
        
        validation_results = {}
        
        # Phase 1A Validation
        logger.info("\\n--- Phase 1A: AST Foundation Validation ---")
        
        # Test 1: Backward Compatibility
        compatibility_results = self.validate_backward_compatibility()
        compatibility_passed = all(r.passed for r in compatibility_results)
        
        # Test 2: Improvement Capabilities 
        improvement_results = self.validate_improvement_capabilities()
        improvements_working = all(r.passed for r in improvement_results)
        
        # Test 3: Performance Impact
        performance_results = self.validate_performance_impact()
        performance_acceptable = performance_results['overall_acceptable']
        
        # Test 4: Error Handling
        error_handling_results = self.validate_error_handling()
        error_handling_robust = all(r.passed for r in error_handling_results)
        
        # Phase 1A Summary
        phase_1a_ready = (compatibility_passed and improvements_working and 
                         performance_acceptable and error_handling_robust)
        
        validation_results = {
            'phase_1a': {
                'ready_for_deployment': phase_1a_ready,
                'backward_compatibility': {
                    'passed': compatibility_passed,
                    'results': [vars(r) for r in compatibility_results]
                },
                'improvement_capabilities': {
                    'foundation_working': improvements_working,
                    'results': [vars(r) for r in improvement_results]
                },
                'performance_impact': performance_results,
                'error_handling': {
                    'robust': error_handling_robust,
                    'results': [vars(r) for r in error_handling_results]
                }
            }
        }
        
        # Summary Report
        logger.info("\\n" + "=" * 70)
        logger.info("🎯 Sequential Improvement Validation Results")
        logger.info("=" * 70)
        
        logger.info(f"Phase 1A AST Foundation: {'✅ READY' if phase_1a_ready else '❌ NOT READY'}")
        logger.info(f"  Backward Compatibility: {'✅ MAINTAINED' if compatibility_passed else '❌ BROKEN'}")
        logger.info(f"  Improvement Foundation: {'✅ WORKING' if improvements_working else '❌ ISSUES'}")
        logger.info(f"  Performance Impact: {'✅ ACCEPTABLE' if performance_acceptable else '❌ TOO HIGH'}")
        logger.info(f"  Error Handling: {'✅ ROBUST' if error_handling_robust else '❌ FRAGILE'}")
        
        if phase_1a_ready:
            logger.info("\\n🎉 Phase 1A is ready for implementation!")
            logger.info("   Safe to proceed with Phase 1B (Indirect Execution Detection)")
        else:
            logger.info("\\n⚠️  Phase 1A needs fixes before proceeding")
            logger.info("   Review failed tests and address issues")
        
        return validation_results

async def main():
    """Main validation execution"""
    validator = SequentialImprovementValidator()
    results = await asyncio.get_event_loop().run_in_executor(
        None, validator.run_comprehensive_validation
    )
    
    # Final assessment
    phase_1a_ready = results['phase_1a']['ready_for_deployment']
    
    print(f"\\n🏁 Sequential Improvement Validation Completed")
    print(f"🎯 Phase 1A Ready: {'YES' if phase_1a_ready else 'NO'}")
    
    if phase_1a_ready:
        print("✅ Safe to implement Phase 1A improvements")
        print("✅ Existing functionality preserved")
        print("✅ Foundation ready for Phase 1B/1C")
    
    return phase_1a_ready

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)