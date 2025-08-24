#!/usr/bin/env python3
"""
Simple MCP Service Implementation for Testing Claude Guardian Integration
This provides a basic MCP server implementation for testing purposes
"""

import asyncio
import json
import logging
import re
import time
import websockets
from datetime import datetime
from typing import Dict, Any, Optional, List
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IFFGuardianMCPServer:
    """Simple Claude Guardian MCP Server implementation for testing"""
    
    def __init__(self, host: str = "localhost", port: int = 8083):
        self.host = host
        self.port = port
        self.sessions = {}
        self.server_info = {
            "name": "claude-guardian",
            "version": "1.0.0"
        }
        self.capabilities = {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True},
            "logging": {}
        }
        
        # Load security tools registry
        self.security_tools = self.load_security_tools()
        self.security_resources = self.load_security_resources()
    
    def load_security_tools(self) -> List[Dict[str, Any]]:
        """Load security tools configuration"""
        return [
            {
                "name": "security_scan_code",
                "description": "Scans code for security vulnerabilities and dangerous patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to scan"},
                        "language": {"type": "string", "description": "Programming language"},
                        "security_level": {"type": "string", "enum": ["strict", "moderate", "relaxed"]}
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "analyze_threat",
                "description": "Analyzes potential security threats and calculates risk scores",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string", "description": "Type of security event"},
                        "file_path": {"type": "string", "description": "File path involved"},
                        "user_context": {"type": "object", "description": "User context"}
                    },
                    "required": ["event_type"]
                }
            },
            {
                "name": "check_permissions",
                "description": "Checks user permissions for resources and actions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"},
                        "resource": {"type": "string", "description": "Resource name"},
                        "action": {"type": "string", "enum": ["read", "write", "execute", "delete"]}
                    },
                    "required": ["user_id", "resource", "action"]
                }
            },
            {
                "name": "validate_input",
                "description": "Validates user input for security threats",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_data": {"type": "string", "description": "Input to validate"},
                        "input_type": {"type": "string", "enum": ["sql_parameter", "web_form", "command_line"]},
                        "validation_rules": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["input_data", "input_type"]
                }
            },
            {
                "name": "monitor_execution",
                "description": "Monitors code execution for suspicious behavior",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "execution_id": {"type": "string", "description": "Execution ID to monitor"},
                        "monitoring_duration": {"type": "integer", "default": 30},
                        "alert_threshold": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["execution_id"]
                }
            }
        ]
    
    def load_security_resources(self) -> List[Dict[str, Any]]:
        """Load security resources configuration"""
        return [
            {
                "uri": "iff://security/policies/default",
                "name": "Default Security Policies",
                "description": "Default security policies and configurations",
                "mimeType": "application/json"
            },
            {
                "uri": "iff://security/threat-intelligence/feeds",
                "name": "Threat Intelligence Feeds",
                "description": "Current threat intelligence data",
                "mimeType": "application/json"
            },
            {
                "uri": "iff://security/audit-logs/recent",
                "name": "Recent Security Events",
                "description": "Recent security events and audit logs",
                "mimeType": "application/json"
            }
        ]
    
    async def handle_client(self, websocket):
        """Handle MCP client WebSocket connection"""
        client_id = f"client_{int(time.time() * 1000)}"
        logger.info(f"New MCP client connected: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    logger.info(f"Received raw message: {message}")
                    data = json.loads(message)
                    logger.info(f"Parsed message data: {data}")
                    
                    response = await self.handle_message(client_id, data)
                    
                    if response:
                        response_json = json.dumps(response)
                        logger.info(f"Sending response: {response_json}")
                        await websocket.send(response_json)
                    else:
                        logger.info("No response to send")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MCP client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}", exc_info=True)
        finally:
            if client_id in self.sessions:
                del self.sessions[client_id]
    
    async def handle_message(self, client_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle individual MCP protocol messages"""
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(f"Received {method} from {client_id} with params: {params}")
        
        try:
            if method == "initialize":
                return await self.handle_initialize(request_id, params)
            elif method == "initialized":
                return None  # No response needed
            elif method == "tools/list":
                return await self.handle_tools_list(request_id, params)
            elif method == "tools/call":
                return await self.handle_tool_call(request_id, params)
            elif method == "resources/list":
                return await self.handle_resources_list(request_id, params)
            elif method == "resources/read":
                return await self.handle_resource_read(request_id, params)
            else:
                logger.warning(f"Unknown method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize message"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": self.server_info,
                "capabilities": self.capabilities
            }
        }
    
    async def handle_tools_list(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list message"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.security_tools
            }
        }
    
    async def handle_tool_call(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call message with security analysis"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Find the tool
        tool = next((t for t in self.security_tools if t["name"] == tool_name), None)
        if not tool:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        # Execute the security tool
        result = await self.execute_security_tool(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result["message"]
                    }
                ],
                "isError": result.get("is_error", False)
            }
        }
    
    async def execute_security_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a security tool and return results"""
        
        if tool_name == "security_scan_code":
            return await self.scan_code_security(arguments)
        elif tool_name == "analyze_threat":
            return await self.analyze_threat(arguments)
        elif tool_name == "check_permissions":
            return await self.check_permissions(arguments)
        elif tool_name == "validate_input":
            return await self.validate_input(arguments)
        elif tool_name == "monitor_execution":
            return await self.monitor_execution(arguments)
        else:
            return {
                "message": f"Unknown security tool: {tool_name}",
                "is_error": True
            }
    
    async def scan_code_security(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Scan code for security vulnerabilities with enhanced context awareness"""
        code = arguments.get("code", "")
        language = arguments.get("language", "unknown")
        security_level = arguments.get("security_level", "moderate")
        
        # Import enhanced scanner locally to avoid import issues
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from enhanced_security_scanner import EnhancedSecurityScanner
            scanner = EnhancedSecurityScanner()
            return scanner.enhanced_security_scan(code, language, security_level)
        except ImportError:
            # Fallback to basic scanning if enhanced scanner is not available
            logger.warning("Enhanced security scanner not available, using basic scanner")
            return await self.basic_scan_code_security(code, language, security_level)
    
    async def basic_scan_code_security(self, code: str, language: str, security_level: str) -> Dict[str, Any]:
        """Basic security scan (fallback method)"""
        vulnerabilities = []
        risk_score = 0
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'eval\s*\(', "Use of eval() is dangerous - code injection risk", 9),
            (r'exec\s*\(', "Use of exec() is dangerous - code injection risk", 9),
            (r'os\.system\s*\(', "Use of os.system() is dangerous - command injection risk", 8),
            (r'subprocess\.call.*shell=True', "Shell=True in subprocess is risky", 7),
            (r'rm\s+-rf\s+/', "Dangerous file deletion command detected", 10),
            (r'DROP\s+TABLE', "SQL DROP TABLE detected - potential data loss", 8),
            (r'DELETE\s+FROM.*WHERE.*1=1', "Dangerous SQL DELETE pattern", 9),
            (r'<script', "Potential XSS vulnerability", 6),
            (r'innerHTML\s*=', "Direct innerHTML assignment - XSS risk", 5)
        ]
        
        for pattern, message, severity in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                vulnerabilities.append({
                    "type": "dangerous_pattern",
                    "message": message,
                    "severity": severity,
                    "pattern": pattern
                })
                risk_score += severity
        
        # Determine overall risk level
        if risk_score >= 25:
            risk_level = "critical"
        elif risk_score >= 15:
            risk_level = "high"
        elif risk_score >= 8:
            risk_level = "medium"
        elif risk_score > 0:
            risk_level = "low"
        else:
            risk_level = "safe"
        
        result_message = f"Security scan completed for {language} code.\n"
        result_message += f"Risk Level: {risk_level.upper()} (Score: {risk_score})\n"
        
        if vulnerabilities:
            result_message += f"Found {len(vulnerabilities)} security issues:\n"
            for i, vuln in enumerate(vulnerabilities[:5], 1):  # Limit to first 5
                result_message += f"{i}. {vuln['message']} (Severity: {vuln['severity']})\n"
        else:
            result_message += "No obvious security vulnerabilities detected."
        
        # Block critical operations
        is_blocked = risk_level == "critical" and security_level == "strict"
        if is_blocked:
            result_message = f"🚫 OPERATION BLOCKED: {result_message}"
        
        return {
            "message": result_message,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "vulnerabilities": len(vulnerabilities),
            "is_error": is_blocked
        }
    
    async def analyze_threat(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security threat"""
        event_type = arguments.get("event_type", "unknown")
        file_path = arguments.get("file_path", "")
        user_context = arguments.get("user_context", {})
        
        # Calculate risk score based on event type and context
        risk_factors = {
            "suspicious_file_access": 7,
            "unauthorized_command": 8,
            "privilege_escalation": 9,
            "data_exfiltration": 10,
            "malware_detected": 10,
            "unknown": 3
        }
        
        base_risk = risk_factors.get(event_type, 3)
        
        # Adjust risk based on file path
        if file_path:
            if "/etc/passwd" in file_path or "/etc/shadow" in file_path:
                base_risk += 3
            elif file_path.startswith("/etc/"):
                base_risk += 2
            elif file_path.startswith("/var/log/"):
                base_risk += 1
        
        # Adjust risk based on user context
        user_level = user_context.get("permission_level", "standard")
        if user_level == "admin":
            base_risk -= 1  # Admin access is expected
        elif user_level == "guest":
            base_risk += 2  # Guest doing sensitive operations is suspicious
        
        risk_score = min(base_risk, 10)  # Cap at 10
        
        if risk_score >= 8:
            risk_level = "high"
            recommendation = "Immediate investigation required"
        elif risk_score >= 6:
            risk_level = "medium"
            recommendation = "Monitor closely and investigate if pattern continues"
        elif risk_score >= 3:
            risk_level = "low"
            recommendation = "Log for audit trail"
        else:
            risk_level = "minimal"
            recommendation = "Normal activity"
        
        result_message = f"Threat Analysis Results:\n"
        result_message += f"Event: {event_type}\n"
        result_message += f"Risk Level: {risk_level.upper()} (Score: {risk_score}/10)\n"
        result_message += f"Recommendation: {recommendation}\n"
        
        if file_path:
            result_message += f"File Path: {file_path}\n"
        
        if user_context:
            user_id = user_context.get("user_id", "unknown")
            result_message += f"User: {user_id} ({user_level})\n"
        
        return {
            "message": result_message,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation
        }
    
    async def check_permissions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Check user permissions"""
        user_id = arguments.get("user_id", "")
        resource = arguments.get("resource", "")
        action = arguments.get("action", "")
        
        # Simple permission logic for testing
        # In reality, this would check against a proper RBAC system
        permissions = {
            "test_user": {
                "public_resource": ["read"],
                "user_data": ["read", "write"],
                "sensitive_config": []  # No access
            },
            "admin_user": {
                "public_resource": ["read", "write", "execute"],
                "user_data": ["read", "write", "execute"],
                "sensitive_config": ["read", "write"]
            }
        }
        
        user_perms = permissions.get(user_id, {})
        allowed_actions = user_perms.get(resource, [])
        access_granted = action in allowed_actions
        
        result_message = f"Permission Check Results:\n"
        result_message += f"User: {user_id}\n"
        result_message += f"Resource: {resource}\n"
        result_message += f"Action: {action}\n"
        result_message += f"Access: {'GRANTED' if access_granted else 'DENIED'}\n"
        
        if access_granted:
            result_message += "✅ User has permission to perform this action."
        else:
            result_message += "🚫 Access denied. User lacks required permissions."
            
        return {
            "message": result_message,
            "access_granted": access_granted,
            "user_permissions": allowed_actions
        }
    
    async def validate_input(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input for security threats"""
        input_data = arguments.get("input_data", "")
        input_type = arguments.get("input_type", "")
        validation_rules = arguments.get("validation_rules", ["sql_injection", "xss"])
        
        threats_found = []
        
        # SQL Injection patterns
        if "sql_injection" in validation_rules:
            sql_patterns = [
                r"[';\"]\s*;\s*DROP\s+TABLE",
                r"[';\"]\s*;\s*DELETE\s+FROM",
                r"[';\"]\s*;\s*INSERT\s+INTO",
                r"[';\"]\s*;\s*UPDATE\s+.*SET",
                r"[';\"]\s*OR\s+['\"]?1['\"]?\s*=\s*['\"]?1",
                r"[';\"]\s*UNION\s+SELECT"
            ]
            for pattern in sql_patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    threats_found.append("SQL Injection attempt detected")
                    break
        
        # XSS patterns
        if "xss" in validation_rules:
            xss_patterns = [
                r"<script.*?>.*?</script>",
                r"javascript\s*:",
                r"on\w+\s*=",
                r"<iframe.*?>",
                r"<object.*?>"
            ]
            for pattern in xss_patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    threats_found.append("Cross-Site Scripting (XSS) attempt detected")
                    break
        
        # Command Injection patterns
        if "command_injection" in validation_rules:
            cmd_patterns = [
                r"[;&|`$]",
                r"\|\s*\w+",
                r"&&\s*\w+",
                r";\s*\w+"
            ]
            for pattern in cmd_patterns:
                if re.search(pattern, input_data):
                    threats_found.append("Command injection attempt detected")
                    break
        
        is_safe = len(threats_found) == 0
        
        result_message = f"Input Validation Results:\n"
        result_message += f"Input Type: {input_type}\n"
        result_message += f"Validation Rules: {', '.join(validation_rules)}\n"
        result_message += f"Status: {'SAFE' if is_safe else 'DANGEROUS'}\n"
        
        if threats_found:
            result_message += f"Threats Detected:\n"
            for i, threat in enumerate(threats_found, 1):
                result_message += f"{i}. {threat}\n"
        else:
            result_message += "✅ No security threats detected in input."
        
        return {
            "message": result_message,
            "is_safe": is_safe,
            "threats_found": threats_found,
            "is_error": not is_safe
        }
    
    async def monitor_execution(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor execution for security violations"""
        execution_id = arguments.get("execution_id", "")
        duration = arguments.get("monitoring_duration", 30)
        threshold = arguments.get("alert_threshold", "medium")
        
        # Simulate monitoring results
        suspicious_activities = [
            "Network connection to suspicious IP",
            "File system access to sensitive directory",
            "Process spawn with elevated privileges"
        ]
        
        # Random selection for demo
        import random
        detected_count = random.randint(0, len(suspicious_activities))
        detected = suspicious_activities[:detected_count]
        
        result_message = f"Execution Monitoring Results:\n"
        result_message += f"Execution ID: {execution_id}\n"
        result_message += f"Monitoring Duration: {duration} seconds\n"
        result_message += f"Alert Threshold: {threshold}\n"
        
        if detected:
            result_message += f"⚠️ Suspicious Activities Detected ({len(detected)}):\n"
            for i, activity in enumerate(detected, 1):
                result_message += f"{i}. {activity}\n"
        else:
            result_message += "✅ No suspicious activities detected during monitoring."
        
        return {
            "message": result_message,
            "suspicious_activities": len(detected),
            "activities_detected": detected,
            "monitoring_duration": duration
        }
    
    async def handle_resources_list(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list message"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.security_resources
            }
        }
    
    async def handle_resource_read(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read message"""
        uri = params.get("uri", "")
        
        # Mock resource content based on URI
        if "policies" in uri:
            content = {
                "default_security_level": "moderate",
                "threat_detection": True,
                "auto_block_critical": True,
                "audit_logging": True
            }
        elif "threat-intelligence" in uri:
            content = {
                "active_threats": 1247,
                "last_update": datetime.now().isoformat(),
                "threat_sources": ["malware_feeds", "botnet_tracking", "vulnerability_db"]
            }
        elif "audit-logs" in uri:
            content = {
                "recent_events": 156,
                "security_incidents": 3,
                "last_24h_summary": "Normal activity with 3 low-severity incidents"
            }
        else:
            content = {"error": "Resource not found"}
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content, indent=2)
                    }
                ]
            }
        }
    
    async def start_server(self):
        """Start the MCP WebSocket server"""
        logger.info(f"Starting Claude Guardian MCP Server on {self.host}:{self.port}")
        
        start_server = websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        await start_server
        logger.info(f"✅ Claude Guardian MCP Server running on ws://{self.host}:{self.port}")
        
        # Keep the server running
        await asyncio.Future()  # Run forever

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude Guardian MCP Test Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8083, help="Port to bind to")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    server = IFFGuardianMCPServer(args.host, args.port)
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Claude Guardian MCP Test Server")
    print("================================")
    asyncio.run(main())