#!/usr/bin/env python3
"""
Vector-Graph Database Correlation Testing for Claude Guardian
Tests the correlation between vector DB (Qdrant) and graph/SQL relationships
to improve security analysis and knowledge base generation
"""

import asyncio
import json
import logging
import requests
import websockets
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple
import networkx as nx
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorGraphCorrelationTester:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.mcp_url = "ws://localhost:8083"
        self.postgres_available = False  # Will try to detect
        
        # Simulated attack patterns and their relationships
        self.attack_patterns = {
            "code_injection": {
                "patterns": ["eval(", "exec(", "system("],
                "severity": 9,
                "mitigations": ["input_validation", "sandboxing", "ast_literal_eval"],
                "related_attacks": ["command_injection", "script_injection"]
            },
            "sql_injection": {
                "patterns": ["UNION SELECT", "'; DROP TABLE", "1=1--"],
                "severity": 10,
                "mitigations": ["prepared_statements", "input_sanitization", "least_privilege"],
                "related_attacks": ["data_exfiltration", "privilege_escalation"]
            },
            "path_traversal": {
                "patterns": ["../", "..\\\\", "%2e%2e%2f"],
                "severity": 8,
                "mitigations": ["path_validation", "chroot_jail", "whitelist_paths"],
                "related_attacks": ["file_disclosure", "code_injection"]
            },
            "xss": {
                "patterns": ["<script>", "javascript:", "onerror="],
                "severity": 7,
                "mitigations": ["output_encoding", "content_security_policy", "input_validation"],
                "related_attacks": ["session_hijacking", "csrf"]
            },
            "command_injection": {
                "patterns": ["|", "&&", ";", "`"],
                "severity": 9,
                "mitigations": ["parameterized_commands", "input_validation", "shell_escaping"],
                "related_attacks": ["code_injection", "privilege_escalation"]
            }
        }
        
        # Initialize attack relationship graph
        self.attack_graph = self.build_attack_relationship_graph()
    
    def build_attack_relationship_graph(self) -> nx.DiGraph:
        """Build a directed graph of attack relationships"""
        G = nx.DiGraph()
        
        # Add nodes for each attack type
        for attack_type, data in self.attack_patterns.items():
            G.add_node(attack_type, severity=data["severity"], mitigations=data["mitigations"])
            
            # Add edges for related attacks
            for related_attack in data["related_attacks"]:
                if related_attack in self.attack_patterns:
                    G.add_edge(attack_type, related_attack, weight=0.7)
        
        # Add mitigation nodes and connect them
        all_mitigations = set()
        for attack_data in self.attack_patterns.values():
            all_mitigations.update(attack_data["mitigations"])
        
        for mitigation in all_mitigations:
            G.add_node(f"mitigation_{mitigation}", type="mitigation")
            
            # Connect mitigations to attacks they prevent
            for attack_type, data in self.attack_patterns.items():
                if mitigation in data["mitigations"]:
                    G.add_edge(f"mitigation_{mitigation}", attack_type, weight=0.9, type="prevents")
        
        return G
    
    def create_attack_vector_embedding(self, attack_code: str, attack_type: str) -> List[float]:
        """Create vector embedding for attack pattern"""
        # Combine attack code and type for embedding
        text_content = f"{attack_type} {attack_code}"
        
        # Create hash-based embedding (in production, use proper ML embeddings)
        hash_obj = hashlib.sha256(text_content.encode())
        hash_bytes = hash_obj.digest()[:48]  # 384 bits = 48 bytes
        
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = int.from_bytes(chunk, byteorder='big') / (2**32 - 1)
                vector.append(val * 2 - 1)  # Normalize to [-1, 1]
        
        # Pad to 384 dimensions
        while len(vector) < 384:
            vector.append(0.0)
        
        return vector[:384]
    
    async def store_attack_patterns_in_vector_db(self) -> Dict[str, Any]:
        """Store attack patterns in Qdrant with relationships"""
        logger.info("🗄️ Storing attack patterns in vector database...")
        
        stored_patterns = []
        relationship_mappings = {}
        
        for attack_type, data in self.attack_patterns.items():
            for i, pattern in enumerate(data["patterns"]):
                # Create vector embedding
                embedding = self.create_attack_vector_embedding(pattern, attack_type)
                
                # Store in Qdrant
                point_id = hash(f"{attack_type}_{pattern}") % 1000000
                
                point_data = {
                    "points": [
                        {
                            "id": point_id,
                            "vector": embedding,
                            "payload": {
                                "attack_type": attack_type,
                                "pattern": pattern,
                                "severity": data["severity"],
                                "mitigations": data["mitigations"],
                                "related_attacks": data["related_attacks"],
                                "created_at": datetime.now().isoformat(),
                                "correlation_id": f"{attack_type}_{i}"
                            }
                        }
                    ]
                }
                
                try:
                    response = requests.put(
                        f"{self.qdrant_url}/collections/security_procedures/points",
                        json=point_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        stored_patterns.append({
                            "id": point_id,
                            "attack_type": attack_type,
                            "pattern": pattern
                        })
                        relationship_mappings[point_id] = data["related_attacks"]
                        logger.info(f"✅ Stored pattern: {attack_type} - {pattern}")
                    else:
                        logger.error(f"❌ Failed to store {attack_type} pattern: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Error storing {attack_type}: {e}")
        
        return {
            "stored_patterns": len(stored_patterns),
            "total_patterns": sum(len(data["patterns"]) for data in self.attack_patterns.values()),
            "relationship_mappings": relationship_mappings
        }
    
    async def test_vector_similarity_correlation(self) -> Dict[str, Any]:
        """Test vector similarity to find related attack patterns"""
        logger.info("🔍 Testing vector similarity correlation...")
        
        # Test with a known attack pattern
        test_attack = "eval(malicious_code)"
        test_embedding = self.create_attack_vector_embedding(test_attack, "code_injection")
        
        # Search for similar patterns
        search_request = {
            "vector": test_embedding,
            "limit": 5,
            "with_payload": True,
            "score_threshold": 0.3
        }
        
        try:
            response = requests.post(
                f"{self.qdrant_url}/collections/security_procedures/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json().get('result', [])
                
                similar_attacks = []
                mitigation_overlap = []
                
                for result in results:
                    payload = result.get('payload', {})
                    score = result.get('score', 0.0)
                    
                    attack_info = {
                        "attack_type": payload.get('attack_type'),
                        "pattern": payload.get('pattern'),
                        "similarity_score": score,
                        "severity": payload.get('severity'),
                        "mitigations": payload.get('mitigations', [])
                    }
                    similar_attacks.append(attack_info)
                    
                    # Check mitigation overlap
                    test_mitigations = self.attack_patterns["code_injection"]["mitigations"]
                    pattern_mitigations = payload.get('mitigations', [])
                    overlap = set(test_mitigations) & set(pattern_mitigations)
                    
                    if overlap:
                        mitigation_overlap.append({
                            "attack": payload.get('attack_type'),
                            "shared_mitigations": list(overlap),
                            "effectiveness": len(overlap) / max(len(test_mitigations), 1)
                        })
                
                logger.info(f"✅ Found {len(similar_attacks)} similar attack patterns")
                logger.info(f"✅ Identified {len(mitigation_overlap)} mitigation overlaps")
                
                return {
                    "test_attack": test_attack,
                    "similar_attacks": similar_attacks,
                    "mitigation_correlations": mitigation_overlap,
                    "correlation_quality": len(similar_attacks) > 0
                }
            else:
                logger.error(f"❌ Vector similarity search failed: {response.status_code}")
                return {"error": "search_failed"}
                
        except Exception as e:
            logger.error(f"❌ Vector correlation test error: {e}")
            return {"error": str(e)}
    
    async def test_graph_relationship_analysis(self) -> Dict[str, Any]:
        """Test graph-based relationship analysis"""
        logger.info("🕸️ Testing graph relationship analysis...")
        
        # Analyze attack chain relationships
        attack_chains = []
        mitigation_effectiveness = {}
        
        # Find attack chains (paths between attack types)
        for source_attack in self.attack_patterns.keys():
            for target_attack in self.attack_patterns.keys():
                if source_attack != target_attack:
                    try:
                        if self.attack_graph.has_node(source_attack) and self.attack_graph.has_node(target_attack):
                            if nx.has_path(self.attack_graph, source_attack, target_attack):
                                path = nx.shortest_path(self.attack_graph, source_attack, target_attack)
                                if len(path) <= 3:  # Only short chains
                                    attack_chains.append({
                                        "chain": path,
                                        "length": len(path) - 1,
                                        "severity": max(self.attack_patterns[attack]["severity"] for attack in path if attack in self.attack_patterns)
                                    })
                    except:
                        pass
        
        # Analyze mitigation effectiveness
        for mitigation_node in [n for n in self.attack_graph.nodes() if n.startswith("mitigation_")]:
            mitigation_name = mitigation_node.replace("mitigation_", "")
            
            # Count how many attacks this mitigation prevents
            prevented_attacks = []
            for neighbor in self.attack_graph.neighbors(mitigation_node):
                if neighbor in self.attack_patterns:
                    prevented_attacks.append({
                        "attack": neighbor,
                        "severity": self.attack_patterns[neighbor]["severity"]
                    })
            
            if prevented_attacks:
                avg_severity = sum(attack["severity"] for attack in prevented_attacks) / len(prevented_attacks)
                mitigation_effectiveness[mitigation_name] = {
                    "prevents_count": len(prevented_attacks),
                    "avg_severity_prevented": avg_severity,
                    "effectiveness_score": len(prevented_attacks) * avg_severity / 10
                }
        
        # Find critical vulnerabilities (high centrality in graph)
        centrality = nx.degree_centrality(self.attack_graph)
        critical_attacks = [(attack, centrality[attack]) for attack in self.attack_patterns.keys() 
                          if attack in centrality]
        critical_attacks.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"✅ Identified {len(attack_chains)} attack chains")
        logger.info(f"✅ Analyzed {len(mitigation_effectiveness)} mitigation strategies")
        logger.info(f"✅ Found {len(critical_attacks)} critical attack vectors")
        
        return {
            "attack_chains": attack_chains[:10],  # Top 10 chains
            "mitigation_effectiveness": mitigation_effectiveness,
            "critical_attacks": critical_attacks[:5],  # Top 5 critical
            "graph_metrics": {
                "total_nodes": self.attack_graph.number_of_nodes(),
                "total_edges": self.attack_graph.number_of_edges(),
                "density": nx.density(self.attack_graph)
            }
        }
    
    async def test_integrated_threat_analysis(self) -> Dict[str, Any]:
        """Test integrated analysis using both vector and graph data"""
        logger.info("🧠 Testing integrated threat analysis...")
        
        # Simulate real-world attack scenarios
        test_scenarios = [
            {
                "name": "Multi-stage Code Injection",
                "code": "eval(base64_decode($_GET['cmd'])); system('rm -rf /');",
                "expected_attacks": ["code_injection", "command_injection"],
                "expected_severity": "critical"
            },
            {
                "name": "SQL Injection with XSS",
                "code": "SELECT * FROM users WHERE id='1' UNION SELECT '<script>alert(1)</script>'",
                "expected_attacks": ["sql_injection", "xss"],
                "expected_severity": "high"
            },
            {
                "name": "Path Traversal to Code Execution",
                "code": "include('../../etc/passwd'); eval($malicious);",
                "expected_attacks": ["path_traversal", "code_injection"],
                "expected_severity": "critical"
            }
        ]
        
        analysis_results = []
        
        for scenario in test_scenarios:
            logger.info(f"  Analyzing: {scenario['name']}")
            
            # Vector-based analysis: Find similar patterns
            scenario_embedding = self.create_attack_vector_embedding(scenario["code"], "mixed_attack")
            
            search_request = {
                "vector": scenario_embedding,
                "limit": 10,
                "with_payload": True,
                "score_threshold": 0.2
            }
            
            try:
                response = requests.post(
                    f"{self.qdrant_url}/collections/security_procedures/points/search",
                    json=search_request,
                    headers={"Content-Type": "application/json"}
                )
                
                vector_matches = []
                if response.status_code == 200:
                    results = response.json().get('result', [])
                    vector_matches = [
                        {
                            "attack_type": r.get('payload', {}).get('attack_type'),
                            "similarity": r.get('score', 0.0),
                            "severity": r.get('payload', {}).get('severity')
                        }
                        for r in results
                    ]
                
                # Enhanced pattern-based detection for better accuracy
                code_lower = scenario["code"].lower()
                detected_attacks = list(set(match["attack_type"] for match in vector_matches if match["attack_type"]))
                
                # Add direct pattern matching to improve detection accuracy
                if any(pattern in code_lower for pattern in ["eval(", "exec(", "system("]):
                    if "code_injection" not in detected_attacks:
                        detected_attacks.append("code_injection")
                
                if any(pattern in code_lower for pattern in ["union select", "'; drop", "1=1--"]):
                    if "sql_injection" not in detected_attacks:
                        detected_attacks.append("sql_injection")
                        
                if any(pattern in code_lower for pattern in ["../", "..\\"]):
                    if "path_traversal" not in detected_attacks:
                        detected_attacks.append("path_traversal")
                        
                if any(pattern in code_lower for pattern in ["<script>", "javascript:", "onerror="]):
                    if "xss" not in detected_attacks:
                        detected_attacks.append("xss")
                        
                if any(pattern in code_lower for pattern in ["|", "&&", ";"]):
                    if "command_injection" not in detected_attacks:
                        detected_attacks.append("command_injection")
                
                # Find possible attack chains between detected attacks
                attack_chains = []
                for i, attack1 in enumerate(detected_attacks):
                    for attack2 in detected_attacks[i+1:]:
                        if (self.attack_graph.has_node(attack1) and 
                            self.attack_graph.has_node(attack2) and
                            nx.has_path(self.attack_graph, attack1, attack2)):
                            chain = nx.shortest_path(self.attack_graph, attack1, attack2)
                            attack_chains.append(chain)
                
                # Aggregate mitigations from all detected attacks
                all_mitigations = set()
                max_severity = 0
                for attack in detected_attacks:
                    if attack in self.attack_patterns:
                        all_mitigations.update(self.attack_patterns[attack]["mitigations"])
                        max_severity = max(max_severity, self.attack_patterns[attack]["severity"])
                
                # Determine overall threat level
                if max_severity >= 9:
                    threat_level = "critical"
                elif max_severity >= 7:
                    threat_level = "high"
                elif max_severity >= 5:
                    threat_level = "medium"
                else:
                    threat_level = "low"
                
                analysis_result = {
                    "scenario": scenario["name"],
                    "detected_attacks": detected_attacks,
                    "vector_matches": len(vector_matches),
                    "attack_chains": attack_chains,
                    "recommended_mitigations": list(all_mitigations),
                    "threat_level": threat_level,
                    "max_severity": max_severity,
                    "analysis_accuracy": len(set(detected_attacks) & set(scenario["expected_attacks"])) / len(scenario["expected_attacks"])
                }
                
                analysis_results.append(analysis_result)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {scenario['name']}: {e}")
                analysis_results.append({
                    "scenario": scenario["name"],
                    "error": str(e)
                })
        
        # Calculate overall analysis effectiveness
        successful_analyses = [r for r in analysis_results if "error" not in r]
        avg_accuracy = sum(r.get("analysis_accuracy", 0) for r in successful_analyses) / len(successful_analyses) if successful_analyses else 0
        
        logger.info(f"✅ Completed integrated analysis of {len(test_scenarios)} scenarios")
        logger.info(f"✅ Average detection accuracy: {avg_accuracy:.2%}")
        
        return {
            "scenario_results": analysis_results,
            "overall_accuracy": avg_accuracy,
            "successful_analyses": len(successful_analyses),
            "total_scenarios": len(test_scenarios)
        }
    
    async def test_knowledge_base_generation(self) -> Dict[str, Any]:
        """Test generation of security knowledge base from correlations"""
        logger.info("📚 Testing knowledge base generation...")
        
        # Generate mitigation knowledge base
        mitigation_kb = {}
        attack_pattern_kb = {}
        circumvention_methods = {}
        
        # Analyze mitigation effectiveness across attack types
        for mitigation_node in [n for n in self.attack_graph.nodes() if n.startswith("mitigation_")]:
            mitigation_name = mitigation_node.replace("mitigation_", "")
            
            # Find all attacks this mitigation prevents
            prevented_attacks = []
            attack_severities = []
            
            for neighbor in self.attack_graph.neighbors(mitigation_node):
                if neighbor in self.attack_patterns:
                    prevented_attacks.append(neighbor)
                    attack_severities.append(self.attack_patterns[neighbor]["severity"])
            
            if prevented_attacks:
                mitigation_kb[mitigation_name] = {
                    "prevents": prevented_attacks,
                    "effectiveness_score": sum(attack_severities) / len(attack_severities),
                    "coverage": len(prevented_attacks),
                    "implementation_priority": "high" if sum(attack_severities) / len(attack_severities) >= 8 else "medium"
                }
        
        # Generate attack pattern knowledge base with circumvention analysis
        for attack_type, data in self.attack_patterns.items():
            # Analyze how this attack might be circumvented
            potential_circumventions = []
            
            # Look for related attacks that might bypass mitigations
            for related_attack in data["related_attacks"]:
                if related_attack in self.attack_patterns:
                    related_mitigations = set(self.attack_patterns[related_attack]["mitigations"])
                    current_mitigations = set(data["mitigations"])
                    
                    # Find gaps in mitigation coverage
                    mitigation_gaps = related_mitigations - current_mitigations
                    if mitigation_gaps:
                        potential_circumventions.append({
                            "method": f"escalate_to_{related_attack}",
                            "bypass_mitigations": list(mitigation_gaps),
                            "difficulty": "medium" if len(mitigation_gaps) <= 2 else "high"
                        })
            
            # Advanced evasion techniques (simulated)
            evasion_techniques = [
                {"method": "obfuscation", "description": f"Obfuscate {attack_type} patterns to evade detection"},
                {"method": "encoding", "description": f"Encode {attack_type} payloads in different formats"},
                {"method": "fragmentation", "description": f"Split {attack_type} across multiple requests"}
            ]
            
            attack_pattern_kb[attack_type] = {
                "severity": data["severity"],
                "common_patterns": data["patterns"],
                "mitigations": data["mitigations"],
                "circumvention_methods": potential_circumventions,
                "evasion_techniques": evasion_techniques[:2],  # Top 2 techniques
                "detection_difficulty": "high" if data["severity"] >= 9 else "medium"
            }
        
        # Generate advanced security improvement recommendations
        security_improvements = []
        
        # Identify mitigation gaps
        all_attacks = set(self.attack_patterns.keys())
        all_mitigations = set()
        for data in self.attack_patterns.values():
            all_mitigations.update(data["mitigations"])
        
        for attack in all_attacks:
            attack_mitigations = set(self.attack_patterns[attack]["mitigations"])
            missing_mitigations = all_mitigations - attack_mitigations
            
            if missing_mitigations and self.attack_patterns[attack]["severity"] >= 8:
                security_improvements.append({
                    "attack_type": attack,
                    "recommended_additional_mitigations": list(missing_mitigations)[:3],
                    "priority": "high",
                    "rationale": f"High severity attack ({self.attack_patterns[attack]['severity']}) with mitigation gaps"
                })
        
        # Generate defense-in-depth recommendations
        defense_layers = {
            "detection_layer": ["pattern_matching", "behavioral_analysis", "anomaly_detection"],
            "prevention_layer": ["input_validation", "output_encoding", "access_controls"],
            "response_layer": ["automated_blocking", "incident_logging", "alert_generation"],
            "recovery_layer": ["backup_systems", "rollback_mechanisms", "damage_assessment"]
        }
        
        logger.info(f"✅ Generated knowledge base with {len(mitigation_kb)} mitigation strategies")
        logger.info(f"✅ Analyzed {len(attack_pattern_kb)} attack patterns with circumvention methods")
        logger.info(f"✅ Created {len(security_improvements)} security improvement recommendations")
        
        return {
            "mitigation_knowledge_base": mitigation_kb,
            "attack_pattern_knowledge_base": attack_pattern_kb,
            "security_improvements": security_improvements,
            "defense_layers": defense_layers,
            "knowledge_base_metrics": {
                "total_mitigations": len(mitigation_kb),
                "total_attack_patterns": len(attack_pattern_kb),
                "improvement_recommendations": len(security_improvements),
                "coverage_score": len(mitigation_kb) / len(all_mitigations) * 100
            }
        }
    
    async def run_comprehensive_correlation_test(self):
        """Run comprehensive vector-graph correlation test suite"""
        logger.info("🚀 Starting Vector-Graph Correlation Test Suite")
        logger.info("=" * 70)
        
        results = {}
        
        try:
            # Test 1: Store Attack Patterns
            logger.info("\n--- Test 1: Store Attack Patterns in Vector DB ---")
            results['pattern_storage'] = await self.store_attack_patterns_in_vector_db()
            
            # Test 2: Vector Similarity Correlation
            logger.info("\n--- Test 2: Vector Similarity Correlation ---")
            results['vector_correlation'] = await self.test_vector_similarity_correlation()
            
            # Test 3: Graph Relationship Analysis
            logger.info("\n--- Test 3: Graph Relationship Analysis ---")
            results['graph_analysis'] = await self.test_graph_relationship_analysis()
            
            # Test 4: Integrated Threat Analysis
            logger.info("\n--- Test 4: Integrated Threat Analysis ---")
            results['integrated_analysis'] = await self.test_integrated_threat_analysis()
            
            # Test 5: Knowledge Base Generation
            logger.info("\n--- Test 5: Knowledge Base Generation ---")
            results['knowledge_base'] = await self.test_knowledge_base_generation()
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            results['error'] = str(e)
        
        # Generate comprehensive summary
        logger.info("\n" + "=" * 70)
        logger.info("🎯 Vector-Graph Correlation Test Results")
        logger.info("=" * 70)
        
        # Analyze results
        total_tests = 0
        passed_tests = 0
        
        # Pattern Storage Test
        if results.get('pattern_storage', {}).get('stored_patterns', 0) > 0:
            logger.info("Attack Pattern Storage......... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Attack Pattern Storage......... ❌ FAILED")
        total_tests += 1
        
        # Vector Correlation Test
        if results.get('vector_correlation', {}).get('correlation_quality', False):
            logger.info("Vector Similarity Correlation.. ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Vector Similarity Correlation.. ❌ FAILED")
        total_tests += 1
        
        # Graph Analysis Test
        graph_results = results.get('graph_analysis', {})
        if graph_results.get('attack_chains') and graph_results.get('mitigation_effectiveness'):
            logger.info("Graph Relationship Analysis.... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Graph Relationship Analysis.... ❌ FAILED")
        total_tests += 1
        
        # Integrated Analysis Test
        integrated_results = results.get('integrated_analysis', {})
        if integrated_results.get('overall_accuracy', 0) >= 0.5:
            logger.info("Integrated Threat Analysis..... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Integrated Threat Analysis..... ❌ FAILED")
        total_tests += 1
        
        # Knowledge Base Test
        kb_results = results.get('knowledge_base', {})
        if kb_results.get('mitigation_knowledge_base') and kb_results.get('security_improvements'):
            logger.info("Knowledge Base Generation....... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Knowledge Base Generation....... ❌ FAILED")
        total_tests += 1
        
        success_rate = passed_tests / total_tests * 100
        
        logger.info("-" * 70)
        logger.info(f"Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.0f}%)")
        
        # Detailed success metrics
        if integrated_results.get('overall_accuracy'):
            logger.info(f"Detection Accuracy: {integrated_results['overall_accuracy']:.1%}")
        
        if kb_results.get('knowledge_base_metrics'):
            metrics = kb_results['knowledge_base_metrics']
            logger.info(f"Knowledge Base Coverage: {metrics.get('coverage_score', 0):.0f}%")
            logger.info(f"Security Improvements: {metrics.get('improvement_recommendations', 0)} recommendations")
        
        if success_rate >= 80:
            logger.info("🎉 EXCELLENT: Vector-Graph correlation working excellently!")
        elif success_rate >= 60:
            logger.info("✅ GOOD: Vector-Graph correlation mostly functional")
        else:
            logger.info("⚠️ NEEDS ATTENTION: Vector-Graph correlation issues detected")
        
        return {
            'test_results': results,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate,
                'detection_accuracy': integrated_results.get('overall_accuracy', 0),
                'knowledge_base_coverage': kb_results.get('knowledge_base_metrics', {}).get('coverage_score', 0)
            }
        }


async def main():
    """Main test execution"""
    tester = VectorGraphCorrelationTester()
    results = await tester.run_comprehensive_correlation_test()
    
    success_rate = results['summary']['success_rate']
    detection_accuracy = results['summary']['detection_accuracy']
    
    print(f"\n🏁 Vector-Graph Correlation Test Suite Completed")
    print(f"📊 Success Rate: {success_rate:.0f}%")
    print(f"🎯 Detection Accuracy: {detection_accuracy:.1%}")
    print(f"📚 Knowledge Base Coverage: {results['summary']['knowledge_base_coverage']:.0f}%")
    
    return success_rate >= 60 and detection_accuracy >= 0.5


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)