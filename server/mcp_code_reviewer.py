#!/usr/bin/env python3
"""
MCP Code Reviewer Server for mem0
Comprehensive code analysis with security, performance, and maintainability reviews
"""

import os
import sys
import ast
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server import Server

@dataclass
class CodeIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    title: str
    description: str
    code_snippet: str
    suggestion: str
    category: str
    confidence: float

@dataclass
class CodeReviewResult:
    file_path: str
    language: str
    total_lines: int
    issues: List[CodeIssue]
    metrics: Dict[str, Any]
    summary: Dict[str, int]

class CodeAnalyzer:
    """Advanced code analysis engine"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.executor = ThreadPoolExecutor(max_workers=4)

    def analyze_file(self, file_path: str) -> CodeReviewResult:
        """Analyze a single file comprehensively"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine language
        language = self._detect_language(path)

        # Read file content
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.splitlines()
        total_lines = len(lines)

        issues = []

        # Run different analysis types based on language
        if language == 'python':
            issues.extend(self._analyze_python_code(content, file_path))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_code(content, file_path))
        elif language in ['bash', 'shell']:
            issues.extend(self._analyze_shell_code(content, file_path))

        # Generic code analysis
        issues.extend(self._analyze_generic(content, file_path))

        # Calculate metrics
        metrics = self._calculate_metrics(content, language)

        # Create summary
        summary = self._create_summary(issues)

        return CodeReviewResult(
            file_path=file_path,
            language=language,
            total_lines=total_lines,
            issues=issues,
            metrics=metrics,
            summary=summary
        )

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        ext = path.suffix.lower()
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        }
        return ext_map.get(ext, 'unknown')

    def _analyze_python_code(self, content: str, file_path: str) -> List[CodeIssue]:
        """Comprehensive Python code analysis"""
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=e.lineno or 1,
                issue_type="syntax_error",
                severity="high",
                title="Syntax Error",
                description=f"Syntax error: {e.msg}",
                code_snippet=f"Line {e.lineno}: {e.text}",
                suggestion="Fix the syntax error before proceeding",
                category="syntax",
                confidence=1.0
            ))
            return issues

        # Security analysis
        issues.extend(self._analyze_python_security(tree, content, file_path))

        # Performance analysis
        issues.extend(self._analyze_python_performance(tree, content, file_path))

        # Code quality analysis
        issues.extend(self._analyze_python_quality(tree, content, file_path))

        # Best practices
        issues.extend(self._analyze_python_best_practices(tree, content, file_path))

        return issues

    def _analyze_python_security(self, tree: ast.AST, content: str, file_path: str) -> List[CodeIssue]:
        """Security-focused analysis for Python code"""
        issues = []

        for node in ast.walk(tree):
            # Check for dangerous functions
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in ['eval', 'exec', 'input']:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="security_risk",
                            severity="high",
                            title=f"Dangerous function usage: {func_name}",
                            description=f"Use of {func_name}() can lead to security vulnerabilities",
                            code_snippet=self._get_code_snippet(content, node.lineno),
                            suggestion=f"Replace {func_name}() with safer alternatives",
                            category="security",
                            confidence=0.9
                        ))

            # Check for SQL injection vulnerabilities
            elif isinstance(node, ast.Str):
                if 'SELECT' in node.s or 'INSERT' in node.s or 'UPDATE' in node.s:
                    if '%' in node.s or '+' in node.s:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="sql_injection",
                            severity="high",
                            title="Potential SQL Injection",
                            description="String formatting in SQL queries can lead to injection attacks",
                            code_snippet=self._get_code_snippet(content, node.lineno),
                            suggestion="Use parameterized queries or prepared statements",
                            category="security",
                            confidence=0.8
                        ))

            # Check for hardcoded secrets
            elif isinstance(node, ast.Str):
                if self._looks_like_secret(node.s):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="hardcoded_secret",
                        severity="high",
                        title="Hardcoded Secret Detected",
                        description="Potential hardcoded password, API key, or other secret",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Move secrets to environment variables or secure config",
                        category="security",
                        confidence=0.7
                    ))

        return issues

    def _analyze_python_performance(self, tree: ast.AST, content: str, file_path: str) -> List[CodeIssue]:
        """Performance-focused analysis for Python code"""
        issues = []

        # Check for inefficient patterns
        for node in ast.walk(tree):
            # Check for inefficient list operations
            if isinstance(node, ast.For):
                # Check if using list.append in loop when list comprehension could be used
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                        if len(node.iter.args) == 1:
                            issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="performance_inefficient",
                                severity="medium",
                                title="Inefficient Loop",
                                description="Consider using list comprehension for better performance",
                                code_snippet=self._get_code_snippet(content, node.lineno),
                                suggestion="Use list comprehension: [x*2 for x in range(n)]",
                                category="performance",
                                confidence=0.6
                            ))

            # Check for unnecessary list creation
            elif isinstance(node, ast.ListComp):
                if len(node.generators) > 2:  # Complex comprehension
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="complex_comprehension",
                        severity="low",
                        title="Complex List Comprehension",
                        description="Very complex list comprehension may be hard to read",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Consider breaking into multiple lines or using traditional loop",
                        category="maintainability",
                        confidence=0.5
                    ))

        return issues

    def _analyze_python_quality(self, tree: ast.AST, content: str, file_path: str) -> List[CodeIssue]:
        """Code quality analysis for Python code"""
        issues = []

        # Check function complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="high_complexity",
                        severity="medium",
                        title=f"High Function Complexity: {complexity}",
                        description=f"Function '{node.name}' has high cyclomatic complexity",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Break down into smaller functions",
                        category="maintainability",
                        confidence=0.8
                    ))

                # Check function length
                if len(node.body) > 50:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="long_function",
                        severity="low",
                        title="Long Function",
                        description=f"Function '{node.name}' is {len(node.body)} lines long",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Consider breaking into smaller functions",
                        category="maintainability",
                        confidence=0.6
                    ))

        return issues

    def _analyze_python_best_practices(self, tree: ast.AST, content: str, file_path: str) -> List[CodeIssue]:
        """Best practices analysis for Python code"""
        issues = []

        # Check for imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        severity="low",
                        title=f"Missing Docstring: {node.name}",
                        description=f"{node.__class__.__name__} '{node.name}' lacks docstring",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Add docstring describing the function/class purpose",
                        category="documentation",
                        confidence=0.7
                    ))

        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if not node.type:  # Bare except
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="bare_except",
                        severity="medium",
                        title="Bare Except Clause",
                        description="Bare 'except:' catches all exceptions including system exits",
                        code_snippet=self._get_code_snippet(content, node.lineno),
                        suggestion="Specify exception types: except (ValueError, TypeError):",
                        category="error_handling",
                        confidence=0.8
                    ))

        return issues

    def _analyze_js_code(self, content: str, file_path: str) -> List[CodeIssue]:
        """JavaScript/TypeScript code analysis"""
        issues = []

        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Check for console.log in production code
            if 'console.log' in line and 'console.' in line:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="debug_code",
                    severity="low",
                    title="Debug Code Left in Production",
                    description="console.log statements should be removed for production",
                    code_snippet=line.strip(),
                    suggestion="Remove console.log or replace with proper logging",
                    category="best_practices",
                    confidence=0.6
                ))

            # Check for eval usage
            if 'eval(' in line:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="security_risk",
                    severity="high",
                    title="Use of eval()",
                    description="eval() can lead to security vulnerabilities",
                    code_snippet=line.strip(),
                    suggestion="Avoid eval() - find alternative approaches",
                    category="security",
                    confidence=0.9
                ))

            # Check for hardcoded secrets
            if self._looks_like_secret(line):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="hardcoded_secret",
                    severity="high",
                    title="Hardcoded Secret Detected",
                    description="Potential hardcoded password, API key, or other secret",
                    code_snippet=line.strip(),
                    suggestion="Move secrets to environment variables",
                    category="security",
                    confidence=0.7
                ))

        return issues

    def _analyze_shell_code(self, content: str, file_path: str) -> List[CodeIssue]:
        """Shell script analysis"""
        issues = []

        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Check for sudo without proper validation
            if 'sudo' in line and not any(skip in line for skip in ['#', 'echo', 'read']):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="sudo_usage",
                    severity="medium",
                    title="Sudo Usage",
                    description="Script uses sudo - ensure proper validation",
                    code_snippet=line.strip(),
                    suggestion="Add input validation before sudo commands",
                    category="security",
                    confidence=0.7
                ))

            # Check for command injection vulnerabilities
            if '$' in line and ('eval' in line or 'bash -c' in line):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="command_injection",
                    severity="high",
                    title="Potential Command Injection",
                    description="Variable interpolation in shell commands can be dangerous",
                    code_snippet=line.strip(),
                    suggestion="Use proper quoting or command arrays",
                    category="security",
                    confidence=0.8
                ))

            # Check for set -e missing
            if i == 1 and 'set -e' not in content[:200]:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="missing_error_handling",
                    severity="low",
                    title="Missing Error Handling",
                    description="Script doesn't use 'set -e' for proper error handling",
                    code_snippet="#!/bin/bash",
                    suggestion="Add 'set -e' after shebang for better error handling",
                    category="best_practices",
                    confidence=0.5
                ))

        return issues

    def _analyze_generic(self, content: str, file_path: str) -> List[CodeIssue]:
        """Generic code analysis applicable to all languages"""
        issues = []

        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            # Check for TODO/FIXME comments
            if any(marker in line.upper() for marker in ['TODO', 'FIXME', 'XXX', 'HACK']):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="todo_comment",
                    severity="info",
                    title="TODO/FIXME Comment",
                    description="Code contains TODO or FIXME comment",
                    code_snippet=line.strip(),
                    suggestion="Address the TODO item or remove if completed",
                    category="documentation",
                    confidence=0.8
                ))

            # Check for very long lines
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="long_line",
                    severity="low",
                    title="Very Long Line",
                    description=f"Line is {len(line)} characters long",
                    code_snippet=line.strip()[:80] + "...",
                    suggestion="Break long lines for better readability",
                    category="style",
                    confidence=0.6
                ))

            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="trailing_whitespace",
                    severity="low",
                    title="Trailing Whitespace",
                    description="Line contains trailing whitespace",
                    code_snippet=line.rstrip() + "[whitespace]",
                    suggestion="Remove trailing whitespace",
                    category="style",
                    confidence=1.0
                ))

        return issues

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _looks_like_secret(self, text: str) -> bool:
        """Check if text looks like a hardcoded secret"""
        # Check for common secret patterns
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'auth[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'private[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'[a-f0-9]{32,}',  # Long hex strings (could be hashes/keys)
            r'[A-Za-z0-9+/]{40,}',  # Base64-like strings
        ]

        text_lower = text.lower()
        for pattern in secret_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _get_code_snippet(self, content: str, line_number: int, context: int = 2) -> str:
        """Get code snippet around a line number"""
        lines = content.splitlines()
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)

        snippet_lines = []
        for i in range(start, end):
            marker = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{marker}{i+1:4d}: {lines[i]}")

        return "\n".join(snippet_lines)

    def _calculate_metrics(self, content: str, language: str) -> Dict[str, Any]:
        """Calculate code metrics"""
        lines = content.splitlines()
        total_lines = len(lines)

        # Count non-empty lines
        non_empty_lines = sum(1 for line in lines if line.strip())

        # Count comments (language-specific)
        comment_lines = 0
        if language == 'python':
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        elif language in ['javascript', 'typescript']:
            comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*'))

        return {
            'total_lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'comment_lines': comment_lines,
            'code_lines': non_empty_lines - comment_lines,
            'comment_ratio': comment_lines / non_empty_lines if non_empty_lines > 0 else 0,
        }

    def _create_summary(self, issues: List[CodeIssue]) -> Dict[str, int]:
        """Create summary of issues by severity and category"""
        summary = {
            'total_issues': len(issues),
            'severity_breakdown': {
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            },
            'category_breakdown': {}
        }

        for issue in issues:
            summary['severity_breakdown'][issue.severity] += 1

            if issue.category not in summary['category_breakdown']:
                summary['category_breakdown'][issue.category] = 0
            summary['category_breakdown'][issue.category] += 1

        return summary

class CodeReviewerServer(Server):
    """MCP Server for comprehensive code review"""

    def __init__(self):
        super().__init__("code-reviewer")
        self.analyzer = CodeAnalyzer(os.getcwd())

    async def setup_handlers(self):
        """Set up MCP handlers for code review operations"""

        @self.app.list_tools()
        async def list_tools():
            """List available code review tools"""
            return [
                {
                    "name": "analyze_file",
                    "description": "Analyze a single file for code quality, security, and performance issues",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to analyze"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Areas to focus on: security, performance, maintainability, best_practices",
                                "default": ["security", "performance", "maintainability"]
                            }
                        },
                        "required": ["file_path"]
                    }
                },
                {
                    "name": "analyze_directory",
                    "description": "Analyze all files in a directory recursively",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Path to the directory to analyze"
                            },
                            "file_extensions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File extensions to analyze (e.g., ['.py', '.js'])",
                                "default": [".py", ".js", ".ts", ".sh"]
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Patterns to exclude (e.g., ['__pycache__', '*.pyc'])",
                                "default": ["__pycache__", "*.pyc", "node_modules", ".git"]
                            }
                        },
                        "required": ["directory_path"]
                    }
                },
                {
                    "name": "generate_report",
                    "description": "Generate a comprehensive code review report",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "analysis_results": {
                                "type": "array",
                                "description": "Array of analysis results from analyze_file or analyze_directory"
                            },
                            "output_format": {
                                "type": "string",
                                "enum": ["json", "markdown", "html"],
                                "default": "markdown"
                            }
                        },
                        "required": ["analysis_results"]
                    }
                },
                {
                    "name": "check_security",
                    "description": "Perform security-focused code analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to check for security issues"
                            }
                        },
                        "required": ["file_path"]
                    }
                },
                {
                    "name": "performance_audit",
                    "description": "Analyze code for performance issues",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to audit for performance"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            ]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Handle tool calls for code review operations"""

            if name == "analyze_file":
                file_path = arguments.get("file_path")
                focus_areas = arguments.get("focus_areas", ["security", "performance", "maintainability"])

                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.analyzer.executor,
                        self.analyzer.analyze_file,
                        file_path
                    )

                    # Filter issues by focus areas if specified
                    if focus_areas != ["security", "performance", "maintainability"]:
                        result.issues = [
                            issue for issue in result.issues
                            if issue.category in focus_areas
                        ]

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(asdict(result), indent=2, default=str)
                        }]
                    }

                except Exception as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error analyzing file {file_path}: {str(e)}"
                        }],
                        "isError": True
                    }

            elif name == "analyze_directory":
                directory_path = arguments.get("directory_path")
                file_extensions = arguments.get("file_extensions", [".py", ".js", ".ts", ".sh"])
                exclude_patterns = arguments.get("exclude_patterns", ["__pycache__", "*.pyc", "node_modules", ".git"])

                try:
                    results = []
                    dir_path = Path(directory_path)

                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and file_path.suffix in file_extensions:
                            # Check if file should be excluded
                            should_exclude = False
                            for pattern in exclude_patterns:
                                if pattern in str(file_path):
                                    should_exclude = True
                                    break

                            if not should_exclude:
                                try:
                                    result = await asyncio.get_event_loop().run_in_executor(
                                        self.analyzer.executor,
                                        self.analyzer.analyze_file,
                                        str(file_path)
                                    )
                                    results.append(asdict(result))
                                except Exception as e:
                                    results.append({
                                        "file_path": str(file_path),
                                        "error": str(e)
                                    })

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(results, indent=2, default=str)
                        }]
                    }

                except Exception as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error analyzing directory {directory_path}: {str(e)}"
                        }],
                        "isError": True
                    }

            elif name == "generate_report":
                analysis_results = arguments.get("analysis_results", [])
                output_format = arguments.get("output_format", "markdown")

                try:
                    report = self._generate_report(analysis_results, output_format)
                    return {
                        "content": [{
                            "type": "text",
                            "text": report
                        }]
                    }
                except Exception as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error generating report: {str(e)}"
                        }],
                        "isError": True
                    }

            elif name == "check_security":
                file_path = arguments.get("file_path")

                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.analyzer.executor,
                        self.analyzer.analyze_file,
                        file_path
                    )

                    # Filter only security issues
                    security_issues = [
                        issue for issue in result.issues
                        if issue.category == "security"
                    ]

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "file_path": file_path,
                                "security_issues": [asdict(issue) for issue in security_issues],
                                "total_security_issues": len(security_issues)
                            }, indent=2, default=str)
                        }]
                    }

                except Exception as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error checking security for {file_path}: {str(e)}"
                        }],
                        "isError": True
                    }

            elif name == "performance_audit":
                file_path = arguments.get("file_path")

                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.analyzer.executor,
                        self.analyzer.analyze_file,
                        file_path
                    )

                    # Filter only performance issues
                    perf_issues = [
                        issue for issue in result.issues
                        if issue.category == "performance"
                    ]

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "file_path": file_path,
                                "performance_issues": [asdict(issue) for issue in perf_issues],
                                "total_performance_issues": len(perf_issues)
                            }, indent=2, default=str)
                        }]
                    }

                except Exception as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Error auditing performance for {file_path}: {str(e)}"
                        }],
                        "isError": True
                    }

            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

    def _generate_report(self, analysis_results: List[Dict], output_format: str) -> str:
        """Generate a comprehensive code review report"""

        if output_format == "json":
            return json.dumps(analysis_results, indent=2, default=str)

        elif output_format == "markdown":
            return self._generate_markdown_report(analysis_results)

        elif output_format == "html":
            return self._generate_html_report(analysis_results)

        else:
            return f"Unsupported format: {output_format}"

    def _generate_markdown_report(self, analysis_results: List[Dict]) -> str:
        """Generate markdown report"""
        lines = ["# Code Review Report\n"]

        total_files = len(analysis_results)
        total_issues = 0
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}

        for result in analysis_results:
            if "error" in result:
                continue

            total_issues += len(result.get("issues", []))
            summary = result.get("summary", {})
            severity_counts["high"] += summary.get("severity_breakdown", {}).get("high", 0)
            severity_counts["medium"] += summary.get("severity_breakdown", {}).get("medium", 0)
            severity_counts["low"] += summary.get("severity_breakdown", {}).get("low", 0)
            severity_counts["info"] += summary.get("severity_breakdown", {}).get("info", 0)

        lines.extend([
            f"## Summary\n",
            f"- **Total Files Analyzed**: {total_files}\n",
            f"- **Total Issues Found**: {total_issues}\n",
            f"- **High Severity**: {severity_counts['high']}\n",
            f"- **Medium Severity**: {severity_counts['medium']}\n",
            f"- **Low Severity**: {severity_counts['low']}\n",
            f"- **Info**: {severity_counts['info']}\n\n"
        ])

        for result in analysis_results:
            if "error" in result:
                lines.append(f"## {result['file_path']}\n**Error**: {result['error']}\n\n")
                continue

            file_path = result["file_path"]
            language = result["language"]
            total_lines = result["total_lines"]
            issues = result.get("issues", [])
            metrics = result.get("metrics", {})

            lines.extend([
                f"## {file_path}\n",
                f"**Language**: {language}\n",
                f"**Lines**: {total_lines}\n",
                f"**Code Lines**: {metrics.get('code_lines', 'N/A')}\n",
                f"**Comment Ratio**: {metrics.get('comment_ratio', 0):.1%}\n\n"
            ])

            if issues:
                lines.append("### Issues Found\n\n")
                for issue in issues:
                    lines.extend([
                        f"#### {issue['title']} ({issue['severity'].upper()})\n",
                        f"**File**: {issue['file_path']}:{issue['line_number']}\n",
                        f"**Type**: {issue['issue_type']}\n",
                        f"**Category**: {issue['category']}\n",
                        f"**Description**: {issue['description']}\n",
                        f"**Suggestion**: {issue['suggestion']}\n\n",
                        f"```code\n{issue['code_snippet']}\n```\n\n"
                    ])
            else:
                lines.append("### ✅ No Issues Found\n\n")

        return "".join(lines)

    def _generate_html_report(self, analysis_results: List[Dict]) -> str:
        """Generate HTML report"""
        html = ["""<!DOCTYPE html>
<html>
<head>
    <title>Code Review Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .file { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .issue { margin: 10px 0; padding: 10px; border-left: 4px solid; }
        .high { border-color: #dc3545; background: #f8d7da; }
        .medium { border-color: #ffc107; background: #fff3cd; }
        .low { border-color: #17a2b8; background: #d1ecf1; }
        .info { border-color: #6c757d; background: #e2e3e5; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f8f8f8; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Code Review Report</h1>
"""]

        # Summary
        total_files = len(analysis_results)
        total_issues = sum(len(result.get("issues", [])) for result in analysis_results if "error" not in result)
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}

        for result in analysis_results:
            if "error" not in result:
                summary = result.get("summary", {})
                severity_counts["high"] += summary.get("severity_breakdown", {}).get("high", 0)
                severity_counts["medium"] += summary.get("severity_breakdown", {}).get("medium", 0)
                severity_counts["low"] += summary.get("severity_breakdown", {}).get("low", 0)
                severity_counts["info"] += summary.get("severity_breakdown", {}).get("info", 0)

        html.extend([
            '<div class="summary">',
            f'<h2>Summary</h2>',
            f'<p><strong>Total Files Analyzed:</strong> {total_files}</p>',
            f'<p><strong>Total Issues Found:</strong> {total_issues}</p>',
            f'<p><strong>High Severity:</strong> {severity_counts["high"]}</p>',
            f'<p><strong>Medium Severity:</strong> {severity_counts["medium"]}</p>',
            f'<p><strong>Low Severity:</strong> {severity_counts["low"]}</p>',
            f'<p><strong>Info:</strong> {severity_counts["info"]}</p>',
            '</div>'
        ])

        # File details
        for result in analysis_results:
            if "error" in result:
                html.extend([
                    f'<div class="file">',
                    f'<h3>{result["file_path"]}</h3>',
                    f'<p><strong>Error:</strong> {result["error"]}</p>',
                    '</div>'
                ])
                continue

            file_path = result["file_path"]
            language = result["language"]
            total_lines = result["total_lines"]
            issues = result.get("issues", [])
            metrics = result.get("metrics", {})

            html.extend([
                f'<div class="file">',
                f'<h3>{file_path}</h3>',
                f'<p><strong>Language:</strong> {language}</p>',
                f'<p><strong>Lines:</strong> {total_lines}</p>',
                f'<p><strong>Code Lines:</strong> {metrics.get("code_lines", "N/A")}</p>',
                f'<p><strong>Comment Ratio:</strong> {metrics.get("comment_ratio", 0):.1%}</p>'
            ])

            if issues:
                html.append('<h4>Issues Found</h4>')
                for issue in issues:
                    severity_class = issue['severity']
                    html.extend([
                        f'<div class="issue {severity_class}">',
                        f'<h5>{issue["title"]} ({issue["severity"].upper()})</h5>',
                        f'<p><strong>File:</strong> {issue["file_path"]}:{issue["line_number"]}</p>',
                        f'<p><strong>Type:</strong> {issue["issue_type"]}</p>',
                        f'<p><strong>Category:</strong> {issue["category"]}</p>',
                        f'<p><strong>Description:</strong> {issue["description"]}</p>',
                        f'<p><strong>Suggestion:</strong> {issue["suggestion"]}</p>',
                        f'<pre><code>{issue["code_snippet"]}</code></pre>',
                        '</div>'
                    ])
            else:
                html.append('<p><strong>✅ No Issues Found</strong></p>')

            html.append('</div>')

        html.extend(['</body>', '</html>'])
        return "".join(html)

async def main():
    """Main entry point for the code reviewer MCP server"""
    server = CodeReviewerServer()
    await server.setup_handlers()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
