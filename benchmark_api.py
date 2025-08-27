#!/usr/bin/env python3
"""
Claude Guardian API Performance Benchmark Script
Tests API endpoints with various payload sizes and concurrent loads
"""

import time
import json
import requests
import statistics
import concurrent.futures
import threading
import subprocess
import os
import psutil
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

class PerformanceBenchmark:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.results = {}
        
    def read_test_files(self):
        """Read test code files of different sizes"""
        test_files = {}
        
        files = {
            'small': 'test_code_small.py',
            'medium': 'test_code_medium.py', 
            'large': 'test_code_large.py'
        }
        
        for size, filename in files.items():
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                    test_files[size] = {
                        'content': content,
                        'size_kb': len(content) / 1024
                    }
                    print(f"Loaded {size} test file: {len(content)} bytes ({test_files[size]['size_kb']:.2f} KB)")
            except FileNotFoundError:
                print(f"Warning: {filename} not found, skipping {size} tests")
                
        return test_files
    
    def benchmark_endpoint(self, endpoint, method='GET', payload=None, iterations=10):
        """Benchmark a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        times = []
        errors = 0
        
        print(f"\nBenchmarking {method} {endpoint} ({iterations} iterations)...")
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                if method == 'GET':
                    response = requests.get(url, timeout=30)
                elif method == 'POST':
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    
                end_time = time.perf_counter()
                
                if response.status_code < 400:
                    times.append((end_time - start_time) * 1000)  # Convert to ms
                else:
                    errors += 1
                    print(f"  Error {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                errors += 1
                print(f"  Request error: {e}")
                end_time = time.perf_counter()
                
        if times:
            return {
                'avg_ms': statistics.mean(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'median_ms': statistics.median(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'success_rate': (len(times) / iterations) * 100,
                'errors': errors,
                'total_requests': iterations
            }
        else:
            return {
                'avg_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'median_ms': 0,
                'std_dev': 0,
                'success_rate': 0,
                'errors': errors,
                'total_requests': iterations
            }
    
    def benchmark_security_scanning(self, test_files):
        """Benchmark security scanning with different payload sizes"""
        security_results = {}
        
        for size, file_data in test_files.items():
            payload = {
                'code': file_data['content'],
                'context': f'Performance test - {size} payload',
                'scan_type': 'comprehensive'
            }
            
            print(f"\n{'='*50}")
            print(f"Testing security scanning with {size} payload ({file_data['size_kb']:.2f} KB)")
            
            # Single request timing
            start_time = time.perf_counter()
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/mcp/scan/security",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                end_time = time.perf_counter()
                
                if response.status_code == 200:
                    response_data = response.json()
                    processing_time = (end_time - start_time) * 1000
                    
                    security_results[size] = {
                        'payload_size_kb': file_data['size_kb'],
                        'response_time_ms': processing_time,
                        'threat_level': response_data.get('threat_level', 'unknown'),
                        'findings_count': len(response_data.get('findings', [])),
                        'confidence': response_data.get('confidence', 0),
                        'server_processing_time_ms': response_data.get('processing_time_ms', 0),
                        'status': 'success'
                    }
                    
                    print(f"  ✅ Success: {processing_time:.2f}ms total")
                    print(f"  🔍 Threat Level: {response_data.get('threat_level')}")
                    print(f"  📊 Findings: {len(response_data.get('findings', []))}")
                    print(f"  ⚡ Server Processing: {response_data.get('processing_time_ms', 0)}ms")
                else:
                    security_results[size] = {
                        'payload_size_kb': file_data['size_kb'],
                        'response_time_ms': 0,
                        'status': f'error_{response.status_code}',
                        'error_message': response.text[:200]
                    }
                    print(f"  ❌ Error {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                security_results[size] = {
                    'payload_size_kb': file_data['size_kb'],
                    'response_time_ms': 0,
                    'status': 'request_error',
                    'error_message': str(e)[:200]
                }
                print(f"  ❌ Request Error: {e}")
        
        return security_results
    
    def concurrent_load_test(self, endpoint, concurrent_requests=10, total_requests=100):
        """Test endpoint under concurrent load"""
        print(f"\n{'='*50}")
        print(f"Concurrent Load Test: {concurrent_requests} concurrent, {total_requests} total requests")
        
        def make_request():
            start_time = time.perf_counter()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                end_time = time.perf_counter()
                return {
                    'time_ms': (end_time - start_time) * 1000,
                    'status_code': response.status_code,
                    'success': response.status_code < 400
                }
            except Exception as e:
                end_time = time.perf_counter()
                return {
                    'time_ms': (end_time - start_time) * 1000,
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                }
        
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(total_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.perf_counter()
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['time_ms'] for r in successful_requests]
            
            return {
                'total_time_sec': end_time - start_time,
                'requests_per_sec': total_requests / (end_time - start_time),
                'success_rate': (len(successful_requests) / total_requests) * 100,
                'failed_requests': len(failed_requests),
                'avg_response_time_ms': statistics.mean(response_times),
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times),
                'median_response_time_ms': statistics.median(response_times),
                'p95_response_time_ms': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
            }
        else:
            return {
                'total_time_sec': end_time - start_time,
                'requests_per_sec': 0,
                'success_rate': 0,
                'failed_requests': len(failed_requests),
                'error': 'All requests failed'
            }
    
    def monitor_system_resources(self, duration_seconds=30):
        """Monitor system resources during testing"""
        print(f"\nMonitoring system resources for {duration_seconds} seconds...")
        
        measurements = []
        start_time = time.time()
        
        # Find the API server process
        api_process = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'claude_guardian.main' in ' '.join(proc.info['cmdline'] or []):
                    api_process = psutil.Process(proc.info['pid'])
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        while time.time() - start_time < duration_seconds:
            measurement = {
                'timestamp': time.time(),
                'system_cpu_percent': psutil.cpu_percent(interval=1),
                'system_memory_percent': psutil.virtual_memory().percent,
                'system_memory_used_mb': psutil.virtual_memory().used / (1024 * 1024)
            }
            
            if api_process and api_process.is_running():
                try:
                    measurement.update({
                        'api_cpu_percent': api_process.cpu_percent(),
                        'api_memory_mb': api_process.memory_info().rss / (1024 * 1024),
                        'api_threads': api_process.num_threads()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            measurements.append(measurement)
            time.sleep(1)
        
        # Calculate averages
        if measurements:
            return {
                'avg_system_cpu_percent': statistics.mean([m['system_cpu_percent'] for m in measurements]),
                'avg_system_memory_percent': statistics.mean([m['system_memory_percent'] for m in measurements]),
                'avg_api_cpu_percent': statistics.mean([m.get('api_cpu_percent', 0) for m in measurements]),
                'avg_api_memory_mb': statistics.mean([m.get('api_memory_mb', 0) for m in measurements]),
                'measurements': measurements
            }
        else:
            return {'error': 'No measurements collected'}
    
    def run_comprehensive_benchmark(self):
        """Run all benchmark tests"""
        print("🚀 Starting Claude Guardian API Performance Benchmark")
        print(f"📊 Target URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Test basic endpoints
        print(f"\n{'='*60}")
        print("BASIC ENDPOINT RESPONSE TIMES")
        print(f"{'='*60}")
        
        basic_endpoints = [
            ('/', 'GET'),
            ('/api/v1/mcp/tools', 'GET'),
            ('/health', 'GET')
        ]
        
        self.results['basic_endpoints'] = {}
        for endpoint, method in basic_endpoints:
            result = self.benchmark_endpoint(endpoint, method, iterations=20)
            self.results['basic_endpoints'][endpoint] = result
            print(f"  {method} {endpoint}: {result['avg_ms']:.2f}ms avg, {result['success_rate']:.1f}% success")
        
        # Test security scanning with different payload sizes
        print(f"\n{'='*60}")
        print("SECURITY SCANNING PERFORMANCE")
        print(f"{'='*60}")
        
        test_files = self.read_test_files()
        self.results['security_scanning'] = self.benchmark_security_scanning(test_files)
        
        # Concurrent load testing
        print(f"\n{'='*60}")
        print("CONCURRENT LOAD TESTING")
        print(f"{'='*60}")
        
        load_tests = [
            ('/api/v1/mcp/tools', 5, 50),   # 5 concurrent, 50 total
            ('/api/v1/mcp/tools', 10, 100), # 10 concurrent, 100 total
            ('/', 20, 200)                   # 20 concurrent, 200 total
        ]
        
        self.results['load_tests'] = {}
        for endpoint, concurrent, total in load_tests:
            result = self.concurrent_load_test(endpoint, concurrent, total)
            self.results['load_tests'][f"{endpoint}_{concurrent}c_{total}t"] = result
            if 'error' not in result:
                print(f"  {endpoint} ({concurrent}c/{total}t): {result['requests_per_sec']:.1f} req/s, {result['avg_response_time_ms']:.2f}ms avg")
            else:
                print(f"  {endpoint} ({concurrent}c/{total}t): FAILED - {result.get('error', 'Unknown error')}")
        
        # System resource monitoring
        print(f"\n{'='*60}")
        print("SYSTEM RESOURCE MONITORING")
        print(f"{'='*60}")
        
        self.results['system_resources'] = self.monitor_system_resources(30)
        resource_data = self.results['system_resources']
        if 'error' not in resource_data:
            print(f"  Avg System CPU: {resource_data['avg_system_cpu_percent']:.1f}%")
            print(f"  Avg System Memory: {resource_data['avg_system_memory_percent']:.1f}%")
            print(f"  Avg API CPU: {resource_data['avg_api_cpu_percent']:.1f}%")
            print(f"  Avg API Memory: {resource_data['avg_api_memory_mb']:.1f} MB")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_performance_benchmark_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✅ Benchmark completed! Results saved to: {results_file}")
        return self.results

if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    benchmark.run_comprehensive_benchmark()