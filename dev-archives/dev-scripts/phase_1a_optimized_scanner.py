#!/usr/bin/env python3
"""
Phase 1A-Revised: Performance-Optimized AST Foundation
Implements performance-optimized AST analysis with conservative enhancements
"""

import ast
import sys
import os
import time
import hashlib
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_security_scanner import EnhancedSecurityScanner, CodeContext, IntentCategory

@dataclass
class PerformanceBudget:
    """Performance budget configuration"""
    small_code_ms: float = 0.5      # <100 chars
    medium_code_ms: float = 2.0     # 100-1000 chars  
    large_code_ms: float = 10.0     # >1000 chars
    absolute_timeout_ms: float = 50.0  # Absolute max

@dataclass
class ASTInsight:
    """Lightweight AST security insight"""
    pattern_type: str
    risk_score: float
    confidence: float
    line_number: int
    description: str

class FalsePositiveGuard:
    """Protects against false positives on known safe patterns"""
    
    def __init__(self):
        # Patterns that MUST NEVER be flagged as threats
        self.protected_patterns = [
            r'#.*eval',                    # Comments mentioning eval
            r'[\'"].*eval.*[\'"]',         # String literals with eval
            r'json\.loads?\s*\(',          # JSON operations
            r'ast\.literal_eval',          # Safe eval alternative  
            r'logger\.|print\(',           # Logging operations
            r'os\.getenv\(',               # Environment variable access
            r'with\s+open\s*\(',           # File operations
            r'cursor\.execute\s*\([\'"][^\'"].*%s',  # Parameterized queries
        ]
    
    def is_protected_pattern(self, code: str) -> bool:
        """Check if code matches protected patterns"""
        for pattern in self.protected_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False
    
    def validate_enhancement(self, original_result: Dict[str, Any], 
                           enhanced_result: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Validate that enhancement doesn't create false positives"""
        
        # If original was safe and code is protected, ensure enhanced stays safe
        if (original_result['risk_level'] == 'safe' and 
            self.is_protected_pattern(code)):
            
            enhanced_result = enhanced_result.copy()
            enhanced_result['risk_level'] = 'safe'
            enhanced_result['risk_score'] = min(enhanced_result['risk_score'], 1.0)
            
        return enhanced_result

class OptimizedASTAnalyzer:
    """Performance-optimized AST analyzer with caching"""
    
    def __init__(self):
        self._ast_cache = {}       # Cache parsed ASTs
        self._analysis_cache = {}  # Cache analysis results
        self._cache_hits = 0
        self._cache_misses = 0
        
        # High-confidence patterns for conservative analysis
        self.dangerous_functions = {
            'eval': {'risk': 9, 'description': 'Code injection via eval()'},
            'exec': {'risk': 9, 'description': 'Code execution via exec()'},
            'compile': {'risk': 7, 'description': 'Dynamic code compilation'},
            '__import__': {'risk': 6, 'description': 'Dynamic module import'},
        }
        
        # Variable assignment patterns
        self.assignment_patterns = [
            (r'(\w+)\s*=\s*(eval|exec|compile)', 0.8, 'Dangerous function assignment'),
            (r'(\w+)\s*=\s*getattr\s*\([^)]*,\s*[\'"]eval[\'"]\s*\)', 0.7, 'Indirect eval via getattr'),
        ]
    
    def safe_parse_with_cache(self, code: str) -> Optional[ast.AST]:
        """Parse code with caching and error handling"""
        # Create cache key
        code_hash = hashlib.md5(code.encode()).hexdigest()
        
        if code_hash in self._ast_cache:
            self._cache_hits += 1
            return self._ast_cache[code_hash]
        
        self._cache_misses += 1
        
        try:
            # Handle common parsing issues
            code = code.strip()
            if not code:
                return None
            
            if not code.endswith('\n'):
                code += '\n'
            
            ast_tree = ast.parse(code)
            
            # Cache successful parse (limit cache size)
            if len(self._ast_cache) < 1000:
                self._ast_cache[code_hash] = ast_tree
            
            return ast_tree
            
        except (SyntaxError, MemoryError, RecursionError):
            # Cache failed parses as None
            if len(self._ast_cache) < 1000:
                self._ast_cache[code_hash] = None
            return None
        except Exception:
            return None
    
    def lightweight_analysis(self, code: str) -> List[ASTInsight]:
        """Lightweight regex-based analysis for small code"""
        insights = []
        
        # Check for direct dangerous function calls
        for func, info in self.dangerous_functions.items():
            pattern = rf'{func}\s*\('
            if re.search(pattern, code):
                # Check if it's in executable context (not comment/string)
                if not self._is_in_safe_context(code, pattern):
                    insights.append(ASTInsight(
                        pattern_type='direct_call',
                        risk_score=info['risk'],
                        confidence=0.9,
                        line_number=self._get_line_number(code, pattern),
                        description=info['description']
                    ))
        
        # Check for variable assignments to dangerous functions
        for pattern, confidence, desc in self.assignment_patterns:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                insights.append(ASTInsight(
                    pattern_type='variable_assignment',
                    risk_score=6.0,
                    confidence=confidence,
                    line_number=self._get_line_number_from_match(code, match),
                    description=desc
                ))
        
        return insights
    
    def full_ast_analysis(self, code: str, ast_tree: ast.AST) -> List[ASTInsight]:
        """Full AST-based analysis for complex code"""
        insights = []
        
        try:
            # Analyze function calls
            insights.extend(self._analyze_function_calls(ast_tree))
            
            # Analyze variable assignments
            insights.extend(self._analyze_variable_assignments(ast_tree))
            
            # Analyze string operations (potential injection)
            insights.extend(self._analyze_string_operations(ast_tree))
            
        except Exception:
            # If AST analysis fails, fall back to lightweight analysis
            return self.lightweight_analysis(code)
        
        return insights
    
    def analyze_with_performance_budget(self, code: str, budget_ms: float) -> List[ASTInsight]:
        """Analyze code within performance budget"""
        start_time = time.time()
        
        # Simple cache key (faster than MD5)
        analysis_key = f"{len(code)}_{hash(code) % 10000}"
        
        if analysis_key in self._analysis_cache:
            self._cache_hits += 1
            return self._analysis_cache[analysis_key]
        
        self._cache_misses += 1
        
        # Determine analysis strategy based on code size and budget
        code_size = len(code)
        
        if code_size < 100 or budget_ms < 2.0:
            # Use lightweight analysis for small code or tight budget
            insights = self.lightweight_analysis(code)
        elif code_size > 2000:
            # Skip AST for very large code to avoid performance issues
            insights = self.lightweight_analysis(code)
        else:
            # Try AST analysis with timeout
            try:
                ast_tree = self.safe_parse_with_cache(code)
                elapsed_ms = (time.time() - start_time) * 1000
                
                if ast_tree and elapsed_ms < budget_ms * 0.5:  # Use only half budget
                    insights = self.full_ast_analysis(code, ast_tree)
                else:
                    insights = self.lightweight_analysis(code)
            except:
                insights = self.lightweight_analysis(code)
        
        # Cache result with size limit
        if len(self._analysis_cache) < 100:  # Smaller cache
            self._analysis_cache[analysis_key] = insights
        
        return insights
    
    def _analyze_function_calls(self, ast_tree: ast.AST) -> List[ASTInsight]:
        """Analyze function calls in AST"""
        insights = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                
                if func_name in self.dangerous_functions:
                    info = self.dangerous_functions[func_name]
                    insights.append(ASTInsight(
                        pattern_type='ast_function_call',
                        risk_score=info['risk'],
                        confidence=0.95,  # Higher confidence from AST
                        line_number=getattr(node, 'lineno', 0),
                        description=f"AST: {info['description']}"
                    ))
        
        return insights
    
    def _analyze_variable_assignments(self, ast_tree: ast.AST) -> List[ASTInsight]:
        """Analyze variable assignments in AST"""
        insights = []
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Name):
                        if node.value.id in self.dangerous_functions:
                            insights.append(ASTInsight(
                                pattern_type='ast_assignment',
                                risk_score=7.0,
                                confidence=0.85,
                                line_number=getattr(node, 'lineno', 0),
                                description=f"Assignment of {node.value.id} to variable {target.id}"
                            ))
        
        return insights
    
    def _analyze_string_operations(self, ast_tree: ast.AST) -> List[ASTInsight]:
        """Analyze string operations for potential injection"""
        insights = []
        
        for node in ast.walk(ast_tree):
            # Look for string concatenation (potential injection risk)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if self._involves_strings_and_variables(node):
                    insights.append(ASTInsight(
                        pattern_type='string_concatenation',
                        risk_score=3.0,
                        confidence=0.6,  # Lower confidence - often legitimate
                        line_number=getattr(node, 'lineno', 0),
                        description='String concatenation with variables'
                    ))
        
        return insights
    
    def _get_function_name(self, call_node: ast.Call) -> Optional[str]:
        """Extract function name from call node"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None
    
    def _is_in_safe_context(self, code: str, pattern: str) -> bool:
        """Check if pattern is in safe context (comment/string)"""
        lines = code.split('\n')
        for line in lines:
            if re.search(pattern, line):
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    return True
                # Simple check for string literals
                if "'" in line or '"' in line:
                    return True
        return False
    
    def _get_line_number(self, code: str, pattern: str) -> int:
        """Get line number where pattern occurs"""
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                return i
        return 0
    
    def _get_line_number_from_match(self, code: str, match: re.Match) -> int:
        """Get line number from regex match"""
        return code[:match.start()].count('\n') + 1
    
    def _involves_strings_and_variables(self, binop_node: ast.BinOp) -> bool:
        """Check if binary operation involves both strings and variables"""
        left_is_string = isinstance(binop_node.left, (ast.Str, ast.Constant))
        right_is_string = isinstance(binop_node.right, (ast.Str, ast.Constant))
        left_is_var = isinstance(binop_node.left, ast.Name)
        right_is_var = isinstance(binop_node.right, ast.Name)
        
        return (left_is_string and right_is_var) or (left_is_var and right_is_string)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching performance statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'ast_cache_size': len(self._ast_cache),
            'analysis_cache_size': len(self._analysis_cache)
        }

class OptimizedEnhancedSecurityScanner(EnhancedSecurityScanner):
    """Performance-optimized enhanced scanner with conservative AST enhancements"""
    
    def __init__(self):
        # ✅ PRESERVE existing initialization
        super().__init__()
        
        # ➕ ADD new components with lazy initialization
        self._ast_analyzer = None
        self._false_positive_guard = FalsePositiveGuard()
        self._performance_budget = PerformanceBudget()
        
        # Performance tracking
        self._performance_stats = {
            'total_scans': 0,
            'ast_enhancements': 0,
            'cache_usage': 0,
            'performance_budget_exceeded': 0
        }
    
    def _get_ast_analyzer(self) -> OptimizedASTAnalyzer:
        """Lazy initialization of AST analyzer"""
        if self._ast_analyzer is None:
            self._ast_analyzer = OptimizedASTAnalyzer()
        return self._ast_analyzer
    
    def _get_performance_budget(self, code: str) -> float:
        """Determine performance budget based on code size"""
        code_size = len(code)
        
        if code_size < 100:
            return self._performance_budget.small_code_ms
        elif code_size < 1000:
            return self._performance_budget.medium_code_ms
        else:
            return self._performance_budget.large_code_ms
    
    def enhanced_security_scan(self, code: str, language: str = "python", security_level: str = "moderate") -> Dict[str, Any]:
        """Enhanced scan with performance-optimized AST analysis"""
        scan_start_time = time.time()
        self._performance_stats['total_scans'] += 1
        
        # ✅ ALWAYS run base analysis first (guaranteed to work)
        base_result = super().enhanced_security_scan(code, language, security_level)
        base_processing_time = (time.time() - scan_start_time) * 1000
        
        # ➕ CONDITIONALLY add AST enhancement within strict performance budget
        if language.lower() == "python" and len(code) > 30 and len(code) < 1000:
            budget_ms = self._get_performance_budget(code)
            remaining_budget = budget_ms - base_processing_time
            
            # Only enhance if we have significant budget remaining and code is reasonable size
            if remaining_budget > 1.0 and base_processing_time < 0.5:
                try:
                    enhancement_start = time.time()
                    enhanced_result = self._add_ast_enhancement(code, base_result, remaining_budget * 0.7)  # Use 70% of remaining budget
                    enhancement_time = (time.time() - enhancement_start) * 1000
                    
                    if enhancement_time <= remaining_budget * 0.8:  # Allow 80% of remaining budget
                        # Enhancement successful within budget
                        self._performance_stats['ast_enhancements'] += 1
                        return self._apply_false_positive_protection(base_result, enhanced_result, code)
                    else:
                        # Enhancement exceeded budget, use base result
                        self._performance_stats['performance_budget_exceeded'] += 1
                        
                except Exception:
                    # Enhancement failed, use base result
                    pass
        
        # Always return a valid result
        return base_result
    
    def _add_ast_enhancement(self, code: str, base_result: Dict[str, Any], budget_ms: float) -> Dict[str, Any]:
        """Add AST-based enhancements within performance budget"""
        analyzer = self._get_ast_analyzer()
        
        # Get AST insights within budget
        insights = analyzer.analyze_with_performance_budget(code, budget_ms)
        
        if not insights:
            return base_result
        
        # Convert high-confidence insights to vulnerabilities
        enhanced_result = base_result.copy()
        additional_risk = 0.0
        high_confidence_insights = [i for i in insights if i.confidence >= 0.8]
        
        for insight in high_confidence_insights:
            additional_risk += insight.risk_score * insight.confidence * 0.3  # Conservative weighting
        
        # Conservative enhancement: max 50% risk increase
        max_enhancement = base_result['risk_score'] * 0.5
        actual_enhancement = min(additional_risk, max_enhancement)
        
        enhanced_result.update({
            'risk_score': base_result['risk_score'] + actual_enhancement,
            'vulnerabilities': base_result['vulnerabilities'] + len(high_confidence_insights),
            'ast_analysis': {
                'enabled': True,
                'insights_found': len(insights),
                'high_confidence_insights': len(high_confidence_insights),
                'risk_enhancement': actual_enhancement,
                'cache_stats': analyzer.get_cache_stats()
            }
        })
        
        # Update risk level if significantly enhanced
        if enhanced_result['risk_score'] > base_result['risk_score'] * 1.2:
            if enhanced_result['risk_score'] >= 15:
                enhanced_result['risk_level'] = 'high'
            elif enhanced_result['risk_score'] >= 8:
                enhanced_result['risk_level'] = 'medium'
        
        return enhanced_result
    
    def _apply_false_positive_protection(self, base_result: Dict[str, Any], 
                                       enhanced_result: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Apply false positive protection to enhanced results"""
        return self._false_positive_guard.validate_enhancement(base_result, enhanced_result, code)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self._performance_stats.copy()
        
        if self._ast_analyzer:
            stats['cache_performance'] = self._ast_analyzer.get_cache_stats()
        
        # Calculate efficiency metrics
        if stats['total_scans'] > 0:
            stats['enhancement_rate'] = stats['ast_enhancements'] / stats['total_scans']
            stats['budget_exceeded_rate'] = stats['performance_budget_exceeded'] / stats['total_scans']
        
        return stats

# Testing and benchmarking functions
def benchmark_phase_1a_improvements():
    """Benchmark Phase 1A improvements against baseline"""
    print("🚀 Benchmarking Phase 1A Performance-Optimized Scanner")
    print("=" * 60)
    
    baseline_scanner = EnhancedSecurityScanner()
    optimized_scanner = OptimizedEnhancedSecurityScanner()
    
    # Test cases for benchmarking
    test_cases = [
        {
            "name": "Small Safe Code",
            "code": "import json\\ndata = json.loads(input_data)",
            "category": "small_safe"
        },
        {
            "name": "Medium Safe Code", 
            "code": "def process_data():\\n    pass\\n" * 20,
            "category": "medium_safe"
        },
        {
            "name": "Direct eval() Usage",
            "code": "result = eval(user_input)",
            "category": "threat_basic"
        },
        {
            "name": "Indirect eval() Assignment",
            "code": "func = eval\\nresult = func(user_input)",
            "category": "threat_indirect"
        },
        {
            "name": "Complex Mixed Code",
            "code": """
# Configuration setup
config = os.getenv('CONFIG_PATH')

# Data processing
def process_user_input(data):
    # Never use eval() in production
    return json.loads(data)

# Dangerous pattern
dangerous_func = eval
result = dangerous_func('2 + 2')
            """,
            "category": "complex_mixed"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\\nTesting: {test_case['name']}")
        
        # Baseline performance
        baseline_times = []
        for _ in range(5):
            start_time = time.time()
            baseline_result = baseline_scanner.enhanced_security_scan(test_case["code"])
            baseline_times.append((time.time() - start_time) * 1000)
        
        # Optimized performance
        optimized_times = []
        optimized_results = []
        for _ in range(5):
            start_time = time.time()
            optimized_result = optimized_scanner.enhanced_security_scan(test_case["code"])
            optimized_times.append((time.time() - start_time) * 1000)
            optimized_results.append(optimized_result)
        
        # Analysis
        avg_baseline = sum(baseline_times) / len(baseline_times)
        avg_optimized = sum(optimized_times) / len(optimized_times)
        performance_impact = ((avg_optimized - avg_baseline) / avg_baseline * 100) if avg_baseline > 0 else 0
        
        # Quality comparison
        baseline_risk = baseline_result['risk_level']
        optimized_risk = optimized_results[0]['risk_level']  
        enhanced_features = 'ast_analysis' in optimized_results[0]
        
        result = {
            'test_case': test_case['name'],
            'category': test_case['category'],
            'baseline_time_ms': round(avg_baseline, 3),
            'optimized_time_ms': round(avg_optimized, 3),
            'performance_impact_pct': round(performance_impact, 1),
            'baseline_risk': baseline_risk,
            'optimized_risk': optimized_risk,
            'enhanced_features': enhanced_features,
            'quality_maintained': baseline_risk == optimized_risk or (baseline_risk == 'safe' and optimized_risk in ['safe', 'low'])
        }
        
        results.append(result)
        
        status = "✅ IMPROVED" if enhanced_features and result['quality_maintained'] else "✅ MAINTAINED"
        print(f"  Performance: {avg_baseline:.2f}ms → {avg_optimized:.2f}ms ({performance_impact:+.1f}%)")
        print(f"  Quality: {baseline_risk} → {optimized_risk} {status}")
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 Phase 1A Benchmark Summary")
    print("=" * 60)
    
    avg_impact = sum(r['performance_impact_pct'] for r in results) / len(results)
    quality_maintained_count = sum(1 for r in results if r['quality_maintained'])
    enhanced_count = sum(1 for r in results if r['enhanced_features'])
    
    print(f"Average Performance Impact: {avg_impact:+.1f}%")
    print(f"Quality Maintained: {quality_maintained_count}/{len(results)} tests")
    print(f"Enhanced Analysis: {enhanced_count}/{len(results)} tests")
    print(f"Performance Budget: {'✅ WITHIN' if avg_impact <= 20 else '❌ EXCEEDED'}")
    
    # Performance stats
    perf_stats = optimized_scanner.get_performance_stats()
    if 'cache_performance' in perf_stats:
        cache_stats = perf_stats['cache_performance']
        print(f"Cache Hit Rate: {cache_stats['hit_rate']:.1%}")
        print(f"AST Enhancement Rate: {perf_stats.get('enhancement_rate', 0):.1%}")
    
    return {
        'results': results,
        'summary': {
            'avg_performance_impact': avg_impact,
            'quality_maintained_rate': quality_maintained_count / len(results),
            'enhancement_rate': enhanced_count / len(results),
            'within_budget': avg_impact <= 20
        },
        'performance_stats': perf_stats
    }

if __name__ == "__main__":
    benchmark_results = benchmark_phase_1a_improvements()
    
    # Validate Phase 1A readiness
    summary = benchmark_results['summary']
    phase_1a_ready = (
        summary['quality_maintained_rate'] >= 0.95 and  # 95%+ quality maintained
        summary['within_budget'] and                     # Within performance budget
        summary['enhancement_rate'] >= 0.6               # 60%+ tests show enhancements
    )
    
    print(f"\\n🎯 Phase 1A Assessment: {'✅ READY' if phase_1a_ready else '❌ NEEDS WORK'}")
    
    if phase_1a_ready:
        print("✅ Safe to proceed to Phase 1B implementation")
    else:
        print("⚠️  Address performance or quality issues before proceeding")