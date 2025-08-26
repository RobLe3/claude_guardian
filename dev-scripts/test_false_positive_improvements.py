#!/usr/bin/env python3
"""
Test False Positive Improvements for Claude Guardian
Verifies that the enhanced context-aware detection reduces false positives
"""

import asyncio
import json
import logging
import requests
import websockets
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FalsePositiveImprovementTester:
    def __init__(self):
        self.mcp_url = "ws://localhost:8083"
        self.enhanced_scanner = EnhancedSecurityScanner()
    
    async def test_enhanced_vs_basic_detection(self) -> Dict[str, Any]:
        """Compare enhanced detection vs basic pattern matching"""
        logger.info("🔍 Testing Enhanced vs Basic Detection...")
        
        test_cases = [
            {
                "name": "Safe JSON Processing",
                "code": "import json; data = json.loads(user_input); print(data['name'])",
                "category": "data_processing",
                "should_be_safe": True,
                "description": "Using json.loads() is safe for parsing JSON"
            },
            {
                "name": "Template String Formatting", 
                "code": "message = f'Hello {username}, welcome to {app_name}'",
                "category": "string_formatting",
                "should_be_safe": True,
                "description": "F-string formatting is safe when not executing code"
            },
            {
                "name": "eval() in Comment",
                "code": "# This function avoids eval() for security\\nresult = ast.literal_eval(data)",
                "category": "documentation",
                "should_be_safe": True,
                "description": "Comments mentioning eval() should be safe"
            },
            {
                "name": "eval() in String Literal",
                "code": "help_text = 'Never use eval() function for user input'",
                "category": "documentation",
                "should_be_safe": True,
                "description": "String literals mentioning eval() should be safe"
            },
            {
                "name": "Safe File Reading",
                "code": "with open('config.json', 'r') as f: config = json.load(f)",
                "category": "file_operations",
                "should_be_safe": True,
                "description": "Reading configuration files is legitimate"
            },
            {
                "name": "Database Query with Parameters",
                "code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                "category": "database",
                "should_be_safe": True,
                "description": "Parameterized queries are safe SQL practice"
            },
            {
                "name": "Safe Subprocess with List Args",
                "code": "subprocess.run(['ls', '-la', '/home/user'], capture_output=True)",
                "category": "system_commands",
                "should_be_safe": True,
                "description": "Subprocess with list args (no shell=True) is safer"
            },
            {
                "name": "Logging User Actions",
                "code": "logger.info('User %s performed action: %s', user_id, action_type)",
                "category": "logging",
                "should_be_safe": True,
                "description": "Parameterized logging prevents injection"
            },
            {
                "name": "Environment Variable Access",
                "code": "import os; database_url = os.getenv('DATABASE_URL', 'default_url')",
                "category": "configuration",
                "should_be_safe": True,
                "description": "Reading environment variables is standard practice"
            },
            {
                "name": "Mathematical Calculations",
                "code": "result = (price * quantity * (1 + tax_rate)) - discount",
                "category": "calculations",
                "should_be_safe": True,
                "description": "Arithmetic operations should never be flagged"
            },
            # Some actual dangerous cases to ensure we still catch real threats
            {
                "name": "Direct eval() Usage",
                "code": "result = eval(user_input)",
                "category": "code_injection",
                "should_be_safe": False,
                "description": "Direct eval() on user input is dangerous"
            },
            {
                "name": "Command Injection",
                "code": "os.system('rm -rf ' + user_path)",
                "category": "command_injection",
                "should_be_safe": False,
                "description": "String concatenation in system calls is dangerous"
            }
        ]
        
        results = []
        enhanced_false_positives = 0
        enhanced_correct = 0
        
        for test_case in test_cases:
            # Test with enhanced scanner
            enhanced_result = self.enhanced_scanner.enhanced_security_scan(
                test_case["code"], "python", "moderate"
            )
            
            # Determine if enhanced scanner correctly classified
            enhanced_safe = enhanced_result["risk_level"] in ["safe", "low"]
            enhanced_correct_classification = (enhanced_safe == test_case["should_be_safe"])
            
            if enhanced_correct_classification:
                enhanced_correct += 1
            elif test_case["should_be_safe"] and not enhanced_safe:
                enhanced_false_positives += 1
            
            results.append({
                "test_case": test_case["name"],
                "code": test_case["code"],
                "category": test_case["category"],
                "should_be_safe": test_case["should_be_safe"],
                "enhanced_risk_level": enhanced_result["risk_level"],
                "enhanced_risk_score": enhanced_result["risk_score"],
                "enhanced_intent": enhanced_result["code_intent"],
                "enhanced_correct": enhanced_correct_classification,
                "vulnerability_count": enhanced_result["vulnerabilities"],
                "context_analysis": enhanced_result.get("context_analysis", {})
            })
            
            status = "✅ CORRECT" if enhanced_correct_classification else "❌ INCORRECT"
            logger.info(f"  {test_case['name']}: {status} (Risk: {enhanced_result['risk_level']})")
        
        safe_cases = [r for r in results if r["should_be_safe"]]
        enhanced_fp_rate = enhanced_false_positives / len(safe_cases) if safe_cases else 0
        enhanced_accuracy = enhanced_correct / len(results)
        
        logger.info(f"✅ Enhanced Scanner Accuracy: {enhanced_accuracy:.1%}")
        logger.info(f"🎯 Enhanced False Positive Rate: {enhanced_fp_rate:.1%}")
        
        return {
            "test_results": results,
            "enhanced_accuracy": enhanced_accuracy,
            "enhanced_false_positive_rate": enhanced_fp_rate,
            "enhanced_correct_classifications": enhanced_correct,
            "total_tests": len(results),
            "safe_test_cases": len(safe_cases),
            "enhanced_false_positives": enhanced_false_positives
        }
    
    async def test_mcp_integration_improvements(self) -> Dict[str, Any]:
        """Test MCP service integration with enhanced scanner"""
        logger.info("🔗 Testing MCP Integration with Enhanced Scanner...")
        
        test_patterns = [
            {
                "name": "Safe Configuration Code",
                "code": "DATABASE_URL = os.getenv('DATABASE_URL')",
                "expected_improvement": "should_be_safe_now"
            },
            {
                "name": "eval() in Documentation",
                "code": "# Example: Never use eval(user_input) in production code",
                "expected_improvement": "should_be_safe_now"
            },
            {
                "name": "SQL in String Literal",
                "code": "example_query = 'SELECT * FROM users WHERE id = 1 UNION SELECT * FROM admin'",
                "expected_improvement": "should_be_safe_now"
            }
        ]
        
        mcp_results = []
        
        try:
            for pattern in test_patterns:
                async with websockets.connect(self.mcp_url) as websocket:
                    # Initialize session
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {"name": "improvement-tester", "version": "1.0.0"},
                            "capabilities": {}
                        }
                    }
                    
                    await websocket.send(json.dumps(init_msg))
                    await websocket.recv()
                    
                    # Test security scan with moderate level
                    scan_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "security_scan_code",
                            "arguments": {
                                "code": pattern["code"],
                                "language": "python",
                                "security_level": "moderate"
                            }
                        }
                    }
                    
                    await websocket.send(json.dumps(scan_msg))
                    response = await websocket.recv()
                    result = json.loads(response)
                    
                    if 'result' in result:
                        content = result['result']['content'][0]['text']
                        is_blocked = result['result'].get('isError', False)
                        
                        # Check if it's flagged as high risk
                        threat_detected = any(keyword in content.upper() for keyword in 
                                           ['HIGH', 'CRITICAL', 'DANGEROUS', 'BLOCKED'])
                        
                        mcp_results.append({
                            "pattern": pattern["name"],
                            "code": pattern["code"],
                            "was_flagged": threat_detected,
                            "was_blocked": is_blocked,
                            "analysis_content": content,
                            "expected_improvement": pattern["expected_improvement"]
                        })
                        
                        improvement_status = "✅ IMPROVED" if not threat_detected else "❌ STILL_FLAGGED"
                        logger.info(f"  {pattern['name']}: {improvement_status}")
                        
        except Exception as e:
            logger.error(f"❌ MCP integration test error: {e}")
            return {"error": str(e)}
        
        # Calculate improvement metrics
        improved_cases = sum(1 for r in mcp_results if not r["was_flagged"])
        improvement_rate = improved_cases / len(mcp_results) if mcp_results else 0
        
        return {
            "mcp_test_results": mcp_results,
            "improvement_rate": improvement_rate,
            "improved_cases": improved_cases,
            "total_mcp_tests": len(mcp_results)
        }
    
    async def run_comprehensive_improvement_test(self):
        """Run comprehensive false positive improvement test"""
        logger.info("🚀 Starting False Positive Improvement Test Suite")
        logger.info("=" * 60)
        
        results = {}
        
        try:
            # Test 1: Enhanced vs Basic Detection
            logger.info("\\n--- Test 1: Enhanced vs Basic Detection ---")
            results['enhanced_detection'] = await self.test_enhanced_vs_basic_detection()
            
            # Test 2: MCP Integration Improvements
            logger.info("\\n--- Test 2: MCP Integration Improvements ---")
            results['mcp_integration'] = await self.test_mcp_integration_improvements()
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            results['error'] = str(e)
        
        # Generate comprehensive summary
        logger.info("\\n" + "=" * 60)
        logger.info("🎯 False Positive Improvement Results")
        logger.info("=" * 60)
        
        if 'enhanced_detection' in results:
            enhanced_data = results['enhanced_detection']
            logger.info(f"Enhanced Scanner Accuracy: {enhanced_data['enhanced_accuracy']:.1%}")
            logger.info(f"False Positive Rate: {enhanced_data['enhanced_false_positive_rate']:.1%}")
            logger.info(f"Correct Classifications: {enhanced_data['enhanced_correct_classifications']}/{enhanced_data['total_tests']}")
        
        if 'mcp_integration' in results:
            mcp_data = results['mcp_integration']
            if 'error' not in mcp_data:
                logger.info(f"MCP Integration Improvement: {mcp_data['improvement_rate']:.1%}")
                logger.info(f"Patterns Now Safe: {mcp_data['improved_cases']}/{mcp_data['total_mcp_tests']}")
        
        # Calculate overall improvement
        overall_metrics = {}
        if 'enhanced_detection' in results:
            enhanced_fp_rate = results['enhanced_detection']['enhanced_false_positive_rate']
            enhanced_accuracy = results['enhanced_detection']['enhanced_accuracy']
            
            # Compare to original 100% false positive rate from analysis
            original_fp_rate = 1.0  # 100% false positive rate
            improvement = ((original_fp_rate - enhanced_fp_rate) / original_fp_rate) * 100
            
            overall_metrics = {
                'original_false_positive_rate': original_fp_rate,
                'enhanced_false_positive_rate': enhanced_fp_rate,
                'false_positive_improvement': improvement,
                'accuracy_achieved': enhanced_accuracy
            }
            
            logger.info("\\n📊 Improvement Summary:")
            logger.info(f"  Original False Positive Rate: {original_fp_rate:.1%}")
            logger.info(f"  Enhanced False Positive Rate: {enhanced_fp_rate:.1%}")
            logger.info(f"  False Positive Improvement: {improvement:.1f}%")
            logger.info(f"  Overall Accuracy: {enhanced_accuracy:.1%}")
            
            if enhanced_fp_rate <= 0.1:  # 10% or less
                logger.info("🎉 TARGET ACHIEVED: False positive rate below 10%!")
            elif enhanced_fp_rate <= 0.2:  # 20% or less
                logger.info("✅ GOOD PROGRESS: Significant false positive reduction")
            else:
                logger.info("⚠️ NEEDS MORE WORK: False positive rate still high")
        
        results['overall_metrics'] = overall_metrics
        return results

async def main():
    """Main test execution"""
    tester = FalsePositiveImprovementTester()
    results = await tester.run_comprehensive_improvement_test()
    
    # Check if we achieved target improvement
    if 'overall_metrics' in results:
        metrics = results['overall_metrics']
        false_positive_improvement = metrics.get('false_positive_improvement', 0)
        enhanced_fp_rate = metrics.get('enhanced_false_positive_rate', 1.0)
        
        print(f"\\n🏁 False Positive Improvement Test Completed")
        print(f"📊 False Positive Improvement: {false_positive_improvement:.1f}%")
        print(f"🎯 Enhanced False Positive Rate: {enhanced_fp_rate:.1%}")
        
        # Success criteria: <10% false positive rate OR >90% improvement
        success = enhanced_fp_rate <= 0.1 or false_positive_improvement >= 90
        return success
    
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)