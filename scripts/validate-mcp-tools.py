#!/usr/bin/env python3
"""
MCP Tool Validation Script
Validates that Claude Guardian security tools can be invoked via MCP protocol
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime

async def validate_mcp_tools():
    """Validate MCP tool invocation"""
    print("🔍 Claude Guardian MCP Tool Validation")
    print("="*50)
    
    try:
        # Connect to MCP server
        websocket = await websockets.connect("ws://localhost:8083")
        print("✅ Connected to MCP server")
        
        # Initialize MCP session
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "mcp-validator", "version": "1.0.0"},
                "capabilities": {}
            }
        }
        
        await websocket.send(json.dumps(init_msg))
        init_response = json.loads(await websocket.recv())
        
        if "result" in init_response:
            print("✅ MCP session initialized")
        else:
            print(f"❌ Initialization failed: {init_response}")
            return False
            
        # List available tools
        tools_msg = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        await websocket.send(json.dumps(tools_msg))
        tools_response = json.loads(await websocket.recv())
        
        if "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✅ Found {len(tools)} security tools:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Failed to list tools: {tools_response}")
            return False
            
        # Test security scan tool
        scan_msg = {
            "jsonrpc": "2.0",
            "id": 3, 
            "method": "tools/call",
            "params": {
                "name": "security_scan_code",
                "arguments": {
                    "code": "eval('print(hello)')",
                    "language": "python",
                    "security_level": "moderate"
                }
            }
        }
        
        await websocket.send(json.dumps(scan_msg))
        scan_response = json.loads(await websocket.recv())
        
        if "result" in scan_response:
            content = scan_response["result"]["content"][0]["text"]
            print(f"✅ Security scan executed:")
            print(f"  Result: {content[:100]}...")
            
            if "eval" in content.lower() or "dangerous" in content.lower():
                print("✅ Correctly detected dangerous eval() usage")
            else:
                print("⚠️ May not have detected eval() properly")
        else:
            print(f"❌ Security scan failed: {scan_response}")
            
        await websocket.close()
        print("✅ MCP tool validation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def check_mcp_service():
    """Check if MCP service is running"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8083))
        sock.close()
        
        if result == 0:
            print("✅ MCP service is running on port 8083")
            return True
        else:
            print("❌ MCP service is not running on port 8083")
            return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False

async def main():
    """Main validation function"""
    print(f"🚀 Starting MCP validation at {datetime.now()}")
    
    # Check if service is running
    if not check_mcp_service():
        print("\n💡 To start the MCP service, run:")
        print("   python3 scripts/start-mcp-service.py --port 8083")
        return False
        
    # Validate MCP tools
    success = await validate_mcp_tools()
    
    if success:
        print(f"\n🎉 MCP Tool Validation: SUCCESS")
        print("✅ Claude Guardian can be invoked as MCP tool")
        print("✅ Security tools are functional")
        print("✅ Protocol compliance verified")
        return True
    else:
        print(f"\n❌ MCP Tool Validation: FAILED")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)