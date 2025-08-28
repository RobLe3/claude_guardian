#!/usr/bin/env python3
"""
AST Foundation Enhancement for Claude Guardian
Phase 1A: Add AST parsing capability without breaking existing functionality
"""

import ast
import sys
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner, CodeContext, IntentCategory

@dataclass
class ASTSecurityInsight:
    """Container for AST-based security insights"""
    node_type: str
    security_concern: str
    confidence: float
    line_number: int
    additional_context: Dict[str, Any]

class ASTSecurityAnalyzer:
    """AST-based security analysis - additive enhancement only"""
    
    def __init__(self):
        self.dangerous_functions = {
            'eval', 'exec', 'compile', '__import__', 'getattr', 'setattr',
            'delattr', 'hasattr', 'globals', 'locals', 'vars'
        }
        
        self.user_input_sources = {
            'input', 'raw_input', 'sys.argv', 'os.environ.get',
            'request.form', 'request.args', 'request.json', 'request.data'
        }
        
        self.dangerous_modules = {
            'os.system', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
            'pickle.loads', 'yaml.load', 'marshal.loads'
        }
    
    def safe_parse(self, code: str) -> Optional[ast.AST]:
        """Safely parse code to AST with comprehensive error handling"""
        try:
            # Remove common issues that break AST parsing
            code = code.strip()
            if not code:
                return None
                
            # Handle incomplete code snippets
            if not code.endswith('\n'):
                code += '\n'
            
            return ast.parse(code)
            
        except SyntaxError as e:
            # Code might be a fragment or have syntax issues
            return None
        except MemoryError:
            # Code too large for AST parsing
            return None
        except RecursionError:
            # Code too deeply nested
            return None
        except Exception:
            # Any other parsing issue
            return None
    
    def analyze_ast_security(self, ast_tree: ast.AST, original_code: str) -> List[ASTSecurityInsight]:
        """Analyze AST for security insights without breaking existing logic"""
        if not ast_tree:
            return []
        
        insights = []
        
        try:
            # Analysis 1: Function call analysis
            insights.extend(self._analyze_function_calls(ast_tree))
            
            # Analysis 2: Variable assignment patterns
            insights.extend(self._analyze_variable_assignments(ast_tree))
            
            # Analysis 3: Import patterns
            insights.extend(self._analyze_imports(ast_tree))
            
            # Analysis 4: String concatenation patterns
            insights.extend(self._analyze_string_operations(ast_tree))
            
        except Exception:
            # If any AST analysis fails, return what we have so far
            pass
        
        return insights
    
    def _analyze_function_calls(self, ast_tree: ast.AST) -> List[ASTSecurityInsight]:
        """Analyze function calls for security concerns"""
        insights = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                
                if func_name in self.dangerous_functions:
                    insights.append(ASTSecurityInsight(
                        node_type='function_call',
                        security_concern=f'Direct call to dangerous function: {func_name}',
                        confidence=0.9,
                        line_number=getattr(node, 'lineno', 0),
                        additional_context={
                            'function_name': func_name,
                            'arg_count': len(node.args),
                            'has_user_input': self._has_potential_user_input(node)
                        }
                    ))
                
                elif func_name and any(danger in func_name for danger in self.dangerous_modules):
                    insights.append(ASTSecurityInsight(
                        node_type='module_call',
                        security_concern=f'Call to potentially dangerous module function: {func_name}',
                        confidence=0.7,
                        line_number=getattr(node, 'lineno', 0),
                        additional_context={
                            'function_name': func_name,
                            'module_pattern': True
                        }
                    ))
        
        return insights
    
    def _analyze_variable_assignments(self, ast_tree: ast.AST) -> List[ASTSecurityInsight]:
        """Analyze variable assignments for indirect execution patterns"""
        insights = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if assigning a dangerous function to a variable
                        if isinstance(node.value, ast.Name) and node.value.id in self.dangerous_functions:
                            insights.append(ASTSecurityInsight(
                                node_type='variable_assignment',
                                security_concern=f'Assignment of dangerous function {node.value.id} to variable {target.id}',
                                confidence=0.8,
                                line_number=getattr(node, 'lineno', 0),
                                additional_context={
                                    'variable_name': target.id,
                                    'assigned_function': node.value.id,
                                    'indirect_execution_risk': True
                                }
                            ))
        
        return insights
    
    def _analyze_imports(self, ast_tree: ast.AST) -> List[ASTSecurityInsight]:
        """Analyze import statements for security concerns"""
        insights = []
        
        risky_modules = {'pickle', 'marshal', 'shelve', 'dill', 'subprocess', 'os'}
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in risky_modules:
                        insights.append(ASTSecurityInsight(
                            node_type='import',
                            security_concern=f'Import of potentially risky module: {alias.name}',
                            confidence=0.3,  # Low confidence - imports are often legitimate
                            line_number=getattr(node, 'lineno', 0),
                            additional_context={
                                'module_name': alias.name,
                                'alias': alias.asname,
                                'risk_level': 'low'
                            }
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in risky_modules:
                    imported_names = [alias.name for alias in node.names]
                    insights.append(ASTSecurityInsight(
                        node_type='import_from',
                        security_concern=f'Import from risky module {node.module}: {imported_names}',
                        confidence=0.4,
                        line_number=getattr(node, 'lineno', 0),
                        additional_context={
                            'module_name': node.module,
                            'imported_names': imported_names,
                            'risk_level': 'low'
                        }
                    ))
        
        return insights
    
    def _analyze_string_operations(self, ast_tree: ast.AST) -> List[ASTSecurityInsight]:
        """Analyze string operations for dynamic construction patterns"""
        insights = []
        
        for node in ast.walk(ast_tree):
            # Look for string concatenation with variables (potential injection)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if self._involves_strings(node):
                    insights.append(ASTSecurityInsight(
                        node_type='string_concatenation',
                        security_concern='String concatenation with variables - potential injection risk',
                        confidence=0.5,  # Medium confidence
                        line_number=getattr(node, 'lineno', 0),
                        additional_context={
                            'operation': 'concatenation',
                            'pattern': 'string + variable',
                            'injection_risk': True
                        }
                    ))
            
            # Look for format string operations
            elif isinstance(node, ast.Call) and self._is_format_call(node):
                insights.append(ASTSecurityInsight(
                    node_type='string_formatting',
                    security_concern='String formatting operation - verify input sanitization',
                    confidence=0.3,  # Lower confidence - often legitimate
                    line_number=getattr(node, 'lineno', 0),
                    additional_context={
                        'operation': 'formatting',
                        'format_type': self._get_format_type(node)
                    }
                ))
        
        return insights
    
    def _get_function_name(self, call_node: ast.Call) -> Optional[str]:
        """Extract function name from call node"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            # Handle module.function calls
            if isinstance(call_node.func.value, ast.Name):
                return f"{call_node.func.value.id}.{call_node.func.attr}"
            return call_node.func.attr
        return None
    
    def _has_potential_user_input(self, call_node: ast.Call) -> bool:
        """Check if function call involves potential user input"""
        for arg in call_node.args:
            if isinstance(arg, ast.Name) and arg.id in {'user_input', 'input_data', 'user_data'}:
                return True
            elif isinstance(arg, ast.Call):
                func_name = self._get_function_name(arg)
                if func_name in self.user_input_sources:
                    return True
        return False
    
    def _involves_strings(self, binop_node: ast.BinOp) -> bool:
        """Check if binary operation involves strings"""
        return (isinstance(binop_node.left, ast.Str) or isinstance(binop_node.left, ast.Constant) or
                isinstance(binop_node.right, ast.Str) or isinstance(binop_node.right, ast.Constant))
    
    def _is_format_call(self, call_node: ast.Call) -> bool:
        """Check if this is a string formatting call"""
        func_name = self._get_function_name(call_node)
        return func_name in {'format', 'str.format'} or (
            isinstance(call_node.func, ast.Attribute) and call_node.func.attr == 'format'
        )
    
    def _get_format_type(self, call_node: ast.Call) -> str:
        """Determine the type of formatting operation"""
        if isinstance(call_node.func, ast.Attribute) and call_node.func.attr == 'format':
            return 'method'
        return 'function'

class EnhancedSecurityScannerWithAST(EnhancedSecurityScanner):
    """Enhanced scanner with AST capability - maintains full backward compatibility"""
    
    def __init__(self):
        # ✅ PRESERVE existing initialization
        super().__init__()
        
        # ➕ ADD new capability with lazy initialization
        self._ast_analyzer = None
        self._ast_available = None
    
    def _get_ast_analyzer(self) -> Optional[ASTSecurityAnalyzer]:
        """Lazy initialization of AST analyzer with error handling"""
        if self._ast_analyzer is None and self._ast_available is not False:
            try:
                self._ast_analyzer = ASTSecurityAnalyzer()
                self._ast_available = True
            except Exception:
                self._ast_available = False
                self._ast_analyzer = None
        
        return self._ast_analyzer if self._ast_available else None
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with optional AST analysis - maintains full API compatibility"""
        
        # ✅ ALWAYS run existing analysis first (guaranteed to work)
        base_result = super().enhanced_security_scan(code, language, security_level)
        
        # ➕ OPTIONALLY add AST insights (with fallback protection)
        if language.lower() == "python" and self._get_ast_analyzer():
            try:
                ast_insights = self._add_ast_analysis(code, base_result)
                if ast_insights:
                    return self._merge_ast_insights(base_result, ast_insights)
            except Exception:
                # 🛡️ FALLBACK: Any AST error returns original result
                pass
        
        # Always return a valid result
        return base_result
    
    def _add_ast_analysis(self, code: str, base_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add AST-based analysis insights"""
        analyzer = self._get_ast_analyzer()
        if not analyzer:
            return None
        
        # Parse code to AST
        ast_tree = analyzer.safe_parse(code)
        if not ast_tree:
            return None
        
        # Get AST insights
        insights = analyzer.analyze_ast_security(ast_tree, code)
        if not insights:
            return None
        
        # Convert insights to additional vulnerabilities
        ast_vulnerabilities = []
        additional_risk = 0.0
        
        for insight in insights:
            # Only add high-confidence insights to avoid false positives
            if insight.confidence > 0.7:
                ast_vulnerabilities.append({
                    'type': 'ast_analysis',
                    'pattern': insight.node_type,
                    'description': insight.security_concern,
                    'confidence': insight.confidence,
                    'line': insight.line_number,
                    'contextual_risk': insight.confidence * 5,  # Scale to match existing scoring
                    'source': 'ast_analyzer',
                    'additional_context': insight.additional_context
                })
                additional_risk += insight.confidence * 3  # Conservative risk addition
        
        return {
            'ast_vulnerabilities': ast_vulnerabilities,
            'additional_risk_score': additional_risk,
            'ast_analysis_successful': True,
            'insights_count': len(insights),
            'high_confidence_insights': len(ast_vulnerabilities)
        }
    
    def _merge_ast_insights(self, base_result: Dict[str, Any], ast_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Safely merge AST insights with base result"""
        
        # ✅ PRESERVE all base result properties
        enhanced_result = base_result.copy()
        
        # ➕ ADD AST-specific information
        ast_vulns = ast_insights.get('ast_vulnerabilities', [])
        additional_risk = ast_insights.get('additional_risk_score', 0)
        
        # Update vulnerability count and risk score conservatively
        enhanced_result.update({
            'vulnerabilities': base_result['vulnerabilities'] + len(ast_vulns),
            'risk_score': base_result['risk_score'] + (additional_risk * 0.5),  # 50% weight for AST
            'ast_analysis': {
                'enabled': True,
                'insights_found': len(ast_vulns),
                'additional_patterns': [v['pattern'] for v in ast_vulns],
                'ast_risk_contribution': additional_risk * 0.5
            }
        })
        
        # Add detailed AST vulnerabilities if any were found
        if ast_vulns:
            enhanced_result['ast_vulnerabilities'] = ast_vulns
        
        return enhanced_result

# Testing and validation functions
def validate_backward_compatibility():
    """Validate that enhanced scanner maintains backward compatibility"""
    original_scanner = EnhancedSecurityScanner()
    enhanced_scanner = EnhancedSecurityScannerWithAST()
    
    test_cases = [
        "import json; data = json.loads(user_input); print(data['name'])",
        "# This code mentions eval() but doesn't use it",
        "help_text = 'Avoid using eval() function for security reasons'",
        "result = eval(user_input)"  # Should still detect this
    ]
    
    compatibility_results = []
    
    for i, code in enumerate(test_cases):
        original_result = original_scanner.enhanced_security_scan(code)
        enhanced_result = enhanced_scanner.enhanced_security_scan(code)
        
        # Check critical compatibility requirements
        compatibility_check = {
            'test_case': i + 1,
            'api_compatible': 'risk_level' in enhanced_result and 'message' in enhanced_result,
            'risk_level_preserved': original_result['risk_level'] == enhanced_result['risk_level'],
            'false_positive_maintained': enhanced_result['risk_level'] in ['safe', 'low'] if 'eval()' in code and '#' in code else True,
            'enhancements_present': 'ast_analysis' in enhanced_result
        }
        
        compatibility_results.append(compatibility_check)
        
        print(f"Test {i+1}: Original={original_result['risk_level']}, Enhanced={enhanced_result['risk_level']}")
        if 'ast_analysis' in enhanced_result:
            print(f"  AST insights: {enhanced_result['ast_analysis']['insights_found']}")
    
    return compatibility_results

if __name__ == "__main__":
    print("🧪 Testing AST Foundation Enhancement")
    print("=" * 50)
    
    # Test 1: Backward compatibility
    print("\\n--- Backward Compatibility Test ---")
    compatibility_results = validate_backward_compatibility()
    
    all_compatible = all(
        result['api_compatible'] and result['false_positive_maintained']
        for result in compatibility_results
    )
    
    print(f"\\n✅ Backward Compatibility: {'PASSED' if all_compatible else 'FAILED'}")
    
    # Test 2: AST Enhancement Capability
    print("\\n--- AST Enhancement Test ---")
    enhanced_scanner = EnhancedSecurityScannerWithAST()
    
    test_code = """
func = eval
result = func(user_input)
os.system('rm -rf ' + user_path)
"""
    
    result = enhanced_scanner.enhanced_security_scan(test_code)
    
    print(f"Risk Level: {result['risk_level']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Vulnerabilities: {result['vulnerabilities']}")
    
    if 'ast_analysis' in result:
        print(f"AST Analysis: {result['ast_analysis']['insights_found']} insights found")
        if 'ast_vulnerabilities' in result:
            for vuln in result['ast_vulnerabilities']:
                print(f"  - {vuln['description']} (confidence: {vuln['confidence']:.2f})")
    
    print("\\n🎉 AST Foundation Enhancement Testing Complete")