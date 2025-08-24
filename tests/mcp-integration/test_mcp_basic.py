#!/usr/bin/env python3
"""
Basic MCP Integration Tests for IFF-Guardian
Tests the MCP protocol implementation and basic tool invocation
"""

import asyncio
import json
import websockets
import pytest
import time
from datetime import datetime
from typing import Dict, Any, Optional

class MCPTestClient:
    """Simple MCP test client for testing IFF-Guardian MCP integration"""
    
    def __init__(self, websocket_url: str, auth_token: str = None):
        self.websocket_url = websocket_url
        self.auth_token = auth_token
        self.websocket = None
        self.session_id = None
        self.request_id = 0
    
    async def connect(self):
        """Connect to the MCP server via WebSocket"""
        url = self.websocket_url
        # For the test server, we don't need authentication
        # if self.auth_token:
        #     url += f"?token={self.auth_token}"
        
        try:
            self.websocket = await websockets.connect(url)
            print(f"✅ Connected to IFF-Guardian MCP server: {self.websocket_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.websocket:
            await self.websocket.close()
            print("✅ Disconnected from MCP server")
    
    def next_request_id(self) -> int:
        """Get the next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def send_message(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send an MCP message and wait for response"""
        if not self.websocket:
            raise Exception("Not connected to MCP server")
        
        message = {
            "jsonrpc": "2.0",
            "id": self.next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        print(f"📤 Sending: {method}")
        await self.websocket.send(json.dumps(message))
        
        # Wait for response
        response_data = await self.websocket.recv()
        response = json.loads(response_data)
        
        print(f"📥 Received: {response.get('result', response.get('error', 'Unknown'))}")
        return response
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP session"""
        params = {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "iff-guardian-test-client",
                "version": "1.0.0"
            },
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            }
        }
        
        response = await self.send_message("initialize", params)
        if "result" in response:
            self.session_id = f"test_session_{int(time.time())}"
            print(f"✅ MCP session initialized: {self.session_id}")
        
        return response

class TestIFFGuardianMCP:
    """Test suite for IFF-Guardian MCP integration"""
    
    @pytest.fixture
    async def mcp_client(self):
        """Create and initialize an MCP test client"""
        # Use test authentication token (in real scenario, this would be obtained from auth service)
        test_token = "test_auth_token_12345"
        client = MCPTestClient("ws://localhost:8083", test_token)
        
        # Connect and initialize
        connected = await client.connect()
        if not connected:
            pytest.skip("Could not connect to IFF-Guardian MCP service")
        
        init_response = await client.initialize()
        if "error" in init_response:
            await client.disconnect()
            pytest.skip(f"Could not initialize MCP session: {init_response['error']}")
        
        yield client
        
        # Cleanup
        await client.disconnect()
    
    async def test_mcp_connection(self, mcp_client):
        """Test basic MCP connection and initialization"""
        assert mcp_client.websocket is not None
        assert mcp_client.session_id is not None
        print("✅ MCP connection and initialization successful")
    
    async def test_list_tools(self, mcp_client):
        """Test listing available security tools"""
        response = await mcp_client.send_message("tools/list")
        
        # Check response structure
        assert "result" in response, f"Expected result, got: {response}"
        assert "tools" in response["result"], "Expected tools array in result"
        
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} security tools available")
        
        # Verify expected security tools exist
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "security_scan_code",
            "analyze_threat",
            "check_permissions",
            "validate_input",
            "monitor_execution"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"✅ Security tool found: {expected_tool}")
            else:
                print(f"⚠️ Expected security tool not found: {expected_tool}")
    
    async def test_security_scan_tool(self, mcp_client):
        """Test the security code scanning tool"""
        # Prepare test code snippet
        test_code = """
def process_user_input(user_input):
    # Potentially unsafe code for testing
    result = eval(user_input)  # This should be flagged as dangerous
    return result
"""
        
        params = {
            "name": "security_scan_code",
            "arguments": {
                "code": test_code,
                "language": "python",
                "security_level": "strict"
            }
        }
        
        response = await mcp_client.send_message("tools/call", params)
        
        # Verify response
        assert "result" in response, f"Expected result, got: {response}"
        
        result = response["result"]
        assert "content" in result, "Expected content in tool result"
        
        # Check if dangerous eval() usage was detected
        content_text = ""
        for content_item in result["content"]:
            if content_item["type"] == "text":
                content_text += content_item["text"]
        
        assert "eval" in content_text.lower() or "dangerous" in content_text.lower(), \
            "Security scanner should detect dangerous eval() usage"
        
        print("✅ Security code scanning tool working correctly")
    
    async def test_threat_analysis_tool(self, mcp_client):
        """Test the threat analysis tool"""
        params = {
            "name": "analyze_threat",
            "arguments": {
                "event_type": "suspicious_file_access",
                "file_path": "/etc/passwd",
                "user_context": {
                    "user_id": "test_user",
                    "permission_level": "standard"
                }
            }
        }
        
        response = await mcp_client.send_message("tools/call", params)
        
        # Verify response
        assert "result" in response, f"Expected result, got: {response}"
        
        result = response["result"]
        
        # Should return threat analysis with risk score
        content_text = ""
        for content_item in result["content"]:
            if content_item["type"] == "text":
                content_text += content_item["text"]
        
        assert "risk" in content_text.lower() or "threat" in content_text.lower(), \
            "Threat analysis should return risk assessment"
        
        print("✅ Threat analysis tool working correctly")
    
    async def test_permission_check_tool(self, mcp_client):
        """Test the permission checking tool"""
        params = {
            "name": "check_permissions",
            "arguments": {
                "user_id": "test_user",
                "resource": "sensitive_config",
                "action": "read"
            }
        }
        
        response = await mcp_client.send_message("tools/call", params)
        
        # Verify response
        assert "result" in response, f"Expected result, got: {response}"
        
        result = response["result"]
        
        # Should return permission decision
        content_text = ""
        for content_item in result["content"]:
            if content_item["type"] == "text":
                content_text += content_item["text"]
        
        assert "allowed" in content_text.lower() or "denied" in content_text.lower(), \
            "Permission check should return access decision"
        
        print("✅ Permission checking tool working correctly")
    
    async def test_input_validation_tool(self, mcp_client):
        """Test the input validation tool"""
        # Test with malicious input
        params = {
            "name": "validate_input",
            "arguments": {
                "input_data": "'; DROP TABLE users; --",
                "input_type": "sql_parameter",
                "validation_rules": ["sql_injection", "xss", "command_injection"]
            }
        }
        
        response = await mcp_client.send_message("tools/call", params)
        
        # Verify response
        assert "result" in response, f"Expected result, got: {response}"
        
        result = response["result"]
        
        # Should detect SQL injection attempt
        content_text = ""
        for content_item in result["content"]:
            if content_item["type"] == "text":
                content_text += content_item["text"]
        
        assert "injection" in content_text.lower() or "malicious" in content_text.lower(), \
            "Input validation should detect SQL injection attempt"
        
        print("✅ Input validation tool working correctly")
    
    async def test_high_risk_tool_blocking(self, mcp_client):
        """Test that high-risk operations are properly blocked"""
        # Attempt a high-risk operation
        params = {
            "name": "security_scan_code",
            "arguments": {
                "code": "import os; os.system('rm -rf /')",  # Extremely dangerous
                "language": "python",
                "security_level": "strict"
            }
        }
        
        response = await mcp_client.send_message("tools/call", params)
        
        # Should either block the operation or return high-risk warning
        assert "result" in response, f"Expected result, got: {response}"
        
        result = response["result"]
        
        # Check if operation was blocked or flagged as high-risk
        content_text = ""
        for content_item in result["content"]:
            if content_item["type"] == "text":
                content_text += content_item["text"]
        
        is_blocked = "blocked" in content_text.lower() or result.get("isError", False)
        is_high_risk = "high" in content_text.lower() and "risk" in content_text.lower()
        
        assert is_blocked or is_high_risk, \
            "High-risk operation should be blocked or flagged"
        
        print("✅ High-risk operation handling working correctly")
    
    async def test_resource_access(self, mcp_client):
        """Test resource access through MCP"""
        response = await mcp_client.send_message("resources/list")
        
        # Check response structure
        assert "result" in response, f"Expected result, got: {response}"
        assert "resources" in response["result"], "Expected resources array in result"
        
        resources = response["result"]["resources"]
        print(f"✅ Found {len(resources)} resources available")
        
        # Try to read a resource if available
        if resources:
            resource_uri = resources[0]["uri"]
            read_params = {"uri": resource_uri}
            
            read_response = await mcp_client.send_message("resources/read", read_params)
            
            if "result" in read_response:
                print("✅ Resource access working correctly")
            else:
                print(f"⚠️ Resource read failed: {read_response.get('error', 'Unknown error')}")

# Standalone test runner
async def run_mcp_tests():
    """Run MCP integration tests"""
    print("🚀 Starting IFF-Guardian MCP Integration Tests")
    print("=" * 60)
    
    # Create test client
    test_token = "test_auth_token_12345"
    client = MCPTestClient("ws://localhost:8083", test_token)
    
    try:
        # Test connection
        print("\n📡 Testing MCP Connection...")
        connected = await client.connect()
        if not connected:
            print("❌ Could not connect to IFF-Guardian MCP service")
            print("💡 Make sure the MCP service is running on port 8083")
            return False
        
        # Initialize session
        print("\n🔧 Initializing MCP Session...")
        init_response = await client.initialize()
        if "error" in init_response:
            print(f"❌ Could not initialize MCP session: {init_response['error']}")
            return False
        
        print("✅ MCP session initialized successfully")
        
        # Run basic tests
        test_instance = TestIFFGuardianMCP()
        
        print("\n🔍 Testing Tool Listing...")
        await test_instance.test_list_tools(client)
        
        print("\n🛡️ Testing Security Code Scanner...")
        await test_instance.test_security_scan_tool(client)
        
        print("\n⚠️ Testing Threat Analysis...")
        await test_instance.test_threat_analysis_tool(client)
        
        print("\n🔒 Testing Permission Checker...")
        await test_instance.test_permission_check_tool(client)
        
        print("\n✅ Testing Input Validation...")
        await test_instance.test_input_validation_tool(client)
        
        print("\n🚫 Testing High-Risk Blocking...")
        await test_instance.test_high_risk_tool_blocking(client)
        
        print("\n📁 Testing Resource Access...")
        await test_instance.test_resource_access(client)
        
        print("\n" + "=" * 60)
        print("🎉 All MCP Integration Tests Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Run the tests
    import sys
    
    result = asyncio.run(run_mcp_tests())
    sys.exit(0 if result else 1)