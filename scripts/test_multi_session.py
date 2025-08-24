#!/usr/bin/env python3
"""
Multi-Session Testing for Claude Guardian
Tests storage, persistence, and lessons learned across multiple concurrent sessions
"""

import asyncio
import json
import logging
import requests
import websockets
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiSessionTester:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.mcp_url = "ws://localhost:8083"
        self.sessions = {}
        self.lesson_counter = 0
        
    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{uuid.uuid4().hex[:8]}"
    
    async def create_mcp_session(self, session_id: str, client_name: str = None) -> bool:
        """Create and initialize an MCP session"""
        try:
            websocket = await websockets.connect(self.mcp_url)
            
            # Initialize session
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": client_name or f"multi-session-tester-{session_id}",
                        "version": "1.0.0"
                    },
                    "capabilities": {}
                }
            }
            
            await websocket.send(json.dumps(init_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            if 'result' in result:
                self.sessions[session_id] = {
                    'websocket': websocket,
                    'connected_at': datetime.now(),
                    'client_name': client_name or f"tester-{session_id}",
                    'lessons_stored': 0,
                    'threats_analyzed': 0
                }
                logger.info(f"✅ Session {session_id} initialized successfully")
                return True
            else:
                logger.error(f"❌ Session {session_id} initialization failed")
                await websocket.close()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create session {session_id}: {e}")
            return False
    
    async def close_session(self, session_id: str):
        """Close an MCP session"""
        if session_id in self.sessions:
            try:
                await self.sessions[session_id]['websocket'].close()
                del self.sessions[session_id]
                logger.info(f"✅ Session {session_id} closed")
            except Exception as e:
                logger.error(f"❌ Error closing session {session_id}: {e}")
    
    async def store_lesson_learned(self, session_id: str, lesson_data: Dict[str, Any]) -> bool:
        """Store a lesson learned from a specific session"""
        try:
            self.lesson_counter += 1
            lesson_id = f"lesson_{self.lesson_counter}_{session_id}"
            
            # Create vector embedding (simplified)
            text_content = f"{lesson_data.get('threat_type', '')} {lesson_data.get('description', '')} {lesson_data.get('mitigation', '')}"
            embedding = [(hash(text_content + str(i)) % 1000) / 1000.0 for i in range(384)]
            
            # Store in Qdrant
            point = {
                "id": lesson_id,
                "vector": embedding,
                "payload": {
                    "session_id": session_id,
                    "threat_type": lesson_data.get('threat_type'),
                    "description": lesson_data.get('description'),
                    "severity": lesson_data.get('severity', 'medium'),
                    "mitigation": lesson_data.get('mitigation'),
                    "learned_at": datetime.now().isoformat(),
                    "source_session": session_id,
                    "type": "lesson_learned"
                }
            }
            
            response = requests.put(
                f"{self.qdrant_url}/collections/security_procedures/points",
                json={"points": [point]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                if session_id in self.sessions:
                    self.sessions[session_id]['lessons_stored'] += 1
                logger.info(f"✅ Lesson {lesson_id} stored from session {session_id}")
                return True
            else:
                logger.error(f"❌ Failed to store lesson {lesson_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing lesson from session {session_id}: {e}")
            return False
    
    async def analyze_threat_in_session(self, session_id: str, threat_code: str, language: str = "python") -> Dict:
        """Analyze a threat in a specific session"""
        try:
            if session_id not in self.sessions:
                return {"error": "Session not found"}
            
            websocket = self.sessions[session_id]['websocket']
            
            # Create unique request ID
            request_id = int(time.time() * 1000) % 10000
            
            scan_msg = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "security_scan_code",
                    "arguments": {
                        "code": threat_code,
                        "language": language,
                        "security_level": "strict"
                    }
                }
            }
            
            await websocket.send(json.dumps(scan_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            if 'result' in result:
                self.sessions[session_id]['threats_analyzed'] += 1
                content = result['result']['content'][0]['text']
                
                # Extract risk info
                risk_level = "unknown"
                if "CRITICAL" in content:
                    risk_level = "critical"
                elif "HIGH" in content:
                    risk_level = "high"
                elif "MEDIUM" in content:
                    risk_level = "medium"
                elif "LOW" in content:
                    risk_level = "low"
                
                return {
                    "session_id": session_id,
                    "risk_level": risk_level,
                    "analysis": content,
                    "is_blocked": result['result'].get('isError', False)
                }
            else:
                return {"error": "Analysis failed", "details": result}
                
        except Exception as e:
            logger.error(f"❌ Error analyzing threat in session {session_id}: {e}")
            return {"error": str(e)}
    
    async def test_concurrent_sessions(self, num_sessions: int = 5) -> Dict:
        """Test concurrent MCP sessions"""
        logger.info(f"🔄 Testing {num_sessions} concurrent sessions...")
        
        # Create multiple sessions concurrently
        session_ids = [self.generate_session_id() for _ in range(num_sessions)]
        
        # Create sessions in parallel
        tasks = [self.create_mcp_session(sid) for sid in session_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_sessions = [sid for sid, result in zip(session_ids, results) if result is True]
        
        logger.info(f"✅ {len(successful_sessions)}/{num_sessions} sessions created successfully")
        
        return {
            "total_requested": num_sessions,
            "successful": len(successful_sessions),
            "failed": num_sessions - len(successful_sessions),
            "session_ids": successful_sessions
        }
    
    async def test_concurrent_storage(self, session_ids: List[str]) -> Dict:
        """Test concurrent storage of lessons learned"""
        logger.info(f"💾 Testing concurrent storage across {len(session_ids)} sessions...")
        
        # Create different lessons for each session
        lessons = [
            {
                "threat_type": f"code_injection_{i}",
                "description": f"Session {i}: Detected use of eval() function in user input processing",
                "severity": "high",
                "mitigation": f"Replace eval() with ast.literal_eval() for safe evaluation - Session {i}"
            }
            for i, _ in enumerate(session_ids)
        ]
        
        # Store lessons concurrently
        tasks = [
            self.store_lesson_learned(session_id, lesson)
            for session_id, lesson in zip(session_ids, lessons)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful_stores = sum(1 for result in results if result is True)
        
        logger.info(f"✅ {successful_stores}/{len(session_ids)} lessons stored successfully")
        
        return {
            "lessons_attempted": len(session_ids),
            "lessons_stored": successful_stores,
            "storage_rate": successful_stores / len(session_ids) * 100
        }
    
    async def test_cross_session_learning(self, session_ids: List[str]) -> Dict:
        """Test if lessons learned in one session are available to others"""
        logger.info("🎓 Testing cross-session learning...")
        
        # Store a lesson in the first session
        lesson = {
            "threat_type": "cross_session_test",
            "description": "Test lesson for cross-session availability",
            "severity": "medium",
            "mitigation": "This lesson should be available to all sessions"
        }
        
        if session_ids:
            await self.store_lesson_learned(session_ids[0], lesson)
            
            # Wait a moment for storage
            await asyncio.sleep(1)
            
            # Search for the lesson from Qdrant
            search_vector = [(hash("cross_session_test" + str(i)) % 1000) / 1000.0 for i in range(384)]
            
            search_request = {
                "vector": search_vector,
                "limit": 10,
                "with_payload": True,
                "filter": {
                    "match": {
                        "key": "threat_type",
                        "value": "cross_session_test"
                    }
                }
            }
            
            try:
                response = requests.post(
                    f"{self.qdrant_url}/collections/security_procedures/points/search",
                    json=search_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    results = response.json().get('result', [])
                    cross_session_available = len(results) > 0
                    
                    logger.info(f"✅ Cross-session learning: {'Available' if cross_session_available else 'Not Available'}")
                    
                    return {
                        "lesson_stored": True,
                        "cross_session_available": cross_session_available,
                        "search_results": len(results)
                    }
                else:
                    logger.error(f"❌ Search failed: {response.status_code}")
                    return {"lesson_stored": True, "cross_session_available": False, "error": "search_failed"}
                    
            except Exception as e:
                logger.error(f"❌ Cross-session search error: {e}")
                return {"lesson_stored": True, "cross_session_available": False, "error": str(e)}
        
        return {"lesson_stored": False, "cross_session_available": False, "error": "no_sessions"}
    
    async def test_concurrent_threat_analysis(self, session_ids: List[str]) -> Dict:
        """Test concurrent threat analysis across multiple sessions"""
        logger.info(f"🛡️ Testing concurrent threat analysis across {len(session_ids)} sessions...")
        
        # Different threat scenarios for each session
        threat_scenarios = [
            "eval(user_input)",
            "os.system('rm -rf /')",
            "subprocess.call(cmd, shell=True)",
            "exec(malicious_code)",
            "import os; os.remove('/etc/passwd')"
        ]
        
        # Pad scenarios if we have more sessions than scenarios
        while len(threat_scenarios) < len(session_ids):
            threat_scenarios.extend(threat_scenarios)
        
        # Analyze threats concurrently
        tasks = [
            self.analyze_threat_in_session(session_id, threat_scenarios[i])
            for i, session_id in enumerate(session_ids[:len(threat_scenarios)])
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_analyses = [r for r in results if isinstance(r, dict) and 'error' not in r]
        blocked_threats = [r for r in successful_analyses if r.get('is_blocked', False)]
        
        logger.info(f"✅ {len(successful_analyses)}/{len(session_ids)} threat analyses completed")
        logger.info(f"🚫 {len(blocked_threats)} threats were blocked")
        
        return {
            "analyses_attempted": len(session_ids),
            "analyses_successful": len(successful_analyses),
            "threats_blocked": len(blocked_threats),
            "blocking_rate": len(blocked_threats) / len(successful_analyses) * 100 if successful_analyses else 0
        }
    
    async def test_persistence_across_reconnects(self, num_reconnects: int = 3) -> Dict:
        """Test data persistence across session reconnects"""
        logger.info(f"🔄 Testing persistence across {num_reconnects} reconnects...")
        
        session_id = self.generate_session_id()
        results = []
        
        for i in range(num_reconnects):
            # Create session
            success = await self.create_mcp_session(session_id, f"persistence-test-{i}")
            if not success:
                results.append({"reconnect": i, "success": False, "error": "connection_failed"})
                continue
            
            # Store a lesson
            lesson = {
                "threat_type": f"persistence_test_{i}",
                "description": f"Reconnect {i}: Testing data persistence",
                "severity": "low",
                "mitigation": f"Test mitigation for reconnect {i}"
            }
            
            stored = await self.store_lesson_learned(session_id, lesson)
            
            # Close session
            await self.close_session(session_id)
            
            results.append({
                "reconnect": i,
                "connected": success,
                "lesson_stored": stored
            })
            
            await asyncio.sleep(1)  # Brief pause between reconnects
        
        # Verify all lessons are still available
        search_vector = [(hash("persistence_test" + str(i)) % 1000) / 1000.0 for i in range(384)]
        
        search_request = {
            "vector": search_vector,
            "limit": 20,
            "with_payload": True
        }
        
        try:
            response = requests.post(
                f"{self.qdrant_url}/collections/security_procedures/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                search_results = response.json().get('result', [])
                persistence_lessons = [r for r in search_results if 'persistence_test' in r.get('payload', {}).get('threat_type', '')]
                
                logger.info(f"✅ {len(persistence_lessons)} persistence lessons found after reconnects")
                
                return {
                    "reconnects": num_reconnects,
                    "lessons_stored": sum(1 for r in results if r.get('lesson_stored', False)),
                    "lessons_persisted": len(persistence_lessons),
                    "persistence_verified": len(persistence_lessons) > 0
                }
            else:
                return {"error": "search_failed", "status_code": response.status_code}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def run_multi_session_test_suite(self):
        """Run complete multi-session test suite"""
        logger.info("🚀 Starting Multi-Session Test Suite")
        logger.info("=" * 70)
        
        test_results = {}
        
        try:
            # Test 1: Concurrent Sessions
            logger.info("\n--- Test 1: Concurrent Sessions ---")
            concurrent_result = await self.test_concurrent_sessions(5)
            test_results['concurrent_sessions'] = concurrent_result
            
            successful_sessions = concurrent_result['session_ids']
            
            if successful_sessions:
                # Test 2: Concurrent Storage
                logger.info("\n--- Test 2: Concurrent Storage ---")
                storage_result = await self.test_concurrent_storage(successful_sessions)
                test_results['concurrent_storage'] = storage_result
                
                # Test 3: Cross-Session Learning
                logger.info("\n--- Test 3: Cross-Session Learning ---")
                learning_result = await self.test_cross_session_learning(successful_sessions)
                test_results['cross_session_learning'] = learning_result
                
                # Test 4: Concurrent Threat Analysis
                logger.info("\n--- Test 4: Concurrent Threat Analysis ---")
                threat_result = await self.test_concurrent_threat_analysis(successful_sessions)
                test_results['concurrent_threat_analysis'] = threat_result
                
                # Clean up sessions
                for session_id in successful_sessions:
                    await self.close_session(session_id)
            
            # Test 5: Persistence Across Reconnects
            logger.info("\n--- Test 5: Persistence Across Reconnects ---")
            persistence_result = await self.test_persistence_across_reconnects(3)
            test_results['persistence'] = persistence_result
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            test_results['error'] = str(e)
        
        # Generate Summary
        logger.info("\n" + "=" * 70)
        logger.info("🎯 Multi-Session Test Results Summary")
        logger.info("=" * 70)
        
        # Analyze results
        total_tests = 0
        passed_tests = 0
        
        if 'concurrent_sessions' in test_results:
            total_tests += 1
            if test_results['concurrent_sessions']['successful'] >= 4:  # At least 80% success
                passed_tests += 1
                logger.info("Concurrent Sessions............ ✅ PASSED")
            else:
                logger.info("Concurrent Sessions............ ❌ FAILED")
        
        if 'concurrent_storage' in test_results:
            total_tests += 1
            if test_results['concurrent_storage']['storage_rate'] >= 80:
                passed_tests += 1
                logger.info("Concurrent Storage............. ✅ PASSED")
            else:
                logger.info("Concurrent Storage............. ❌ FAILED")
        
        if 'cross_session_learning' in test_results:
            total_tests += 1
            if test_results['cross_session_learning'].get('cross_session_available', False):
                passed_tests += 1
                logger.info("Cross-Session Learning......... ✅ PASSED")
            else:
                logger.info("Cross-Session Learning......... ❌ FAILED")
        
        if 'concurrent_threat_analysis' in test_results:
            total_tests += 1
            if test_results['concurrent_threat_analysis']['analyses_successful'] >= 4:
                passed_tests += 1
                logger.info("Concurrent Threat Analysis..... ✅ PASSED")
            else:
                logger.info("Concurrent Threat Analysis..... ❌ FAILED")
        
        if 'persistence' in test_results:
            total_tests += 1
            if test_results['persistence'].get('persistence_verified', False):
                passed_tests += 1
                logger.info("Persistence Across Reconnects.. ✅ PASSED")
            else:
                logger.info("Persistence Across Reconnects.. ❌ FAILED")
        
        logger.info("-" * 70)
        logger.info(f"Overall Results: {passed_tests}/{total_tests} tests passed")
        
        success_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        if success_rate >= 90:
            logger.info("🎉 EXCELLENT: Multi-session functionality working perfectly!")
        elif success_rate >= 70:
            logger.info("✅ GOOD: Multi-session functionality mostly working")
        else:
            logger.info("⚠️ NEEDS ATTENTION: Multi-session issues detected")
        
        return {
            'test_results': test_results,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate
            }
        }


async def main():
    """Main test execution"""
    tester = MultiSessionTester()
    results = await tester.run_multi_session_test_suite()
    
    success_rate = results['summary']['success_rate']
    print(f"\n🏁 Multi-Session Test Suite Completed")
    print(f"📊 Success Rate: {success_rate:.0f}%")
    
    return success_rate >= 70


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)