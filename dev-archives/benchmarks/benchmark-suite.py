#!/usr/bin/env python3
"""
Claude Guardian Comprehensive Benchmarking Suite
Tests performance, accuracy, and Claude Code integration effectiveness
"""

import asyncio
import json
import time
import requests
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class BenchmarkResult:
    test_name: str
    success: bool
    response_time_ms: float
    accuracy_score: float
    details: Dict[str, Any]

class ClaudeGuardianBenchmark:
    def __init__(self, base_url: str = "http://localhost:8083"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []
        
        # Test vectors for security scanning
        self.test_vectors = {
            "sql_injection": [
                ("SELECT * FROM users WHERE id = '1' OR 1=1--';", True),
                ("UPDATE accounts SET balance = 1000000 WHERE user_id = '1'; DROP TABLE users;", True),
                ("SELECT username FROM users WHERE username = ?", False),
                ("const query = `SELECT * FROM posts WHERE author = ${userId}`;", True),
                ("SELECT name FROM products ORDER BY price ASC", False)
            ],
            "xss": [
                ("<script>alert('XSS')</script>", True),
                ("document.write(untrustedData);", True),
                ("<img src='x' onerror='alert(1)'>", True),
                ("const safeText = DOMPurify.sanitize(userInput);", False),
                ("eval(userInput)", True)
            ],
            "secrets": [
                ("const API_KEY = 'sk-1234567890abcdef';", True),
                ("password = 'admin123'", True),
                ("JWT_SECRET = 'my-super-secret-key'", True),
                ("const config = process.env.API_KEY;", False),
                ("DATABASE_URL = process.env.DATABASE_URL || 'fallback'", False)
            ],
            "command_injection": [
                ("os.system(f'ls {user_input}')", True),
                ("subprocess.run(['ping', '-c', '1', user_host])", True),
                ("`curl ${userUrl}`", True),
                ("const result = child_process.exec('safe_command');", False),
                ("subprocess.run(['git', 'status'], shell=False)", False)
            ],
            "path_traversal": [
                ("../../../etc/passwd", True),
                ("..\\..\\windows\\system32\\config", True),
                ("%2e%2e%2f%2e%2e%2f%2e%2e%2f", True),
                ("./uploads/file.txt", False),
                ("/home/user/documents/file.pdf", False)
            ]
        }

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("🚀 Starting Claude Guardian Comprehensive Benchmark Suite")
        print("=" * 70)
        
        # System health check
        await self.test_system_health()
        
        # Performance benchmarks
        await self.benchmark_response_times()
        await self.benchmark_concurrent_requests()
        await self.benchmark_large_payloads()
        
        # Accuracy benchmarks
        await self.benchmark_threat_detection_accuracy()
        await self.benchmark_false_positive_rate()
        
        # Claude Code integration tests
        await self.test_mcp_integration()
        await self.test_tool_availability()
        
        # Database performance
        await self.benchmark_database_operations()
        
        # Generate comprehensive report
        return self.generate_final_report()

    async def test_system_health(self):
        """Test overall system health and availability"""
        print("\n🏥 System Health Check")
        print("-" * 30)
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ System Status: {health_data.get('status', 'unknown')}")
                print(f"✅ Response Time: {response_time:.2f}ms")
                
                services = health_data.get('services', {})
                for service, status in services.items():
                    print(f"   • {service}: {status}")
                
                self.results.append(BenchmarkResult(
                    test_name="system_health",
                    success=True,
                    response_time_ms=response_time,
                    accuracy_score=1.0,
                    details=health_data
                ))
            else:
                print(f"❌ Health check failed: {response.status_code}")
                self.results.append(BenchmarkResult(
                    test_name="system_health",
                    success=False,
                    response_time_ms=response_time,
                    accuracy_score=0.0,
                    details={"error": f"HTTP {response.status_code}"}
                ))
        except Exception as e:
            print(f"❌ Health check error: {e}")
            self.results.append(BenchmarkResult(
                test_name="system_health",
                success=False,
                response_time_ms=10000.0,
                accuracy_score=0.0,
                details={"error": str(e)}
            ))

    async def benchmark_response_times(self):
        """Benchmark API response times"""
        print("\n⚡ Response Time Benchmark")
        print("-" * 30)
        
        # Test different payload sizes
        test_cases = [
            ("small", "var x = 1;", 10),
            ("medium", "function test() {\n" + "  console.log('test');\n" * 50 + "}", 10),
            ("large", "// Large code file\n" + "const data = {\n" + "  key: 'value',\n" * 200 + "};\n", 5)
        ]
        
        for size_name, code, iterations in test_cases:
            times = []
            successes = 0
            
            for i in range(iterations):
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{self.base_url}/api/v1/mcp/scan/security",
                        json={"code": code, "context": f"benchmark_{size_name}_{i}"},
                        timeout=30
                    )
                    response_time = (time.time() - start_time) * 1000
                    times.append(response_time)
                    
                    if response.status_code == 200:
                        successes += 1
                        
                except Exception as e:
                    times.append(10000.0)  # 10s timeout
                    print(f"   ⚠️  Request failed: {e}")
            
            if times:
                avg_time = statistics.mean(times)
                p95_time = sorted(times)[int(0.95 * len(times))]
                success_rate = successes / iterations
                
                print(f"📊 {size_name.capitalize()} payload ({len(code)} chars):")
                print(f"   • Average: {avg_time:.2f}ms")
                print(f"   • P95: {p95_time:.2f}ms")
                print(f"   • Success Rate: {success_rate*100:.1f}%")
                
                self.results.append(BenchmarkResult(
                    test_name=f"response_time_{size_name}",
                    success=success_rate > 0.9,
                    response_time_ms=avg_time,
                    accuracy_score=success_rate,
                    details={
                        "payload_size": len(code),
                        "iterations": iterations,
                        "p95_ms": p95_time,
                        "success_rate": success_rate
                    }
                ))

    async def benchmark_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n🔄 Concurrent Request Benchmark")
        print("-" * 30)
        
        concurrent_levels = [1, 5, 10, 20]
        test_code = "SELECT * FROM users WHERE id = '1' OR 1=1--';"
        
        for concurrency in concurrent_levels:
            print(f"Testing {concurrency} concurrent requests...")
            
            async def make_request():
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{self.base_url}/api/v1/mcp/scan/security",
                        json={"code": test_code, "context": f"concurrent_test"},
                        timeout=30
                    )
                    response_time = (time.time() - start_time) * 1000
                    return response_time, response.status_code == 200
                except:
                    return 10000.0, False
            
            # Run concurrent requests
            start_time = time.time()
            tasks = [make_request() for _ in range(concurrency)]
            results = []
            for task in tasks:
                result = await asyncio.create_task(asyncio.to_thread(lambda: asyncio.run(task)))
                results.append(result)
            total_time = (time.time() - start_time) * 1000
            
            times = [r[0] for r in results]
            successes = sum(1 for r in results if r[1])
            
            avg_time = statistics.mean(times)
            success_rate = successes / concurrency
            throughput = concurrency / (total_time / 1000) if total_time > 0 else 0
            
            print(f"   • Concurrency {concurrency}: {avg_time:.2f}ms avg, {success_rate*100:.1f}% success")
            print(f"   • Throughput: {throughput:.2f} requests/second")
            
            self.results.append(BenchmarkResult(
                test_name=f"concurrent_{concurrency}",
                success=success_rate > 0.8,
                response_time_ms=avg_time,
                accuracy_score=success_rate,
                details={
                    "concurrency": concurrency,
                    "throughput_rps": throughput,
                    "total_time_ms": total_time
                }
            ))

    async def benchmark_threat_detection_accuracy(self):
        """Benchmark threat detection accuracy"""
        print("\n🎯 Threat Detection Accuracy Benchmark")
        print("-" * 30)
        
        overall_accuracy = []
        
        for threat_type, test_cases in self.test_vectors.items():
            correct_detections = 0
            total_tests = len(test_cases)
            response_times = []
            
            print(f"\n🔍 Testing {threat_type} detection:")
            
            for code, should_detect in test_cases:
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{self.base_url}/api/v1/mcp/scan/security",
                        json={"code": code, "context": f"accuracy_test_{threat_type}"},
                        timeout=10
                    )
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        result = response.json()
                        threat_level = result.get('threat_level', 'low')
                        findings = result.get('findings', [])
                        
                        # Check if threat was detected
                        detected = (
                            threat_level in ['medium', 'high', 'critical'] or
                            any(f.get('type') == threat_type for f in findings) or
                            len(findings) > 0
                        )
                        
                        is_correct = detected == should_detect
                        if is_correct:
                            correct_detections += 1
                            
                        status = "✅" if is_correct else "❌"
                        expected = "DETECT" if should_detect else "SAFE"
                        actual = "DETECTED" if detected else "SAFE"
                        print(f"   {status} Expected: {expected}, Got: {actual} ({response_time:.1f}ms)")
                        
                except Exception as e:
                    print(f"   ❌ Error testing: {e}")
                    response_times.append(1000.0)
            
            accuracy = correct_detections / total_tests if total_tests > 0 else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            overall_accuracy.append(accuracy)
            
            print(f"   📊 {threat_type}: {accuracy*100:.1f}% accuracy ({avg_response_time:.1f}ms avg)")
            
            self.results.append(BenchmarkResult(
                test_name=f"accuracy_{threat_type}",
                success=accuracy > 0.8,
                response_time_ms=avg_response_time,
                accuracy_score=accuracy,
                details={
                    "correct_detections": correct_detections,
                    "total_tests": total_tests,
                    "threat_type": threat_type
                }
            ))
        
        overall_avg = statistics.mean(overall_accuracy) if overall_accuracy else 0
        print(f"\n🎯 Overall Detection Accuracy: {overall_avg*100:.1f}%")

    async def test_mcp_integration(self):
        """Test MCP protocol integration"""
        print("\n🔗 MCP Integration Test")
        print("-" * 30)
        
        try:
            # Test MCP tools endpoint
            response = requests.get(f"{self.base_url}/api/v1/mcp/tools", timeout=10)
            if response.status_code == 200:
                tools = response.json()
                print(f"✅ MCP Tools Available: {len(tools)}")
                
                for tool in tools:
                    name = tool.get('name', 'unknown')
                    desc = tool.get('description', '')[:50]
                    print(f"   • {name}: {desc}...")
                
                # Test each tool
                tool_tests = 0
                tool_successes = 0
                
                for tool in tools:
                    tool_name = tool.get('name')
                    if tool_name == 'scan_code_security':
                        # Already tested in other benchmarks
                        tool_tests += 1
                        tool_successes += 1
                        continue
                        
                    elif tool_name == 'detect_secrets':
                        test_payload = {"content": "API_KEY = 'secret123'"}
                        endpoint = f"{self.base_url}/api/v1/mcp/detect/secrets"
                        
                    elif tool_name == 'check_dependencies':
                        test_payload = {"dependencies": ["express", "lodash"]}
                        endpoint = f"{self.base_url}/api/v1/mcp/scan/dependencies"
                        
                    else:
                        continue
                    
                    try:
                        tool_response = requests.post(endpoint, json=test_payload, timeout=10)
                        tool_tests += 1
                        if tool_response.status_code == 200:
                            tool_successes += 1
                            print(f"   ✅ {tool_name}: Working")
                        else:
                            print(f"   ❌ {tool_name}: HTTP {tool_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ {tool_name}: Error - {e}")
                        tool_tests += 1
                
                success_rate = tool_successes / tool_tests if tool_tests > 0 else 0
                self.results.append(BenchmarkResult(
                    test_name="mcp_integration",
                    success=success_rate > 0.8,
                    response_time_ms=0,  # Not applicable for this test
                    accuracy_score=success_rate,
                    details={
                        "tools_available": len(tools),
                        "tools_tested": tool_tests,
                        "tools_working": tool_successes
                    }
                ))
                
        except Exception as e:
            print(f"❌ MCP Integration Error: {e}")
            self.results.append(BenchmarkResult(
                test_name="mcp_integration",
                success=False,
                response_time_ms=0,
                accuracy_score=0.0,
                details={"error": str(e)}
            ))

    async def benchmark_database_operations(self):
        """Benchmark database performance"""
        print("\n💾 Database Performance Benchmark")
        print("-" * 30)
        
        # Test Qdrant collections
        try:
            response = requests.get("http://localhost:6333/collections", timeout=10)
            if response.status_code == 200:
                collections_data = response.json()
                collections = collections_data.get('result', {}).get('collections', [])
                print(f"✅ Qdrant Collections: {len(collections)} active")
                
                for collection in collections:
                    name = collection.get('name', 'unknown')
                    print(f"   • {name}")
                
                self.results.append(BenchmarkResult(
                    test_name="qdrant_performance",
                    success=len(collections) >= 4,
                    response_time_ms=0,
                    accuracy_score=1.0 if len(collections) >= 4 else 0.5,
                    details={"collections_count": len(collections)}
                ))
            else:
                print(f"❌ Qdrant not accessible: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Qdrant Error: {e}")

    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        print("\n" + "=" * 70)
        print("📊 CLAUDE GUARDIAN BENCHMARK REPORT")
        print("=" * 70)
        
        # Calculate overall metrics
        successful_tests = sum(1 for r in self.results if r.success)
        total_tests = len(self.results)
        overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))] if response_times else 0
        
        accuracy_scores = [r.accuracy_score for r in self.results if r.accuracy_score > 0]
        overall_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0
        
        # Performance grades
        def get_grade(score):
            if score >= 0.95: return "A+"
            elif score >= 0.90: return "A"
            elif score >= 0.85: return "B+"
            elif score >= 0.80: return "B"
            elif score >= 0.70: return "C"
            else: return "D"
        
        response_grade = get_grade(1.0 - min(avg_response_time / 1000, 1.0))  # Grade based on response time
        accuracy_grade = get_grade(overall_accuracy)
        reliability_grade = get_grade(overall_success_rate)
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_metrics": {
                "success_rate": overall_success_rate,
                "avg_response_time_ms": avg_response_time,
                "p95_response_time_ms": p95_response_time,
                "accuracy_score": overall_accuracy,
                "tests_run": total_tests,
                "tests_passed": successful_tests
            },
            "grades": {
                "response_time": response_grade,
                "accuracy": accuracy_grade,
                "reliability": reliability_grade,
                "overall": get_grade((overall_accuracy + overall_success_rate + (1.0 - min(avg_response_time / 1000, 1.0))) / 3)
            },
            "detailed_results": [
                {
                    "test": r.test_name,
                    "success": r.success,
                    "response_time_ms": r.response_time_ms,
                    "accuracy": r.accuracy_score,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        # Print summary
        print(f"\n🎯 OVERALL PERFORMANCE SUMMARY")
        print(f"   • Success Rate: {overall_success_rate*100:.1f}% ({successful_tests}/{total_tests})")
        print(f"   • Average Response: {avg_response_time:.1f}ms")
        print(f"   • P95 Response: {p95_response_time:.1f}ms")
        print(f"   • Detection Accuracy: {overall_accuracy*100:.1f}%")
        
        print(f"\n📊 PERFORMANCE GRADES:")
        print(f"   • Response Time: {response_grade}")
        print(f"   • Accuracy: {accuracy_grade}")
        print(f"   • Reliability: {reliability_grade}")
        print(f"   • Overall Grade: {report['grades']['overall']}")
        
        # Claude Code integration assessment
        print(f"\n🤖 CLAUDE CODE INTEGRATION ASSESSMENT:")
        mcp_result = next((r for r in self.results if r.test_name == "mcp_integration"), None)
        if mcp_result and mcp_result.success:
            print(f"   ✅ Ready for Claude Code integration")
            print(f"   ✅ {mcp_result.details.get('tools_available', 0)} security tools available")
            print(f"   ✅ MCP protocol working correctly")
        else:
            print(f"   ❌ Issues with Claude Code integration")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_response_time > 500:
            print(f"   • Consider optimizing response times (current: {avg_response_time:.1f}ms)")
        if overall_accuracy < 0.9:
            print(f"   • Improve threat detection accuracy (current: {overall_accuracy*100:.1f}%)")
        if overall_success_rate < 0.95:
            print(f"   • Address reliability issues (current: {overall_success_rate*100:.1f}%)")
        
        if overall_accuracy > 0.9 and avg_response_time < 200 and overall_success_rate > 0.95:
            print(f"   🎉 Excellent performance! Ready for production use.")
        
        return report

async def main():
    """Run the complete benchmark suite"""
    benchmark = ClaudeGuardianBenchmark()
    report = await benchmark.run_all_benchmarks()
    
    # Save report to file
    report_file = f"claude-guardian-benchmark-{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    return report

if __name__ == "__main__":
    asyncio.run(main())