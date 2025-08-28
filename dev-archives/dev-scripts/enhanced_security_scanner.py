#!/usr/bin/env python3
"""
Enhanced Security Scanner with Context-Aware Detection
Implements Phase 1 improvements from Six Sigma quality analysis to reduce false positives
"""

import ast
import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class CodeContext(Enum):
    """Code context types for better classification"""
    COMMENT = "comment"
    STRING_LITERAL = "string_literal"
    DOCUMENTATION = "documentation"
    TEST_CODE = "test_code"
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    TEMPLATE = "template"
    SAFE_USAGE = "safe_usage"
    EXECUTABLE_CODE = "executable_code"

class IntentCategory(Enum):
    """Code intent categories"""
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    DATA_PROCESSING = "data_processing"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    VALIDATION = "validation"
    SYSTEM_OPERATIONS = "system_operations"
    USER_INTERFACE = "user_interface"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"

@dataclass
class SecurityPattern:
    """Security pattern definition with context awareness"""
    pattern: str
    description: str
    base_severity: int
    safe_contexts: List[CodeContext]
    intent_modifiers: Dict[IntentCategory, float]
    
class EnhancedSecurityScanner:
    """Enhanced security scanner with context awareness and intent classification"""
    
    def __init__(self):
        self.security_patterns = self._load_security_patterns()
        self.intent_keywords = self._load_intent_keywords()
    
    def _load_security_patterns(self) -> List[SecurityPattern]:
        """Load security patterns with context-aware definitions"""
        return [
            SecurityPattern(
                pattern=r'eval\s*\(',
                description="Use of eval() function - code injection risk",
                base_severity=9,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION],
                intent_modifiers={
                    IntentCategory.TESTING: 0.3,
                    IntentCategory.DOCUMENTATION: 0.1,
                    IntentCategory.CONFIGURATION: 0.4,
                    IntentCategory.LOGGING: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'exec\s*\(',
                description="Use of exec() function - code injection risk",
                base_severity=9,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION],
                intent_modifiers={
                    IntentCategory.TESTING: 0.2,
                    IntentCategory.DOCUMENTATION: 0.1,
                    IntentCategory.LOGGING: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'os\.system\s*\(',
                description="Use of os.system() - command injection risk",
                base_severity=8,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION],
                intent_modifiers={
                    IntentCategory.TESTING: 0.3,
                    IntentCategory.SYSTEM_OPERATIONS: 0.5,
                    IntentCategory.DOCUMENTATION: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'subprocess\.call.*shell=True',
                description="Subprocess with shell=True - command injection risk",
                base_severity=7,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.SAFE_USAGE],
                intent_modifiers={
                    IntentCategory.SYSTEM_OPERATIONS: 0.4,
                    IntentCategory.TESTING: 0.3
                }
            ),
            SecurityPattern(
                pattern=r'DROP\s+TABLE',
                description="SQL DROP TABLE - data destruction risk",
                base_severity=8,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION, CodeContext.TEST_CODE],
                intent_modifiers={
                    IntentCategory.TESTING: 0.2,
                    IntentCategory.DATA_PROCESSING: 0.6,
                    IntentCategory.DOCUMENTATION: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'UNION\s+SELECT',
                description="SQL UNION SELECT - injection risk",
                base_severity=8,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION, CodeContext.TEST_CODE],
                intent_modifiers={
                    IntentCategory.TESTING: 0.2,
                    IntentCategory.DATA_PROCESSING: 0.7,
                    IntentCategory.DOCUMENTATION: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'<script',
                description="Script tag - XSS vulnerability risk",
                base_severity=6,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION, CodeContext.TEMPLATE],
                intent_modifiers={
                    IntentCategory.USER_INTERFACE: 0.3,
                    IntentCategory.TESTING: 0.2,
                    IntentCategory.DOCUMENTATION: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'\.\./|\.\.\\\|%2e%2e',
                description="Path traversal pattern",
                base_severity=7,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION, CodeContext.CONFIGURATION],
                intent_modifiers={
                    IntentCategory.CONFIGURATION: 0.2,
                    IntentCategory.TESTING: 0.3,
                    IntentCategory.DOCUMENTATION: 0.1
                }
            ),
            SecurityPattern(
                pattern=r'rm\s+-rf\s+/',
                description="Dangerous file deletion command",
                base_severity=10,
                safe_contexts=[CodeContext.COMMENT, CodeContext.STRING_LITERAL, CodeContext.DOCUMENTATION],
                intent_modifiers={
                    IntentCategory.TESTING: 0.1,
                    IntentCategory.SYSTEM_OPERATIONS: 0.7,
                    IntentCategory.DOCUMENTATION: 0.05
                }
            )
        ]
    
    def _load_intent_keywords(self) -> Dict[IntentCategory, List[str]]:
        """Load keywords that help classify code intent"""
        return {
            IntentCategory.CONFIGURATION: [
                'config', 'settings', 'env', 'environment', 'setup', 'initialize',
                'configure', 'option', 'parameter', 'default', 'DATABASE_URL'
            ],
            IntentCategory.LOGGING: [
                'log', 'logger', 'print', 'debug', 'info', 'warn', 'error',
                'console', 'stdout', 'stderr', 'trace'
            ],
            IntentCategory.DATA_PROCESSING: [
                'json', 'csv', 'pandas', 'data', 'parse', 'serialize',
                'transform', 'process', 'query', 'database', 'sql'
            ],
            IntentCategory.TESTING: [
                'test', 'mock', 'assert', 'expect', 'should', 'spec',
                'unittest', 'pytest', 'jest', 'describe', 'it'
            ],
            IntentCategory.DOCUMENTATION: [
                'example', 'demo', 'tutorial', 'doc', 'readme', 'help',
                'usage', 'sample', 'illustration'
            ],
            IntentCategory.VALIDATION: [
                'validate', 'sanitize', 'clean', 'check', 'verify',
                'filter', 'escape', 'encode'
            ],
            IntentCategory.SYSTEM_OPERATIONS: [
                'system', 'process', 'command', 'shell', 'exec',
                'spawn', 'run', 'call'
            ],
            IntentCategory.USER_INTERFACE: [
                'render', 'display', 'view', 'template', 'html',
                'component', 'widget', 'ui'
            ]
        }
    
    def analyze_code_context(self, code: str, pattern_match: re.Match) -> CodeContext:
        """Analyze the context where a pattern was found"""
        lines = code.split('\n')
        match_pos = pattern_match.start()
        
        # Find which line contains the match
        current_pos = 0
        match_line_idx = 0
        for i, line in enumerate(lines):
            if current_pos <= match_pos < current_pos + len(line) + 1:
                match_line_idx = i
                break
            current_pos += len(line) + 1
        
        if match_line_idx < len(lines):
            line = lines[match_line_idx].strip()
            
            # Check for comments
            if line.startswith('#') or line.startswith('//') or '/*' in line or '*/' in line:
                return CodeContext.COMMENT
            
            # Check for string literals
            if self._is_in_string_literal(code, pattern_match.start()):
                return CodeContext.STRING_LITERAL
            
            # Check for documentation patterns
            if any(doc_word in line.lower() for doc_word in ['example', 'demo', 'tutorial', 'usage']):
                return CodeContext.DOCUMENTATION
            
            # Check for test code
            if any(test_word in line.lower() for test_word in ['test', 'mock', 'assert', 'expect']):
                return CodeContext.TEST_CODE
            
            # Check for configuration
            if any(config_word in line.lower() for config_word in ['config', 'setting', 'env']):
                return CodeContext.CONFIGURATION
            
            # Check for logging
            if any(log_word in line.lower() for log_word in ['log', 'print', 'debug', 'console']):
                return CodeContext.LOGGING
            
            # Check for safe usage patterns (parameterized queries, proper escaping)
            if self._is_safe_usage_pattern(line):
                return CodeContext.SAFE_USAGE
        
        return CodeContext.EXECUTABLE_CODE
    
    def _is_in_string_literal(self, code: str, position: int) -> bool:
        """Check if position is inside a string literal"""
        # Simple check for string boundaries
        before_pos = code[:position]
        
        # Count unescaped quotes
        single_quotes = before_pos.count("'") - before_pos.count("\\'")
        double_quotes = before_pos.count('"') - before_pos.count('\\"')
        
        # If odd number of quotes, we're inside a string
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)
    
    def _is_safe_usage_pattern(self, line: str) -> bool:
        """Check if line contains safe usage patterns"""
        safe_patterns = [
            r'cursor\.execute.*%s',  # Parameterized SQL
            r'\.format\s*\(',       # String formatting
            r'f["\'].*\{[^}]*\}',   # F-strings with variables
            r'json\.loads?\s*\(',   # JSON processing
            r'\.strip\(\)',         # String cleaning
            r'\.replace\s*\(',      # String replacement
            r'with\s+open\s*\(',    # File operations
            r'os\.getenv\s*\(',     # Environment variables
        ]
        
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in safe_patterns)
    
    def classify_code_intent(self, code: str) -> IntentCategory:
        """Classify the overall intent of the code"""
        code_lower = code.lower()
        intent_scores = {category: 0 for category in IntentCategory}
        
        # Score based on keyword presence
        for category, keywords in self.intent_keywords.items():
            for keyword in keywords:
                count = code_lower.count(keyword)
                intent_scores[category] += count
        
        # Additional context clues
        if 'def test_' in code_lower or 'class Test' in code_lower:
            intent_scores[IntentCategory.TESTING] += 5
        
        if any(pattern in code_lower for pattern in ['"""', "'''"]):
            intent_scores[IntentCategory.DOCUMENTATION] += 3
        
        if 'import' in code_lower and ('unittest' in code_lower or 'pytest' in code_lower):
            intent_scores[IntentCategory.TESTING] += 3
        
        # Find category with highest score
        max_score = max(intent_scores.values())
        if max_score == 0:
            return IntentCategory.UNKNOWN
        
        return max(intent_scores, key=intent_scores.get)
    
    def calculate_contextual_risk_score(self, pattern: SecurityPattern, context: CodeContext, intent: IntentCategory) -> float:
        """Calculate risk score adjusted for context and intent"""
        base_risk = pattern.base_severity
        
        # Apply context modifier
        if context in pattern.safe_contexts:
            context_modifier = 0.1  # Very low risk in safe contexts
        elif context == CodeContext.SAFE_USAGE:
            context_modifier = 0.3  # Reduced risk for safe usage patterns
        else:
            context_modifier = 1.0  # Full risk for executable code
        
        # Apply intent modifier
        intent_modifier = pattern.intent_modifiers.get(intent, 1.0)
        
        # Calculate final risk
        final_risk = base_risk * context_modifier * intent_modifier
        
        return max(final_risk, 0.1)  # Minimum risk of 0.1
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Perform enhanced security scan with context awareness"""
        
        # Classify overall code intent
        code_intent = self.classify_code_intent(code)
        
        vulnerabilities = []
        total_risk_score = 0.0
        
        # Check each security pattern
        for pattern_def in self.security_patterns:
            matches = list(re.finditer(pattern_def.pattern, code, re.IGNORECASE))
            
            for match in matches:
                # Analyze context for this specific match
                context = self.analyze_code_context(code, match)
                
                # Calculate contextual risk score
                risk_score = self.calculate_contextual_risk_score(pattern_def, context, code_intent)
                
                # Only report if risk is above threshold
                min_threshold = 1.0 if security_level == "strict" else 2.0
                if risk_score >= min_threshold:
                    vulnerabilities.append({
                        "type": "security_pattern",
                        "pattern": pattern_def.pattern,
                        "description": pattern_def.description,
                        "base_severity": pattern_def.base_severity,
                        "contextual_risk": round(risk_score, 2),
                        "context": context.value,
                        "intent": code_intent.value,
                        "line": self._get_line_number(code, match.start()),
                        "matched_text": match.group()
                    })
                    total_risk_score += risk_score
        
        # Determine overall risk level based on contextual analysis
        if total_risk_score >= 20:
            risk_level = "critical"
        elif total_risk_score >= 10:
            risk_level = "high"
        elif total_risk_score >= 5:
            risk_level = "medium"
        elif total_risk_score >= 1:
            risk_level = "low"
        else:
            risk_level = "safe"
        
        # Enhanced result message with context information
        result_message = f"Enhanced security scan completed for {language} code.\n"
        result_message += f"Code Intent: {code_intent.value.replace('_', ' ').title()}\n"
        result_message += f"Risk Level: {risk_level.upper()} (Contextual Score: {total_risk_score:.2f})\n"
        
        if vulnerabilities:
            result_message += f"\nFound {len(vulnerabilities)} potential security issues:\n"
            for i, vuln in enumerate(vulnerabilities[:5], 1):
                context_info = f" [Context: {vuln['context'].replace('_', ' ').title()}]"
                result_message += f"{i}. {vuln['description']} (Risk: {vuln['contextual_risk']}){context_info}\n"
            
            if len(vulnerabilities) > 5:
                result_message += f"... and {len(vulnerabilities) - 5} more issues\n"
        else:
            result_message += "\n✅ No security vulnerabilities detected in current context."
        
        # Context-aware blocking decision
        is_blocked = False
        if security_level == "strict":
            # Only block if we have high contextual risk in executable code
            critical_executable_risks = [
                v for v in vulnerabilities 
                if v['contextual_risk'] >= 7 and v['context'] == 'executable_code'
            ]
            is_blocked = len(critical_executable_risks) > 0
        
        if is_blocked:
            result_message = f"🚫 OPERATION BLOCKED: {result_message}"
        
        return {
            "message": result_message,
            "risk_score": round(total_risk_score, 2),
            "risk_level": risk_level,
            "vulnerabilities": len(vulnerabilities),
            "code_intent": code_intent.value,
            "is_error": is_blocked,
            "vulnerability_details": vulnerabilities,
            "context_analysis": {
                "total_patterns_found": sum(len(list(re.finditer(p.pattern, code, re.IGNORECASE))) for p in self.security_patterns),
                "patterns_after_context_filter": len(vulnerabilities),
                "false_positive_reduction": True
            }
        }
    
    def _get_line_number(self, code: str, position: int) -> int:
        """Get line number for a given character position"""
        return code[:position].count('\n') + 1

# Example usage and testing
if __name__ == "__main__":
    scanner = EnhancedSecurityScanner()
    
    # Test cases from false positive analysis
    test_cases = [
        {
            "name": "Safe JSON Processing",
            "code": "import json; data = json.loads(user_input); print(data['name'])",
            "expected": "safe"
        },
        {
            "name": "eval() in Comment",
            "code": "# This code mentions eval() but doesn't use it\nresult = calculate_value(x, y)",
            "expected": "safe"
        },
        {
            "name": "eval() in String",
            "code": "help_text = 'Avoid using eval() function for security reasons'",
            "expected": "safe"
        },
        {
            "name": "Actual eval() Usage",
            "code": "result = eval(user_input)",
            "expected": "high_risk"
        }
    ]
    
    print("Enhanced Security Scanner Test Results:")
    print("=" * 50)
    
    for test in test_cases:
        result = scanner.enhanced_security_scan(test["code"])
        print(f"\nTest: {test['name']}")
        print(f"Expected: {test['expected']}")
        print(f"Result: {result['risk_level']} (Score: {result['risk_score']})")
        print(f"Intent: {result['code_intent']}")
        print(f"Vulnerabilities: {result['vulnerabilities']}")
        
        if result["vulnerability_details"]:
            for vuln in result["vulnerability_details"]:
                print(f"  - {vuln['description']} [Context: {vuln['context']}]")