#!/usr/bin/env python3
"""
API Integration Security Testing
Tests security scanning through MCP interface and bulk operations
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import os

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_guardian.core.security import SecurityManager, ThreatAnalysis
from claude_guardian.core.config import SecurityConfig

class APISecurityTester:
    """Tests API-based security operations"""
    
    def __init__(self):
        self.config = SecurityConfig(
            jwt_secret="test_secret_key_for_api_testing_very_long_secure",
            jwt_algorithm="HS256",
            jwt_expiration=3600,
            bcrypt_rounds=12,
            max_login_attempts=5
        )
        self.security_manager = SecurityManager(self.config, None)
        self.test_results = []
    
    async def test_bulk_scanning(self):
        """Test bulk scanning operations"""
        print("📦 Testing Bulk Scanning Operations")
        print("-" * 50)
        
        # Create test files with various threat levels
        test_files = {
            "safe_code.py": """
def safe_function(user_input):
    # Safely validate input
    if not user_input or len(user_input) > 100:
        return None
    return user_input.strip()
            """,
            
            "vulnerable_sql.php": """
$username = $_POST['username'];
$query = "SELECT * FROM users WHERE username = '$username'";
$result = mysql_query($query);
            """,
            
            "xss_vulnerability.js": """
function displayMessage(msg) {
    document.getElementById('output').innerHTML = msg;
    eval(userInput);
}
            """,
            
            "command_injection.py": """
import os
filename = request.args.get('file')
os.system('cat ' + filename)
            """,
            
            "hardcoded_secrets.js": """
const config = {
    api_key: 'sk-1234567890abcdefghijklmnop',
    database_password: 'admin123',
    secret_token: 'super_secret_auth_token_123'
};
            """
        }
        
        # Test bulk analysis
        results = []
        start_time = time.time()
        
        for filename, code in test_files.items():
            analysis = await self.security_manager.analyze_code_security(code, filename)
            results.append({
                'filename': filename,
                'threat_level': analysis.threat_level,
                'findings_count': len(analysis.findings),
                'confidence': analysis.confidence,
                'processing_time': analysis.processing_time_ms
            })
        
        total_time = (time.time() - start_time) * 1000
        total_code_size = sum(len(code) for code in test_files.values())
        
        print(f"Bulk Scan Results:")
        for result in results:
            threat_icon = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(result['threat_level'], "⚪")
            print(f"  {threat_icon} {result['filename']}: {result['threat_level']} ({result['findings_count']} findings)")
        
        print(f"\nBulk Performance:")
        print(f"  Total files: {len(test_files)}")
        print(f"  Total code size: {total_code_size:,} characters")
        print(f"  Total time: {total_time:.1f}ms")
        print(f"  Average per file: {total_time/len(test_files):.1f}ms")
        print(f"  Throughput: {total_code_size/(total_time/1000):,.0f} chars/sec")
        
        return results
    
    async def test_large_file_handling(self):
        """Test handling of large files"""
        print(f"\n🗂️  Testing Large File Handling")
        print("-" * 50)
        
        # Generate large file with mixed content
        large_code = """
def process_data(data):
    results = []
    for item in data:
        # This is safe processing
        processed = item.strip().lower()
        results.append(processed)
    return results

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def validate_input(self, input_data):
        if not input_data:
            return False
        return True
""" * 1000  # Repeat to create large file

        # Add some vulnerabilities in the large file
        large_code += """
# Hidden vulnerability in large file
password = 'admin123'
query = "SELECT * FROM users WHERE id = " + user_id
eval(user_input)
"""
        
        file_size = len(large_code)
        print(f"Testing file size: {file_size:,} characters")
        
        start_time = time.time()
        analysis = await self.security_manager.analyze_code_security(large_code)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"Large File Results:")
        print(f"  Processing time: {processing_time:.1f}ms")
        print(f"  Throughput: {file_size/(processing_time/1000):,.0f} chars/sec")
        print(f"  Threats found: {len(analysis.findings)}")
        print(f"  Threat level: {analysis.threat_level}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        
        return {
            'file_size': file_size,
            'processing_time': processing_time,
            'throughput': file_size / (processing_time / 1000),
            'findings': len(analysis.findings)
        }
    
    async def test_concurrent_scanning(self):
        """Test concurrent scanning operations"""
        print(f"\n🔄 Testing Concurrent Scanning")
        print("-" * 50)
        
        # Create multiple code samples for concurrent testing
        test_samples = [
            "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin",
            "<script>alert('XSS')</script>",
            "../../../etc/passwd",
            "; cat /etc/passwd",
            "api_key = 'sk-1234567890abcdef'",
            "password = 'admin123'",
            "eval(userInput)",
            "document.cookie",
            "import os; os.system(cmd)",
            "$query = 'SELECT * FROM users WHERE id = ' . $_GET['id']"
        ]
        
        # Test sequential processing
        print("Sequential processing:")
        start_time = time.time()
        sequential_results = []
        for i, sample in enumerate(test_samples):
            analysis = await self.security_manager.analyze_code_security(sample)
            sequential_results.append(analysis)
        sequential_time = (time.time() - start_time) * 1000
        
        # Test concurrent processing
        print("Concurrent processing:")
        start_time = time.time()
        concurrent_tasks = [
            self.security_manager.analyze_code_security(sample) 
            for sample in test_samples
        ]
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        concurrent_time = (time.time() - start_time) * 1000
        
        print(f"Results:")
        print(f"  Samples processed: {len(test_samples)}")
        print(f"  Sequential time: {sequential_time:.1f}ms")
        print(f"  Concurrent time: {concurrent_time:.1f}ms")
        print(f"  Speedup: {sequential_time/concurrent_time:.1f}x")
        print(f"  Threats detected: {sum(1 for r in concurrent_results if len(r.findings) > 0)}")
        
        return {
            'sequential_time': sequential_time,
            'concurrent_time': concurrent_time,
            'speedup': sequential_time / concurrent_time,
            'samples_count': len(test_samples)
        }
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print(f"\n⚠️  Testing Error Handling")
        print("-" * 50)
        
        error_cases = [
            ("empty_string", ""),
            ("very_long_string", "A" * 10000000),  # 10MB string
            ("null_bytes", "test\x00code"),
            ("unicode_chars", "test 🔒 unicode ñáéíóú"),
            ("mixed_encoding", "test\xff\xfe\x00code"),
            ("only_whitespace", "   \n\t   \n  "),
            ("special_regex_chars", ".*+?^${}()|[]\\"),
        ]
        
        results = []
        for test_name, test_input in error_cases:
            try:
                start_time = time.time()
                if test_name == "very_long_string":
                    print(f"  Testing {test_name}... (this may take a moment)")
                else:
                    print(f"  Testing {test_name}...")
                
                analysis = await self.security_manager.analyze_code_security(test_input)
                processing_time = (time.time() - start_time) * 1000
                
                results.append({
                    'test': test_name,
                    'status': 'success',
                    'processing_time': processing_time,
                    'findings': len(analysis.findings),
                    'threat_level': analysis.threat_level
                })
                
                print(f"    ✅ Success - {processing_time:.1f}ms, {analysis.threat_level} threat")
                
            except Exception as e:
                print(f"    ❌ Error - {str(e)}")
                results.append({
                    'test': test_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        success_rate = sum(1 for r in results if r.get('status') == 'success') / len(results)
        print(f"\nError Handling Summary:")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Failed cases: {sum(1 for r in results if r.get('status') == 'error')}")
        
        return results
    
    async def run_all_tests(self):
        """Run all API security tests"""
        print("🔒 CLAUDE GUARDIAN API SECURITY TESTING")
        print("=" * 70)
        
        # Run all test categories
        bulk_results = await self.test_bulk_scanning()
        large_file_results = await self.test_large_file_handling()
        concurrent_results = await self.test_concurrent_scanning()
        error_results = await self.test_error_handling()
        
        # Generate comprehensive report
        print(f"\n📊 API TESTING SUMMARY")
        print("=" * 70)
        
        print(f"✅ Bulk Scanning:")
        print(f"   • Files processed: {len(bulk_results)}")
        print(f"   • Threats detected: {sum(1 for r in bulk_results if r['threat_level'] != 'low')}")
        print(f"   • Average processing: {sum(r['processing_time'] for r in bulk_results)/len(bulk_results):.1f}ms")
        
        print(f"\n✅ Large File Handling:")
        print(f"   • File size: {large_file_results['file_size']:,} chars")
        print(f"   • Processing time: {large_file_results['processing_time']:.1f}ms")
        print(f"   • Throughput: {large_file_results['throughput']:,.0f} chars/sec")
        
        print(f"\n✅ Concurrent Processing:")
        print(f"   • Samples: {concurrent_results['samples_count']}")
        print(f"   • Speedup: {concurrent_results['speedup']:.1f}x")
        print(f"   • Concurrent time: {concurrent_results['concurrent_time']:.1f}ms")
        
        print(f"\n✅ Error Handling:")
        success_count = sum(1 for r in error_results if r.get('status') == 'success')
        print(f"   • Success rate: {success_count}/{len(error_results)} ({success_count/len(error_results):.1%})")
        print(f"   • Robustness: {'Excellent' if success_count/len(error_results) > 0.8 else 'Good' if success_count/len(error_results) > 0.6 else 'Needs Improvement'}")
        
        return {
            'bulk_results': bulk_results,
            'large_file_results': large_file_results,
            'concurrent_results': concurrent_results,
            'error_results': error_results
        }

async def main():
    """Main testing function"""
    tester = APISecurityTester()
    results = await tester.run_all_tests()
    
    # Save API test results
    with open('/Users/roble/Documents/Python/claude_guardian/api_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 API test results saved to api_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())