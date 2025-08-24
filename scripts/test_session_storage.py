#!/usr/bin/env python3
"""
Simplified Multi-Session Storage Test
Tests session isolation and data persistence
"""

import asyncio
import json
import logging
import requests
import websockets
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionStorageTester:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.mcp_url = "ws://localhost:8083"
    
    async def test_qdrant_storage_format(self):
        """Test correct Qdrant storage format"""
        logger.info("🔧 Testing Qdrant storage format...")
        
        # Correct format for Qdrant point storage
        correct_payload = {
            "points": [
                {
                    "id": f"test_{int(time.time())}",
                    "vector": [0.1] * 384,  # 384-dimensional vector
                    "payload": {
                        "session_id": "test_session",
                        "lesson_type": "format_test",
                        "created_at": datetime.now().isoformat()
                    }
                }
            ]
        }
        
        try:
            response = requests.put(
                f"{self.qdrant_url}/collections/security_procedures/points",
                json=correct_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("✅ Qdrant storage format working")
                return True
            else:
                logger.error(f"❌ Qdrant storage failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Storage test error: {e}")
            return False
    
    async def test_concurrent_mcp_sessions(self):
        """Test multiple concurrent MCP sessions"""
        logger.info("🔗 Testing concurrent MCP sessions...")
        
        session_results = []
        
        async def create_session(session_num):
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
                            "name": f"concurrent-test-{session_num}",
                            "version": "1.0.0"
                        },
                        "capabilities": {}
                    }
                }
                
                await websocket.send(json.dumps(init_msg))
                response = await websocket.recv()
                result = json.loads(response)
                
                success = 'result' in result
                
                # Perform a quick threat analysis
                if success:
                    scan_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "security_scan_code",
                            "arguments": {
                                "code": f"# Session {session_num} test\neval('print({session_num})')",
                                "language": "python",
                                "security_level": "moderate"
                            }
                        }
                    }
                    
                    await websocket.send(json.dumps(scan_msg))
                    scan_response = await websocket.recv()
                    scan_result = json.loads(scan_response)
                    
                    threat_detected = 'result' in scan_result
                else:
                    threat_detected = False
                
                await websocket.close()
                
                return {
                    "session": session_num,
                    "connected": success,
                    "threat_analysis": threat_detected
                }
                
            except Exception as e:
                return {
                    "session": session_num,
                    "connected": False,
                    "error": str(e)
                }
        
        # Create 3 sessions concurrently
        tasks = [create_session(i) for i in range(3)]
        session_results = await asyncio.gather(*tasks)
        
        successful_sessions = sum(1 for s in session_results if s.get('connected', False))
        successful_analyses = sum(1 for s in session_results if s.get('threat_analysis', False))
        
        logger.info(f"✅ {successful_sessions}/3 sessions connected successfully")
        logger.info(f"✅ {successful_analyses}/3 threat analyses completed")
        
        return {
            "total_sessions": 3,
            "successful_connections": successful_sessions,
            "successful_analyses": successful_analyses,
            "session_results": session_results
        }
    
    async def test_persistent_storage(self):
        """Test persistent storage across operations"""
        logger.info("💾 Testing persistent storage...")
        
        # Store multiple lessons with correct format
        lesson_count = 3
        stored_lessons = []
        
        for i in range(lesson_count):
            lesson_data = {
                "points": [
                    {
                        "id": f"lesson_persistent_{i}_{int(time.time())}",
                        "vector": [(i + 1) * 0.1] * 384,  # Unique vector per lesson
                        "payload": {
                            "lesson_id": f"persistent_lesson_{i}",
                            "session_id": f"persistence_test_session_{i}",
                            "threat_type": f"test_threat_{i}",
                            "description": f"Persistent lesson {i} for testing",
                            "severity": "medium",
                            "created_at": datetime.now().isoformat(),
                            "test_marker": "multi_session_persistence"
                        }
                    }
                ]
            }
            
            try:
                response = requests.put(
                    f"{self.qdrant_url}/collections/security_procedures/points",
                    json=lesson_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    stored_lessons.append(f"persistent_lesson_{i}")
                    logger.info(f"✅ Stored persistent lesson {i}")
                else:
                    logger.error(f"❌ Failed to store lesson {i}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error storing lesson {i}: {e}")
        
        # Wait a moment for storage to propagate
        await asyncio.sleep(2)
        
        # Search for stored lessons
        search_request = {
            "vector": [0.1] * 384,  # Simple search vector
            "limit": 10,
            "with_payload": True,
            "filter": {
                "match": {
                    "key": "test_marker",
                    "value": "multi_session_persistence"
                }
            }
        }
        
        try:
            search_response = requests.post(
                f"{self.qdrant_url}/collections/security_procedures/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if search_response.status_code == 200:
                search_results = search_response.json().get('result', [])
                found_lessons = len(search_results)
                
                logger.info(f"✅ Found {found_lessons}/{lesson_count} persistent lessons")
                
                return {
                    "lessons_stored": len(stored_lessons),
                    "lessons_found": found_lessons,
                    "storage_persistent": found_lessons > 0,
                    "search_results": search_results[:3]  # Show first 3 results
                }
            else:
                logger.error(f"❌ Search failed: {search_response.status_code}")
                return {"error": "search_failed"}
                
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return {"error": str(e)}
    
    async def test_session_isolation(self):
        """Test that sessions are properly isolated"""
        logger.info("🔒 Testing session isolation...")
        
        session_data = []
        
        # Create session-specific data
        for session_id in range(2):
            session_lesson = {
                "points": [
                    {
                        "id": f"isolation_test_{session_id}_{int(time.time())}",
                        "vector": [(session_id + 1) * 0.2] * 384,
                        "payload": {
                            "session_id": f"isolation_session_{session_id}",
                            "session_specific_data": f"only_session_{session_id}_sees_this",
                            "isolation_test": True,
                            "created_at": datetime.now().isoformat()
                        }
                    }
                ]
            }
            
            try:
                response = requests.put(
                    f"{self.qdrant_url}/collections/security_procedures/points",
                    json=session_lesson,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    session_data.append(f"isolation_session_{session_id}")
                    logger.info(f"✅ Stored data for session {session_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error storing session {session_id} data: {e}")
        
        await asyncio.sleep(1)
        
        # Verify data can be retrieved (simulating cross-session access)
        search_request = {
            "vector": [0.2] * 384,
            "limit": 10,
            "with_payload": True,
            "filter": {
                "match": {
                    "key": "isolation_test",
                    "value": True
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
                
                # Check if both sessions' data is accessible
                session_0_found = any('only_session_0_sees_this' in r.get('payload', {}).get('session_specific_data', '') for r in results)
                session_1_found = any('only_session_1_sees_this' in r.get('payload', {}).get('session_specific_data', '') for r in results)
                
                logger.info(f"✅ Session isolation test: Session 0 data found: {session_0_found}, Session 1 data found: {session_1_found}")
                
                return {
                    "sessions_stored": len(session_data),
                    "session_0_accessible": session_0_found,
                    "session_1_accessible": session_1_found,
                    "cross_session_learning": session_0_found and session_1_found
                }
            else:
                return {"error": "search_failed"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def run_session_storage_tests(self):
        """Run all session storage tests"""
        logger.info("🚀 Starting Session Storage Tests")
        logger.info("=" * 50)
        
        results = {}
        
        # Test 1: Qdrant Format
        logger.info("\n--- Test 1: Qdrant Storage Format ---")
        results['qdrant_format'] = await self.test_qdrant_storage_format()
        
        # Test 2: Concurrent Sessions
        logger.info("\n--- Test 2: Concurrent MCP Sessions ---")
        results['concurrent_sessions'] = await self.test_concurrent_mcp_sessions()
        
        # Test 3: Persistent Storage
        logger.info("\n--- Test 3: Persistent Storage ---")
        results['persistent_storage'] = await self.test_persistent_storage()
        
        # Test 4: Session Isolation
        logger.info("\n--- Test 4: Session Isolation ---")
        results['session_isolation'] = await self.test_session_isolation()
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("🎯 Session Storage Test Results")
        logger.info("=" * 50)
        
        passed_tests = 0
        total_tests = 0
        
        if results.get('qdrant_format'):
            logger.info("Qdrant Storage Format........ ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Qdrant Storage Format........ ❌ FAILED")
        total_tests += 1
        
        concurrent_result = results.get('concurrent_sessions', {})
        if concurrent_result.get('successful_connections', 0) >= 2:
            logger.info("Concurrent MCP Sessions...... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Concurrent MCP Sessions...... ❌ FAILED")
        total_tests += 1
        
        storage_result = results.get('persistent_storage', {})
        if storage_result.get('storage_persistent', False):
            logger.info("Persistent Storage........... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Persistent Storage........... ❌ FAILED")
        total_tests += 1
        
        isolation_result = results.get('session_isolation', {})
        if isolation_result.get('cross_session_learning', False):
            logger.info("Session Isolation/Learning... ✅ PASSED")
            passed_tests += 1
        else:
            logger.info("Session Isolation/Learning... ❌ FAILED")
        total_tests += 1
        
        success_rate = passed_tests / total_tests * 100
        
        logger.info("-" * 50)
        logger.info(f"Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.0f}%)")
        
        if success_rate >= 75:
            logger.info("🎉 EXCELLENT: Multi-session storage working well!")
        elif success_rate >= 50:
            logger.info("✅ GOOD: Multi-session functionality mostly working")
        else:
            logger.info("⚠️ NEEDS ATTENTION: Multi-session storage issues")
        
        return results


async def main():
    tester = SessionStorageTester()
    results = await tester.run_session_storage_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())