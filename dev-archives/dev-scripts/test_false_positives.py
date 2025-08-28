#!/usr/bin/env python3
"""
False Positive Analysis for Claude Guardian
Tests legitimate code patterns that should NOT be flagged as threats
"""

import asyncio
import json
import logging
import requests
import websockets
import time
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FalsePositiveTester:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.mcp_url = "ws://localhost:8083"
    
    async def test_legitimate_code_patterns(self) -> Dict[str, Any]:
        """Test legitimate code that should NOT trigger security alerts"""
        logger.info("🔍 Testing legitimate code patterns for false positives...")
        
        legitimate_patterns = [
            {
                "name": "Safe JSON Processing",
                "code": "import json; data = json.loads(user_input); print(data['name'])",
                "category": "data_processing",
                "should_block": False,
                "description": "Using json.loads() is safe for parsing JSON"
            },
            {
                "name": "Template String Formatting", 
                "code": "message = f'Hello {username}, welcome to {app_name}'",
                "category": "string_formatting",
                "should_block": False,
                "description": "F-string formatting is safe when not executing code"
            },
            {
                "name": "Safe File Reading",
                "code": "with open('config.json', 'r') as f: config = json.load(f)",
                "category": "file_operations",
                "should_block": False,
                "description": "Reading configuration files is legitimate"
            },
            {
                "name": "Database Query with Parameters",
                "code": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                "category": "database",
                "should_block": False,
                "description": "Parameterized queries are safe SQL practice"
            },
            {
                "name": "Safe Subprocess with List Args",
                "code": "subprocess.run(['ls', '-la', '/home/user'], capture_output=True)",
                "category": "system_commands",
                "should_block": False,
                "description": "Subprocess with list args (no shell=True) is safer"
            },
            {
                "name": "Logging User Actions",
                "code": "logger.info('User %s performed action: %s', user_id, action_type)",
                "category": "logging",
                "should_block": False,
                "description": "Parameterized logging prevents injection"
            },
            {
                "name": "Safe Regular Expression",
                "code": "import re; pattern = re.compile(r'^[a-zA-Z0-9_]+$'); pattern.match(username)",
                "category": "validation",
                "should_block": False,
                "description": "Input validation with regex is legitimate security practice"
            },
            {
                "name": "Environment Variable Access",
                "code": "import os; database_url = os.getenv('DATABASE_URL', 'default_url')",
                "category": "configuration",
                "should_block": False,
                "description": "Reading environment variables is standard practice"
            },
            {
                "name": "Safe String Operations",
                "code": "cleaned_input = user_input.strip().lower().replace(' ', '_')",
                "category": "string_processing",
                "should_block": False,
                "description": "String cleaning operations are legitimate"
            },
            {
                "name": "Mathematical Calculations",
                "code": "result = (price * quantity * (1 + tax_rate)) - discount",
                "category": "calculations",
                "should_block": False,
                "description": "Arithmetic operations should never be flagged"
            }
        ]
        
        false_positive_results = []
        
        for pattern in legitimate_patterns:
            try:
                async with websockets.connect(self.mcp_url) as websocket:
                    # Initialize session
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {"name": "false-positive-tester", "version": "1.0.0"},
                            "capabilities": {}
                        }
                    }
                    
                    await websocket.send(json.dumps(init_msg))
                    await websocket.recv()
                    
                    # Test security scan
                    scan_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "security_scan_code",
                            "arguments": {
                                "code": pattern["code"],
                                "language": "python",
                                "security_level": "strict"
                            }
                        }
                    }
                    
                    await websocket.send(json.dumps(scan_msg))
                    response = await websocket.recv()
                    result = json.loads(response)
                    
                    if 'result' in result:
                        content = result['result']['content'][0]['text']
                        is_blocked = result['result'].get('isError', False)
                        
                        # Check if legitimate code was incorrectly flagged
                        threat_detected = any(keyword in content.upper() for keyword in 
                                           ['HIGH', 'CRITICAL', 'DANGEROUS', 'BLOCKED', 'RISK'])
                        
                        is_false_positive = threat_detected and not pattern["should_block"]
                        
                        false_positive_results.append({
                            "pattern": pattern["name"],
                            "category": pattern["category"],
                            "code": pattern["code"],
                            "should_block": pattern["should_block"],
                            "was_flagged": threat_detected,
                            "was_blocked": is_blocked,
                            "is_false_positive": is_false_positive,
                            "analysis_content": content,
                            "description": pattern["description"]
                        })
                        
                        status = "❌ FALSE POSITIVE" if is_false_positive else "✅ CORRECT"
                        logger.info(f"  {pattern['name']}: {status}")
                        
            except Exception as e:
                logger.error(f"❌ Error testing {pattern['name']}: {e}")
                false_positive_results.append({
                    "pattern": pattern["name"],
                    "error": str(e)
                })
        
        # Calculate false positive rate
        valid_tests = [r for r in false_positive_results if "error" not in r]
        false_positives = sum(1 for r in valid_tests if r.get("is_false_positive", False))
        false_positive_rate = (false_positives / len(valid_tests)) if valid_tests else 0
        
        return {
            "test_results": false_positive_results,
            "false_positive_count": false_positives,
            "total_legitimate_tests": len(valid_tests),
            "false_positive_rate": false_positive_rate,
            "accuracy": 1.0 - false_positive_rate
        }
    
    async def test_edge_case_scenarios(self) -> Dict[str, Any]:
        """Test edge cases that might cause false positives or missed detections"""
        logger.info("🎭 Testing edge case scenarios...")
        
        edge_cases = [
            {
                "name": "eval() in Comments",
                "code": "# This code mentions eval() but doesn't use it\nresult = calculate_value(x, y)",
                "expected": "safe",
                "description": "Comments mentioning dangerous functions should be safe"
            },
            {
                "name": "eval() in String Literal",
                "code": "help_text = 'Avoid using eval() function for security reasons'",
                "expected": "safe", 
                "description": "String literals mentioning eval() should be safe"
            },
            {
                "name": "SQL Keywords in Data",
                "code": "user_data = {'name': 'DROP TABLE', 'hobby': 'UNION SELECT'}",
                "expected": "safe",
                "description": "SQL keywords as data values should be safe"
            },
            {
                "name": "Path-like Strings in Config",
                "code": "config = {'backup_path': '../backups/', 'log_path': '../../logs/'}",
                "expected": "safe",
                "description": "Path strings in configuration should be safe"
            },
            {
                "name": "Legitimate Shell Command",
                "code": "subprocess.run(['python', '-c', 'print(\"Hello World\")'])",
                "expected": "moderate_risk",
                "description": "Should flag as moderate risk, not critical"
            },
            {
                "name": "Dynamic Import (Legitimate)",
                "code": "module_name = 'json'; module = importlib.import_module(module_name)",
                "expected": "moderate_risk",
                "description": "Dynamic imports should be flagged but not blocked"
            },
            {
                "name": "File Operations with User Input",
                "code": "filename = f'reports/{user_id}_{timestamp}.json'",
                "expected": "safe",
                "description": "Safe file naming with controlled input should be allowed"
            },
            {
                "name": "URL Construction",
                "code": "api_url = f'https://api.example.com/users/{user_id}/data'",
                "expected": "safe",
                "description": "URL construction with validated input should be safe"
            }
        ]
        
        edge_case_results = []
        
        for case in edge_cases:
            try:
                async with websockets.connect(self.mcp_url) as websocket:
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {"name": "edge-case-tester", "version": "1.0.0"},
                            "capabilities": {}
                        }
                    }
                    
                    await websocket.send(json.dumps(init_msg))
                    await websocket.recv()
                    
                    scan_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "security_scan_code",
                            "arguments": {
                                "code": case["code"],
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
                        
                        # Determine actual risk level detected
                        if "CRITICAL" in content:
                            detected_level = "critical"
                        elif "HIGH" in content:
                            detected_level = "high"
                        elif "MEDIUM" in content:
                            detected_level = "moderate_risk"
                        elif "LOW" in content:
                            detected_level = "low_risk"
                        else:
                            detected_level = "safe"
                        
                        expectation_met = (detected_level == case["expected"] or
                                         (case["expected"] == "safe" and detected_level in ["safe", "low_risk"]) or
                                         (case["expected"] == "moderate_risk" and detected_level in ["moderate_risk", "low_risk"]))
                        
                        edge_case_results.append({
                            "case": case["name"],
                            "expected_level": case["expected"],
                            "detected_level": detected_level,
                            "expectation_met": expectation_met,
                            "analysis": content,
                            "description": case["description"]
                        })
                        
                        status = "✅ CORRECT" if expectation_met else "⚠️ INCORRECT"
                        logger.info(f"  {case['name']}: {status} (Expected: {case['expected']}, Got: {detected_level})")
                        
            except Exception as e:
                logger.error(f"❌ Error testing edge case {case['name']}: {e}")
                edge_case_results.append({
                    "case": case["name"],
                    "error": str(e)
                })
        
        valid_tests = [r for r in edge_case_results if "error" not in r]
        correct_assessments = sum(1 for r in valid_tests if r.get("expectation_met", False))
        edge_case_accuracy = (correct_assessments / len(valid_tests)) if valid_tests else 0
        
        return {
            "edge_case_results": edge_case_results,
            "correct_assessments": correct_assessments,
            "total_edge_cases": len(valid_tests),
            "edge_case_accuracy": edge_case_accuracy
        }
    
    async def run_false_positive_analysis(self):
        """Run comprehensive false positive analysis"""
        logger.info("🚀 Starting False Positive Analysis Suite")
        logger.info("=" * 60)
        
        results = {}
        
        try:
            # Test 1: Legitimate Code Patterns
            logger.info("\n--- Test 1: Legitimate Code Patterns ---")
            results['legitimate_patterns'] = await self.test_legitimate_code_patterns()
            
            # Test 2: Edge Case Scenarios
            logger.info("\n--- Test 2: Edge Case Scenarios ---")
            results['edge_cases'] = await self.test_edge_case_scenarios()
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            results['error'] = str(e)
        
        # Generate summary
        logger.info("\n" + "=" * 60)
        logger.info("🎯 False Positive Analysis Results")
        logger.info("=" * 60)
        
        if 'legitimate_patterns' in results:
            fp_data = results['legitimate_patterns']
            logger.info(f"False Positive Rate: {fp_data['false_positive_rate']:.1%}")
            logger.info(f"Legitimate Code Accuracy: {fp_data['accuracy']:.1%}")
            logger.info(f"False Positives: {fp_data['false_positive_count']}/{fp_data['total_legitimate_tests']}")
        
        if 'edge_cases' in results:
            ec_data = results['edge_cases']
            logger.info(f"Edge Case Accuracy: {ec_data['edge_case_accuracy']:.1%}")
            logger.info(f"Correct Assessments: {ec_data['correct_assessments']}/{ec_data['total_edge_cases']}")
        
        return results

async def main():
    """Main test execution"""
    tester = FalsePositiveTester()
    results = await tester.run_false_positive_analysis()
    
    # Calculate overall quality metrics
    fp_accuracy = results.get('legitimate_patterns', {}).get('accuracy', 0)
    ec_accuracy = results.get('edge_cases', {}).get('edge_case_accuracy', 0)
    overall_accuracy = (fp_accuracy + ec_accuracy) / 2
    
    print(f"\n🏁 False Positive Analysis Completed")
    print(f"📊 Overall Accuracy: {overall_accuracy:.1%}")
    print(f"🎯 False Positive Rate: {1-fp_accuracy:.1%}")
    
    return overall_accuracy >= 0.95

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)