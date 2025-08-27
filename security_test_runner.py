#!/usr/bin/env python3
"""
Security Pattern Detection Test Runner
Tests Claude Guardian security pattern detection accuracy, performance, and coverage
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_guardian.core.security import SecurityManager, ThreatAnalysis
from claude_guardian.core.config import SecurityConfig
from claude_guardian.core.database import DatabaseManager
from security_test_samples import (
    sql_injection_samples,
    xss_samples,
    path_traversal_samples,
    command_injection_samples,
    insecure_secrets_samples,
    legitimate_code_samples,
    evasion_samples,
    performance_test_samples,
    real_world_samples
)

@dataclass
class TestResult:
    """Results from a security test"""
    test_name: str
    sample_type: str
    expected_detection: bool
    was_detected: bool
    threat_level: str
    confidence: float
    processing_time_ms: int
    findings_count: int
    false_positive: bool
    false_negative: bool

@dataclass
class TestSummary:
    """Summary of all test results"""
    total_tests: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_processing_time: float
    pattern_coverage: Dict[str, int]

class SecurityTestRunner:
    """Runs comprehensive security pattern detection tests"""
    
    def __init__(self):
        # Initialize with test configuration
        self.config = SecurityConfig(
            jwt_secret="test_secret_key_for_security_testing_only_very_long",
            jwt_algorithm="HS256",
            jwt_expiration=3600,
            bcrypt_rounds=12,
            max_login_attempts=5
        )
        
        # Mock database manager for testing
        self.db_manager = None
        self.security_manager = SecurityManager(self.config, self.db_manager)
        
        self.test_results: List[TestResult] = []
    
    async def run_all_tests(self) -> TestSummary:
        """Run all security pattern detection tests"""
        print("🔒 Starting Comprehensive Security Pattern Detection Tests")
        print("=" * 70)
        
        # Test categories with expected results
        test_categories = [
            ("SQL Injection", sql_injection_samples, True),
            ("XSS", xss_samples, True),
            ("Path Traversal", path_traversal_samples, True),
            ("Command Injection", command_injection_samples, True),
            ("Insecure Secrets", insecure_secrets_samples, True),
            ("Legitimate Code", legitimate_code_samples, False),
            ("Evasion Techniques", evasion_samples, True),
            ("Real World", real_world_samples, True)
        ]
        
        # Run tests for each category
        for category, samples, should_detect in test_categories:
            print(f"\n📊 Testing {category} Detection...")
            await self._test_category(category, samples, should_detect)
        
        # Run performance tests
        print(f"\n⚡ Running Performance Tests...")
        await self._test_performance()
        
        # Generate test summary
        summary = self._generate_summary()
        
        print(f"\n✅ All tests completed!")
        return summary
    
    async def _test_category(self, category: str, samples: Dict[str, str], should_detect: bool):
        """Test a category of security patterns"""
        for test_name, code_sample in samples.items():
            try:
                # Run security analysis
                start_time = time.time()
                analysis = await self.security_manager.analyze_code_security(code_sample)
                processing_time = int((time.time() - start_time) * 1000)
                
                # Determine if threat was detected
                was_detected = len(analysis.findings) > 0 and analysis.threat_level != "low"
                
                # Calculate false positives/negatives
                false_positive = was_detected and not should_detect
                false_negative = not was_detected and should_detect
                
                # Store result
                result = TestResult(
                    test_name=f"{category}_{test_name}",
                    sample_type=category,
                    expected_detection=should_detect,
                    was_detected=was_detected,
                    threat_level=analysis.threat_level,
                    confidence=analysis.confidence,
                    processing_time_ms=processing_time,
                    findings_count=len(analysis.findings),
                    false_positive=false_positive,
                    false_negative=false_negative
                )
                
                self.test_results.append(result)
                
                # Print result
                status = "✅" if (was_detected == should_detect) else "❌"
                print(f"  {status} {test_name}: {analysis.threat_level} ({analysis.confidence:.2f}) - {processing_time}ms")
                
                # Print findings for failed tests
                if false_positive or false_negative:
                    print(f"    Expected: {'Detection' if should_detect else 'No Detection'}")
                    print(f"    Got: {'Detection' if was_detected else 'No Detection'}")
                    if analysis.findings:
                        for finding in analysis.findings[:2]:  # Show first 2 findings
                            print(f"    Finding: {finding.get('type', 'unknown')} - {finding.get('description', 'N/A')}")
                
            except Exception as e:
                print(f"  ❌ {test_name}: ERROR - {str(e)}")
                # Still record the failed test
                self.test_results.append(TestResult(
                    test_name=f"{category}_{test_name}",
                    sample_type=category,
                    expected_detection=should_detect,
                    was_detected=False,
                    threat_level="error",
                    confidence=0.0,
                    processing_time_ms=0,
                    findings_count=0,
                    false_positive=False,
                    false_negative=should_detect
                ))
    
    async def _test_performance(self):
        """Test performance with large code samples"""
        print("\n⚡ Performance Benchmarking:")
        
        for test_name, code_sample in performance_test_samples.items():
            code_size = len(code_sample)
            print(f"\n  Testing {test_name} (Size: {code_size:,} characters)")
            
            # Run multiple iterations for average
            times = []
            for i in range(5):
                start_time = time.time()
                analysis = await self.security_manager.analyze_code_security(code_sample)
                processing_time = (time.time() - start_time) * 1000
                times.append(processing_time)
            
            avg_time = sum(times) / len(times)
            throughput = code_size / (avg_time / 1000)  # chars per second
            
            print(f"    Average time: {avg_time:.1f}ms")
            print(f"    Throughput: {throughput:,.0f} chars/sec")
            print(f"    Findings: {len(analysis.findings)}")
    
    def _generate_summary(self) -> TestSummary:
        """Generate comprehensive test summary"""
        if not self.test_results:
            return TestSummary(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, {})
        
        # Calculate metrics
        total = len(self.test_results)
        true_positives = sum(1 for r in self.test_results if r.expected_detection and r.was_detected)
        true_negatives = sum(1 for r in self.test_results if not r.expected_detection and not r.was_detected)
        false_positives = sum(1 for r in self.test_results if r.false_positive)
        false_negatives = sum(1 for r in self.test_results if r.false_negative)
        
        # Calculate performance metrics
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        avg_processing_time = sum(r.processing_time_ms for r in self.test_results) / total
        
        # Pattern coverage analysis
        pattern_coverage = {}
        for result in self.test_results:
            if result.sample_type not in pattern_coverage:
                pattern_coverage[result.sample_type] = 0
            if result.was_detected:
                pattern_coverage[result.sample_type] += 1
        
        return TestSummary(
            total_tests=total,
            true_positives=true_positives,
            true_negatives=true_negatives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            avg_processing_time=avg_processing_time,
            pattern_coverage=pattern_coverage
        )
    
    def print_detailed_report(self, summary: TestSummary):
        """Print comprehensive security testing report"""
        print("\n" + "="*70)
        print("🔒 CLAUDE GUARDIAN SECURITY TESTING REPORT")
        print("="*70)
        
        print(f"\n📊 DETECTION ACCURACY METRICS:")
        print(f"  Total Tests: {summary.total_tests}")
        print(f"  True Positives: {summary.true_positives}")
        print(f"  True Negatives: {summary.true_negatives}")
        print(f"  False Positives: {summary.false_positives}")
        print(f"  False Negatives: {summary.false_negatives}")
        print(f"  Accuracy: {summary.accuracy:.2%}")
        print(f"  Precision: {summary.precision:.2%}")
        print(f"  Recall: {summary.recall:.2%}")
        print(f"  F1-Score: {summary.f1_score:.2%}")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"  Average Processing Time: {summary.avg_processing_time:.1f}ms")
        
        print(f"\n🎯 PATTERN COVERAGE ANALYSIS:")
        for pattern_type, detections in summary.pattern_coverage.items():
            total_samples = len([r for r in self.test_results if r.sample_type == pattern_type])
            coverage_rate = (detections / total_samples) * 100 if total_samples > 0 else 0
            print(f"  {pattern_type}: {detections}/{total_samples} ({coverage_rate:.1f}%)")
        
        print(f"\n❌ FALSE POSITIVE ANALYSIS:")
        fp_results = [r for r in self.test_results if r.false_positive]
        if fp_results:
            for result in fp_results[:5]:  # Show first 5
                print(f"  - {result.test_name}: {result.threat_level} (confidence: {result.confidence:.2f})")
        else:
            print("  No false positives detected! ✅")
        
        print(f"\n❌ FALSE NEGATIVE ANALYSIS:")
        fn_results = [r for r in self.test_results if r.false_negative]
        if fn_results:
            for result in fn_results[:5]:  # Show first 5
                print(f"  - {result.test_name}: Missed detection")
        else:
            print("  No false negatives detected! ✅")
        
        print(f"\n💡 SECURITY PATTERN ANALYSIS:")
        security_manager = self.security_manager
        print(f"  Implemented Patterns:")
        for threat_type, patterns in security_manager.threat_patterns.items():
            print(f"    {threat_type}: {len(patterns)} patterns")
        
        print(f"\n🔍 OWASP TOP 10 COVERAGE:")
        owasp_coverage = {
            "A03 - Injection": "✅ SQL Injection, Command Injection detected",
            "A07 - Cross-Site Scripting": "✅ XSS patterns implemented", 
            "A01 - Broken Access Control": "⚠️  Path traversal partially covered",
            "A02 - Cryptographic Failures": "⚠️  Weak randomization detected",
            "A08 - Software Integrity": "❌ Not implemented",
            "A04 - Insecure Design": "❌ Not implemented",
            "A05 - Security Misconfiguration": "❌ Not implemented",
            "A06 - Vulnerable Components": "❌ Not implemented",
            "A09 - Security Logging": "❌ Not implemented", 
            "A10 - Server-Side Request Forgery": "❌ Not implemented"
        }
        
        for vuln, status in owasp_coverage.items():
            print(f"    {status}: {vuln}")
        
        print(f"\n📋 RECOMMENDATIONS:")
        if summary.false_positives > 0:
            print(f"  • Reduce false positives by refining pattern specificity")
        if summary.false_negatives > 0:
            print(f"  • Add more comprehensive patterns to catch missed threats")
        if summary.accuracy < 0.9:
            print(f"  • Improve overall accuracy through pattern optimization")
        
        print(f"  • Consider implementing additional OWASP Top 10 categories")
        print(f"  • Add context-aware analysis for better accuracy")
        print(f"  • Implement severity scoring based on context")
        print(f"  • Add support for more programming languages")
        
        print(f"\n✅ ASSESSMENT: {'EXCELLENT' if summary.accuracy > 0.95 else 'GOOD' if summary.accuracy > 0.85 else 'NEEDS IMPROVEMENT'}")
        print("="*70)

async def main():
    """Main test runner"""
    runner = SecurityTestRunner()
    summary = await runner.run_all_tests()
    runner.print_detailed_report(summary)
    
    # Save results to JSON file
    results_data = {
        "summary": {
            "total_tests": summary.total_tests,
            "accuracy": summary.accuracy,
            "precision": summary.precision,
            "recall": summary.recall,
            "f1_score": summary.f1_score,
            "avg_processing_time": summary.avg_processing_time,
            "pattern_coverage": summary.pattern_coverage
        },
        "detailed_results": [
            {
                "test_name": r.test_name,
                "sample_type": r.sample_type,
                "expected_detection": r.expected_detection,
                "was_detected": r.was_detected,
                "threat_level": r.threat_level,
                "confidence": r.confidence,
                "processing_time_ms": r.processing_time_ms,
                "findings_count": r.findings_count,
                "false_positive": r.false_positive,
                "false_negative": r.false_negative
            }
            for r in runner.test_results
        ]
    }
    
    with open('/Users/roble/Documents/Python/claude_guardian/security_test_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📄 Detailed results saved to security_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())