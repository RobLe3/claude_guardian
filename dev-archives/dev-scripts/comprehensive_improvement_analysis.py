#!/usr/bin/env python3
"""
Comprehensive Improvement Analysis for Claude Guardian
Analyzes current performance and identifies specific improvement opportunities
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
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImprovementOpportunity:
    """Represents a specific improvement opportunity"""
    category: str
    issue: str
    current_performance: float
    target_performance: float
    priority: str
    estimated_effort: str
    implementation_approach: str

class ComprehensiveImprovementAnalyzer:
    def __init__(self):
        self.mcp_url = "ws://localhost:8083"
        self.qdrant_url = "http://localhost:6333"
        self.enhanced_scanner = EnhancedSecurityScanner()
        self.improvement_opportunities = []
    
    async def analyze_detection_gaps(self) -> Dict[str, Any]:
        """Analyze detection accuracy gaps"""
        logger.info("🔍 Analyzing Detection Accuracy Gaps...")
        
        # Test cases that expose detection limitations
        challenging_cases = [
            {
                "name": "Complex Command Injection",
                "code": "os.system('rm -rf ' + user_path)",
                "expected": "high_risk",
                "category": "command_injection_complex"
            },
            {
                "name": "Indirect Eval Usage",
                "code": "func = eval; func(user_input)",
                "expected": "high_risk", 
                "category": "indirect_execution"
            },
            {
                "name": "Template Injection",
                "code": "template.render(**user_data)",
                "expected": "medium_risk",
                "category": "template_injection"
            },
            {
                "name": "Serialization Attack",
                "code": "pickle.loads(untrusted_data)",
                "expected": "high_risk",
                "category": "deserialization"
            },
            {
                "name": "Dynamic Import Risk",
                "code": "__import__(user_module_name)",
                "expected": "medium_risk",
                "category": "dynamic_import"
            },
            {
                "name": "File Path Construction",
                "code": "open(base_dir + '/' + user_file)",
                "expected": "medium_risk",
                "category": "path_construction"
            },
            {
                "name": "SQL Dynamic Construction",
                "code": "query = 'SELECT * FROM ' + table_name",
                "expected": "medium_risk",
                "category": "dynamic_sql"
            }
        ]
        
        detection_results = []
        missed_detections = 0
        incorrect_severity = 0
        
        for case in challenging_cases:
            result = self.enhanced_scanner.enhanced_security_scan(case["code"])
            
            # Determine if detection was correct
            detected_level = result["risk_level"]
            expected_level = case["expected"].replace("_risk", "")
            
            severity_mapping = {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
            detected_severity = severity_mapping.get(detected_level, 0)
            expected_severity = severity_mapping.get(expected_level, 0)
            
            # Analyze detection quality
            detection_accurate = abs(detected_severity - expected_severity) <= 1
            
            if not detection_accurate:
                if detected_severity < expected_severity:
                    missed_detections += 1
                else:
                    incorrect_severity += 1
            
            detection_results.append({
                "case": case["name"],
                "category": case["category"],
                "expected": expected_level,
                "detected": detected_level,
                "accurate": detection_accurate,
                "risk_score": result["risk_score"],
                "vulnerabilities": result["vulnerabilities"]
            })
            
            status = "✅ ACCURATE" if detection_accurate else "❌ INACCURATE"
            logger.info(f"  {case['name']}: {status} (Expected: {expected_level}, Got: {detected_level})")
        
        # Identify improvement opportunities
        accuracy_rate = (len(challenging_cases) - missed_detections - incorrect_severity) / len(challenging_cases)
        
        if missed_detections > 0:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="Detection Accuracy",
                issue=f"Missed {missed_detections} high-risk patterns",
                current_performance=accuracy_rate,
                target_performance=0.95,
                priority="high",
                estimated_effort="2-3 weeks",
                implementation_approach="Enhanced pattern matching with AST analysis"
            ))
        
        if accuracy_rate < 0.8:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="Overall Detection",
                issue="Detection accuracy below 80% on challenging cases",
                current_performance=accuracy_rate,
                target_performance=0.85,
                priority="medium",
                estimated_effort="3-4 weeks",
                implementation_approach="Machine learning model integration"
            ))
        
        return {
            "detection_results": detection_results,
            "accuracy_rate": accuracy_rate,
            "missed_detections": missed_detections,
            "incorrect_severity": incorrect_severity,
            "total_cases": len(challenging_cases)
        }
    
    async def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance bottlenecks"""
        logger.info("⚡ Analyzing Performance Bottlenecks...")
        
        # Test different code sizes and complexities
        performance_tests = [
            {"name": "Small Code (10 lines)", "code": "import os\n" * 10, "size": "small"},
            {"name": "Medium Code (100 lines)", "code": "import os\nprint('test')\n" * 50, "size": "medium"},
            {"name": "Large Code (1000+ lines)", "code": "def test():\n    pass\n" * 500, "size": "large"},
            {"name": "Complex Patterns", "code": "eval(exec(system(user_input)))", "size": "complex"}
        ]
        
        performance_results = []
        slow_operations = []
        
        for test in performance_tests:
            start_time = time.time()
            result = self.enhanced_scanner.enhanced_security_scan(test["code"])
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            performance_results.append({
                "test": test["name"],
                "size": test["size"],
                "processing_time_ms": round(processing_time, 2),
                "vulnerabilities_found": result["vulnerabilities"],
                "context_analysis": result.get("context_analysis", {})
            })
            
            # Identify slow operations
            if processing_time > 100:  # >100ms is concerning
                slow_operations.append({
                    "operation": test["name"],
                    "time_ms": processing_time,
                    "threshold_exceeded": "100ms"
                })
            
            logger.info(f"  {test['name']}: {processing_time:.2f}ms")
        
        # Performance improvement opportunities
        avg_time = sum(p["processing_time_ms"] for p in performance_results) / len(performance_results)
        
        if avg_time > 50:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="Performance",
                issue=f"Average processing time {avg_time:.1f}ms exceeds 50ms target",
                current_performance=avg_time,
                target_performance=25.0,
                priority="medium",
                estimated_effort="1-2 weeks",
                implementation_approach="Algorithm optimization and caching"
            ))
        
        if slow_operations:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="Performance",
                issue=f"{len(slow_operations)} operations exceed 100ms threshold",
                current_performance=len(slow_operations),
                target_performance=0.0,
                priority="low",
                estimated_effort="1 week",
                implementation_approach="Code parsing optimization"
            ))
        
        return {
            "performance_results": performance_results,
            "average_processing_time": avg_time,
            "slow_operations": slow_operations,
            "performance_target": 50.0
        }
    
    async def analyze_context_classification_gaps(self) -> Dict[str, Any]:
        """Analyze context classification accuracy"""
        logger.info("🎯 Analyzing Context Classification Gaps...")
        
        # Edge cases for context classification
        context_edge_cases = [
            {
                "name": "Multi-line Comment with eval()",
                "code": "# This is a multi-line comment\n# that mentions eval() function\n# but should be safe",
                "expected_context": "comment",
                "category": "complex_comment"
            },
            {
                "name": "String with Embedded Quotes",
                "code": "message = \"Don't use eval() or 'system()' functions\"",
                "expected_context": "string_literal", 
                "category": "complex_string"
            },
            {
                "name": "Docstring with Examples",
                "code": '"""\\nExample: eval(user_input)  # Never do this\\n"""',
                "expected_context": "documentation",
                "category": "docstring"
            },
            {
                "name": "Configuration Dictionary",
                "code": "config = {'dangerous_ops': ['eval', 'exec', 'system']}",
                "expected_context": "configuration",
                "category": "config_data"
            },
            {
                "name": "Test Assertion",
                "code": "assert_raises(SecurityError, eval, user_input)",
                "expected_context": "test_code",
                "category": "test_context"
            }
        ]
        
        classification_results = []
        misclassifications = 0
        
        for case in context_edge_cases:
            # This would require exposing context analysis from enhanced scanner
            # For now, we'll simulate by running security scan and checking results
            result = self.enhanced_scanner.enhanced_security_scan(case["code"])
            
            # If risk is very low, likely classified correctly as safe context
            correctly_classified = result["risk_score"] < 1.0
            
            if not correctly_classified:
                misclassifications += 1
            
            classification_results.append({
                "case": case["name"],
                "expected_context": case["expected_context"],
                "correctly_classified": correctly_classified,
                "risk_score": result["risk_score"],
                "category": case["category"]
            })
            
            status = "✅ CORRECT" if correctly_classified else "❌ INCORRECT"
            logger.info(f"  {case['name']}: {status}")
        
        classification_accuracy = (len(context_edge_cases) - misclassifications) / len(context_edge_cases)
        
        if classification_accuracy < 0.9:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="Context Classification",
                issue=f"Context classification accuracy {classification_accuracy:.1%} below 90%",
                current_performance=classification_accuracy,
                target_performance=0.95,
                priority="medium",
                estimated_effort="2-3 weeks", 
                implementation_approach="Enhanced AST parsing and NLP techniques"
            ))
        
        return {
            "classification_results": classification_results,
            "classification_accuracy": classification_accuracy,
            "misclassifications": misclassifications,
            "total_cases": len(context_edge_cases)
        }
    
    async def analyze_mcp_integration_issues(self) -> Dict[str, Any]:
        """Analyze MCP integration performance and issues"""
        logger.info("🔗 Analyzing MCP Integration Issues...")
        
        integration_issues = []
        response_times = []
        
        try:
            # Test multiple rapid connections
            connection_tests = []
            for i in range(3):
                start_time = time.time()
                async with websockets.connect(self.mcp_url) as websocket:
                    # Initialize session
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {"name": f"analyzer-{i}", "version": "1.0.0"},
                            "capabilities": {}
                        }
                    }
                    
                    await websocket.send(json.dumps(init_msg))
                    response = await websocket.recv()
                    end_time = time.time()
                    
                    connection_time = (end_time - start_time) * 1000
                    connection_tests.append(connection_time)
                    response_times.append(connection_time)
            
            avg_connection_time = sum(connection_tests) / len(connection_tests)
            logger.info(f"  Average MCP connection time: {avg_connection_time:.2f}ms")
            
            # Test tool response times
            async with websockets.connect(self.mcp_url) as websocket:
                init_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "clientInfo": {"name": "analyzer", "version": "1.0.0"},
                        "capabilities": {}
                    }
                }
                
                await websocket.send(json.dumps(init_msg))
                await websocket.recv()
                
                # Test security scan performance
                start_time = time.time()
                scan_msg = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "security_scan_code",
                        "arguments": {
                            "code": "eval(user_input)",
                            "language": "python",
                            "security_level": "moderate"
                        }
                    }
                }
                
                await websocket.send(json.dumps(scan_msg))
                response = await websocket.recv()
                end_time = time.time()
                
                tool_response_time = (end_time - start_time) * 1000
                response_times.append(tool_response_time)
                logger.info(f"  Security scan tool response time: {tool_response_time:.2f}ms")
            
        except Exception as e:
            integration_issues.append(f"MCP connection error: {e}")
            logger.error(f"❌ MCP integration issue: {e}")
        
        # Analyze response time performance
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        if avg_response_time > 200:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="MCP Integration",
                issue=f"Average response time {avg_response_time:.1f}ms exceeds 200ms",
                current_performance=avg_response_time,
                target_performance=100.0,
                priority="medium",
                estimated_effort="1-2 weeks",
                implementation_approach="Connection pooling and response caching"
            ))
        
        if integration_issues:
            self.improvement_opportunities.append(ImprovementOpportunity(
                category="MCP Integration",
                issue=f"{len(integration_issues)} integration stability issues",
                current_performance=len(integration_issues),
                target_performance=0.0,
                priority="high",
                estimated_effort="1 week",
                implementation_approach="Error handling and connection management"
            ))
        
        return {
            "response_times": response_times,
            "average_response_time": avg_response_time,
            "integration_issues": integration_issues,
            "stability_score": 1.0 - (len(integration_issues) / 10)  # Normalize to 0-1
        }
    
    async def analyze_scalability_limits(self) -> Dict[str, Any]:
        """Analyze system scalability limitations"""
        logger.info("📈 Analyzing Scalability Limitations...")
        
        # Test vector database capacity
        try:
            response = requests.get(f"{self.qdrant_url}/collections/security_procedures")
            if response.status_code == 200:
                collection_info = response.json()
                current_points = collection_info.get("result", {}).get("points_count", 0)
                vector_size = collection_info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size", 384)
                
                # Estimate memory usage and limits
                estimated_memory_mb = (current_points * vector_size * 4) / (1024 * 1024)  # 4 bytes per float
                
                logger.info(f"  Current vector points: {current_points}")
                logger.info(f"  Estimated memory usage: {estimated_memory_mb:.1f}MB")
                
                # Scalability concerns
                if current_points > 500:
                    self.improvement_opportunities.append(ImprovementOpportunity(
                        category="Scalability",
                        issue=f"Vector database approaching capacity limit ({current_points} points)",
                        current_performance=current_points,
                        target_performance=10000,
                        priority="medium",
                        estimated_effort="2-3 weeks",
                        implementation_approach="Database partitioning and indexing optimization"
                    ))
                
                scalability_results = {
                    "current_points": current_points,
                    "vector_dimensions": vector_size,
                    "estimated_memory_mb": estimated_memory_mb,
                    "capacity_utilization": current_points / 1000,  # Assume 1000 point soft limit
                    "scalability_concerns": current_points > 500
                }
                
            else:
                scalability_results = {"error": f"Cannot access vector database: {response.status_code}"}
                
        except Exception as e:
            scalability_results = {"error": f"Scalability analysis failed: {e}"}
        
        return scalability_results
    
    def prioritize_improvements(self) -> List[ImprovementOpportunity]:
        """Prioritize improvement opportunities"""
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        sorted_opportunities = sorted(
            self.improvement_opportunities,
            key=lambda x: (priority_order.get(x.priority, 0), x.target_performance - x.current_performance),
            reverse=True
        )
        
        return sorted_opportunities
    
    async def run_comprehensive_analysis(self):
        """Run comprehensive improvement analysis"""
        logger.info("🚀 Starting Comprehensive Improvement Analysis")
        logger.info("=" * 70)
        
        analysis_results = {}
        
        try:
            # Run all analyses
            logger.info("\\n--- Detection Gap Analysis ---")
            analysis_results['detection_gaps'] = await self.analyze_detection_gaps()
            
            logger.info("\\n--- Performance Analysis ---")
            analysis_results['performance'] = await self.analyze_performance_bottlenecks()
            
            logger.info("\\n--- Context Classification Analysis ---")
            analysis_results['context_classification'] = await self.analyze_context_classification_gaps()
            
            logger.info("\\n--- MCP Integration Analysis ---")
            analysis_results['mcp_integration'] = await self.analyze_mcp_integration_issues()
            
            logger.info("\\n--- Scalability Analysis ---")
            analysis_results['scalability'] = await self.analyze_scalability_limits()
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            analysis_results['error'] = str(e)
        
        # Generate prioritized improvement plan
        prioritized_opportunities = self.prioritize_improvements()
        
        # Summary
        logger.info("\\n" + "=" * 70)
        logger.info("🎯 Comprehensive Analysis Results")
        logger.info("=" * 70)
        
        if 'detection_gaps' in analysis_results:
            detection_data = analysis_results['detection_gaps']
            logger.info(f"Detection Accuracy on Challenging Cases: {detection_data['accuracy_rate']:.1%}")
            logger.info(f"Missed Detections: {detection_data['missed_detections']}/{detection_data['total_cases']}")
        
        if 'performance' in analysis_results:
            perf_data = analysis_results['performance']
            logger.info(f"Average Processing Time: {perf_data['average_processing_time']:.1f}ms")
            logger.info(f"Slow Operations: {len(perf_data['slow_operations'])}")
        
        if 'context_classification' in analysis_results:
            context_data = analysis_results['context_classification']
            logger.info(f"Context Classification Accuracy: {context_data['classification_accuracy']:.1%}")
        
        if 'mcp_integration' in analysis_results:
            mcp_data = analysis_results['mcp_integration']
            logger.info(f"MCP Response Time: {mcp_data['average_response_time']:.1f}ms")
            logger.info(f"Integration Issues: {len(mcp_data['integration_issues'])}")
        
        logger.info("\\n📋 Top Improvement Opportunities:")
        for i, opportunity in enumerate(prioritized_opportunities[:5], 1):
            logger.info(f"  {i}. {opportunity.category}: {opportunity.issue}")
            logger.info(f"     Priority: {opportunity.priority.upper()}, Effort: {opportunity.estimated_effort}")
            logger.info(f"     Approach: {opportunity.implementation_approach}")
        
        analysis_results['improvement_opportunities'] = [
            {
                'category': op.category,
                'issue': op.issue,
                'current_performance': op.current_performance,
                'target_performance': op.target_performance,
                'priority': op.priority,
                'estimated_effort': op.estimated_effort,
                'implementation_approach': op.implementation_approach
            } for op in prioritized_opportunities
        ]
        
        return analysis_results

async def main():
    """Main analysis execution"""
    analyzer = ComprehensiveImprovementAnalyzer()
    results = await analyzer.run_comprehensive_analysis()
    
    # Calculate overall improvement potential
    opportunities = results.get('improvement_opportunities', [])
    high_priority_count = sum(1 for op in opportunities if op['priority'] == 'high')
    total_opportunities = len(opportunities)
    
    print(f"\\n🏁 Comprehensive Analysis Completed")
    print(f"📊 Total Improvement Opportunities: {total_opportunities}")
    print(f"🔥 High Priority Items: {high_priority_count}")
    
    return total_opportunities > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)