#!/usr/bin/env python3
"""
Quick and Clean Re-benchmark Script
"""
import requests
import time
import json
import statistics

def benchmark_response_time(payload, iterations=8, test_name="test"):
    """Benchmark response times for a given payload"""
    times = []
    successes = 0
    
    for i in range(iterations):
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8083/api/v1/mcp/scan/security",
                json=payload,
                timeout=10
            )
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            times.append(response_time)
            
            if response.status_code == 200:
                successes += 1
                
        except Exception as e:
            times.append(1000.0)  # 1s penalty for failures
            
    avg_time = statistics.mean(times) if times else 0
    p95_time = sorted(times)[int(0.95 * len(times))] if times else 0
    success_rate = successes / iterations
    
    return {
        "test_name": test_name,
        "avg_time_ms": round(avg_time, 1),
        "p95_time_ms": round(p95_time, 1),
        "success_rate": success_rate,
        "iterations": iterations
    }

def test_threat_detection():
    """Test threat detection accuracy"""
    test_cases = [
        {
            "code": "SELECT * FROM users WHERE id = '1' OR 1=1--';",
            "expected": "high",
            "threat_type": "SQL Injection"
        },
        {
            "code": "<script>alert('xss')</script>",
            "expected": "high",
            "threat_type": "XSS"
        },
        {
            "code": "const API_KEY = 'sk-1234567890abcdef';",
            "expected": "high", 
            "threat_type": "Hardcoded Secret"
        },
        {
            "code": "const name = process.env.USER_NAME;",
            "expected": "low",
            "threat_type": "Clean Code"
        }
    ]
    
    results = []
    correct = 0
    total = len(test_cases)
    
    for case in test_cases:
        try:
            response = requests.post(
                "http://localhost:8083/api/v1/mcp/scan/security",
                json={"code": case["code"], "context": "accuracy_test"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                threat_level = data.get("threat_level", "unknown")
                confidence = data.get("confidence", 0)
                
                is_correct = threat_level == case["expected"]
                if is_correct:
                    correct += 1
                
                results.append({
                    "threat_type": case["threat_type"],
                    "expected": case["expected"],
                    "actual": threat_level,
                    "confidence": round(confidence, 2),
                    "correct": is_correct,
                    "status": "✅" if is_correct else "❌"
                })
            else:
                results.append({
                    "threat_type": case["threat_type"],
                    "expected": case["expected"],
                    "actual": f"HTTP {response.status_code}",
                    "confidence": 0,
                    "correct": False,
                    "status": "❌"
                })
                
        except Exception as e:
            results.append({
                "threat_type": case["threat_type"],
                "expected": case["expected"],
                "actual": f"Error: {e}",
                "confidence": 0,
                "correct": False,
                "status": "❌"
            })
    
    accuracy = correct / total if total > 0 else 0
    return results, accuracy

def main():
    print("🔄 CLAUDE GUARDIAN RE-BENCHMARK")
    print("=" * 50)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Health Check
    print("\n🏥 SYSTEM HEALTH CHECK:")
    try:
        start = time.time()
        health = requests.get("http://localhost:8083/health", timeout=10)
        health_time = (time.time() - start) * 1000
        
        if health.status_code == 200:
            health_data = health.json()
            print(f"   Status: {health_data.get('status', 'unknown')} ({health_time:.1f}ms)")
            services = health_data.get('services', {})
            for service, status in services.items():
                print(f"   • {service}: {status}")
        else:
            print(f"   ❌ Health check failed: HTTP {health.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Performance Benchmarks
    print("\n⚡ PERFORMANCE BENCHMARK:")
    
    # Small payload
    small_result = benchmark_response_time(
        {"code": "var x = 1;", "context": "rebench_small"},
        iterations=10,
        test_name="Small Payload"
    )
    print(f"   Small (10 chars): {small_result['avg_time_ms']}ms avg, P95: {small_result['p95_time_ms']}ms, Success: {small_result['success_rate']*100:.0f}%")
    
    # Medium payload
    medium_code = """function validateUser(input) {
    if (input && input.length > 0) {
        return input.toLowerCase();
    }
    return null;
}"""
    medium_result = benchmark_response_time(
        {"code": medium_code, "context": "rebench_medium"},
        iterations=8,
        test_name="Medium Payload"
    )
    print(f"   Medium ({len(medium_code)} chars): {medium_result['avg_time_ms']}ms avg, P95: {medium_result['p95_time_ms']}ms, Success: {medium_result['success_rate']*100:.0f}%")
    
    # Large payload
    large_code = "// Large test file\n" + "const data = { key: 'value' };\n" * 100
    large_result = benchmark_response_time(
        {"code": large_code, "context": "rebench_large"},
        iterations=5,
        test_name="Large Payload"
    )
    print(f"   Large ({len(large_code)} chars): {large_result['avg_time_ms']}ms avg, P95: {large_result['p95_time_ms']}ms, Success: {large_result['success_rate']*100:.0f}%")
    
    # Threat Detection Test
    print("\n🎯 THREAT DETECTION ACCURACY:")
    detection_results, accuracy = test_threat_detection()
    
    for result in detection_results:
        print(f"   {result['status']} {result['threat_type']}: Expected {result['expected']}, Got {result['actual']} (confidence: {result['confidence']})")
    
    print(f"\n   Overall Accuracy: {accuracy*100:.0f}% ({sum(1 for r in detection_results if r['correct'])}/{len(detection_results)} correct)")
    
    # MCP Integration Test
    print("\n🔗 MCP INTEGRATION:")
    try:
        tools_response = requests.get("http://localhost:8083/api/v1/mcp/tools", timeout=10)
        if tools_response.status_code == 200:
            tools = tools_response.json()
            print(f"   ✅ MCP Tools Available: {len(tools)}")
            for tool in tools[:3]:  # Show first 3
                print(f"      • {tool.get('name', 'unknown')}")
        else:
            print(f"   ❌ MCP Tools Error: HTTP {tools_response.status_code}")
    except Exception as e:
        print(f"   ❌ MCP Tools Error: {e}")
    
    # Database Status
    print("\n💾 DATABASE STATUS:")
    try:
        qdrant_response = requests.get("http://localhost:6333/collections", timeout=10)
        if qdrant_response.status_code == 200:
            collections = qdrant_response.json().get('result', {}).get('collections', [])
            print(f"   ✅ Qdrant Collections: {len(collections)} active")
        else:
            print(f"   ❌ Qdrant Error: HTTP {qdrant_response.status_code}")
    except Exception as e:
        print(f"   ❌ Qdrant Error: {e}")
    
    # Performance Grades
    print("\n📊 PERFORMANCE GRADES:")
    avg_response = statistics.mean([small_result['avg_time_ms'], medium_result['avg_time_ms'], large_result['avg_time_ms']])
    avg_success = statistics.mean([small_result['success_rate'], medium_result['success_rate'], large_result['success_rate']])
    
    def get_grade(score, is_time=False):
        if is_time:
            if score <= 10: return "A+"
            elif score <= 20: return "A"
            elif score <= 50: return "B+"
            elif score <= 100: return "B"
            else: return "C"
        else:
            if score >= 0.95: return "A+"
            elif score >= 0.90: return "A"
            elif score >= 0.85: return "B+"
            elif score >= 0.80: return "B"
            else: return "C"
    
    print(f"   • Response Time: {get_grade(avg_response, True)} ({avg_response:.1f}ms average)")
    print(f"   • Reliability: {get_grade(avg_success)} ({avg_success*100:.0f}% success rate)")
    print(f"   • Accuracy: {get_grade(accuracy)} ({accuracy*100:.0f}% detection accuracy)")
    
    overall_grade = get_grade((accuracy + avg_success + (1 - min(avg_response/100, 1))) / 3)
    print(f"   • Overall Grade: {overall_grade}")
    
    print("\n" + "=" * 50)
    print("🎯 RE-BENCHMARK COMPLETE")
    print(f"Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()