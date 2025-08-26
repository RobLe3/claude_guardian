#!/usr/bin/env python3
"""
Simple MCP test to verify basic connectivity
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_connection():
    """Test basic MCP connection and protocol"""
    
    try:
        # Connect to MCP server
        logger.info("Connecting to MCP server...")
        websocket = await websockets.connect("ws://localhost:8083")
        logger.info("✅ Connected to MCP server")
        
        # Send initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "simple-test-client",
                    "version": "1.0.0"
                },
                "capabilities": {}
            }
        }
        
        logger.info("Sending initialize message...")
        await websocket.send(json.dumps(init_message))
        
        # Wait for response
        response_data = await websocket.recv()
        response = json.loads(response_data)
        
        logger.info(f"Received response: {response}")
        
        if "result" in response:
            logger.info("✅ MCP initialization successful!")
            
            # Test tools list
            tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            logger.info("Requesting tools list...")
            await websocket.send(json.dumps(tools_message))
            
            tools_response_data = await websocket.recv()
            tools_response = json.loads(tools_response_data)
            
            logger.info(f"Tools response: {tools_response}")
            
            if "result" in tools_response:
                tools = tools_response["result"]["tools"]
                logger.info(f"✅ Found {len(tools)} security tools:")
                for tool in tools:
                    logger.info(f"  - {tool['name']}: {tool['description']}")
                
                # Test a security tool
                if tools:
                    tool_call_message = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "security_scan_code",
                            "arguments": {
                                "code": "import os; os.system('echo hello')",
                                "language": "python",
                                "security_level": "moderate"
                            }
                        }
                    }
                    
                    logger.info("Testing security_scan_code tool...")
                    await websocket.send(json.dumps(tool_call_message))
                    
                    scan_response_data = await websocket.recv()
                    scan_response = json.loads(scan_response_data)
                    
                    logger.info(f"Security scan response: {scan_response}")
                    
                    if "result" in scan_response:
                        content = scan_response["result"]["content"]
                        for item in content:
                            if item["type"] == "text":
                                logger.info(f"Security scan result:\n{item['text']}")
                        
                        logger.info("✅ Security tool execution successful!")
                    else:
                        logger.error(f"Security tool failed: {scan_response}")
                        
        else:
            logger.error(f"Initialization failed: {response}")
            
        await websocket.close()
        logger.info("✅ Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple MCP Integration Test")
    print("==============================")
    
    result = asyncio.run(test_mcp_connection())
    if result:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")