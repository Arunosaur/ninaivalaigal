# SPEC-136: Execution System Backends

**Status:** Draft
**Created:** 2025-10-28
**Updated:** 2025-10-28
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, Platform Infrastructure

---

## Executive Summary

Define a unified execution system architecture that abstracts different backend types (tool-calling, code execution, GUI automation) behind a common interface. This enables agents to execute actions across multiple domains while maintaining consistent error handling, security boundaries, and observability.

---

## Problem Statement

Current agent systems lack standardized execution backends, leading to:
- **Fragmented implementations:** Each action type requires custom code
- **Inconsistent error handling:** Different backends handle failures differently
- **Security concerns:** No unified sandboxing or permission model
- **Limited observability:** Execution traces vary by backend type
- **Poor reusability:** Can't easily swap or extend backends

This prevents agents from reliably executing complex workflows that span multiple execution domains.

---

## Goals

### Primary Goals
1. Define unified execution interface for all backend types
2. Implement secure sandboxing for code execution
3. Enable GUI automation with cross-platform support
4. Provide consistent error handling and logging
5. Support async/streaming execution

### Non-Goals
1. Building custom VM or container runtime
2. Implementing specific GUI automation tools from scratch
3. Creating programming language implementations

---

## Execution Backend Types

### 1. Tool-Calling Backend

**Description:** Execute structured function calls with JSON schemas

**Capabilities:**
- Call external APIs
- Invoke system functions
- Execute database queries
- Trigger webhooks

**Interface:**
```python
@dataclass
class ToolDefinition:
    """Function specification"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    returns: Dict[str, Any]  # Return type schema
    timeout: int = 30
    retry_policy: Optional[RetryPolicy] = None

class ToolCallingBackend:
    def register_tool(self, tool: ToolDefinition, handler: Callable):
        """Register a callable tool"""
        self.tools[tool.name] = {
            "definition": tool,
            "handler": handler
        }

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ToolResult:
        """Execute registered tool"""
        if tool_name not in self.tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not registered")

        tool = self.tools[tool_name]

        # Validate parameters
        self._validate_params(parameters, tool["definition"].parameters)

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                tool["handler"](**parameters),
                timeout=tool["definition"].timeout
            )
            return ToolResult(
                success=True,
                output=result,
                tool_name=tool_name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=tool_name
            )
```

**Example Tool Definitions:**
```python
# File system tool
file_read_tool = ToolDefinition(
    name="read_file",
    description="Read contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "encoding": {"type": "string", "default": "utf-8"}
        },
        "required": ["path"]
    },
    returns={"type": "string"},
    timeout=10
)

# API call tool
api_call_tool = ToolDefinition(
    name="api_request",
    description="Make HTTP request",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "headers": {"type": "object"},
            "body": {"type": "object"}
        },
        "required": ["url", "method"]
    },
    returns={"type": "object"},
    timeout=30,
    retry_policy=RetryPolicy(max_retries=3, backoff_factor=2.0)
)

# Database query tool
db_query_tool = ToolDefinition(
    name="execute_query",
    description="Execute SQL query",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "parameters": {"type": "array"},
            "database": {"type": "string", "default": "main"}
        },
        "required": ["query"]
    },
    returns={"type": "array"},
    timeout=60
)
```

**Tool Registry:**
```python
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.handlers: Dict[str, Callable] = {}

    def register(self, tool: ToolDefinition, handler: Callable):
        self.tools[tool.name] = tool
        self.handlers[tool.name] = handler

    def list_tools(self) -> List[ToolDefinition]:
        return list(self.tools.values())

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get OpenAPI-style schema for tool"""
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "returns": tool.returns
        }
```

---

### 2. Code Execution Backend

**Description:** Execute code in sandboxed environments

**Supported Languages:**
- Python
- JavaScript/Node.js
- SQL
- Shell/Bash

**Security Model:**
```python
@dataclass
class SandboxConfig:
    """Security constraints for code execution"""
    allowed_imports: List[str]  # Whitelist of importable modules
    blocked_functions: List[str]  # Blacklist dangerous functions
    max_execution_time: int = 30  # Seconds
    max_memory: int = 512  # MB
    network_access: bool = False
    filesystem_access: bool = False
    allowed_directories: List[str] = None
```

**Python Execution:**
```python
class PythonExecutionBackend:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.executor = RestrictedPython(config)

    async def execute(
        self,
        code: str,
        globals: Dict[str, Any] = None,
        timeout: int = None
    ) -> ExecutionResult:
        """Execute Python code in sandbox"""

        # Parse and validate
        try:
            tree = ast.parse(code)
            self._validate_ast(tree)
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                error=f"Syntax error: {e}",
                stderr=str(e)
            )

        # Set up restricted environment
        safe_globals = self._create_safe_globals(globals)

        # Execute with timeout and resource limits
        try:
            with ResourceLimiter(
                max_memory=self.config.max_memory,
                max_time=timeout or self.config.max_execution_time
            ):
                result = await self._run_in_subprocess(code, safe_globals)

            return ExecutionResult(
                success=True,
                output=result.stdout,
                return_value=result.value,
                execution_time=result.duration
            )
        except TimeoutError:
            return ExecutionResult(
                success=False,
                error="Execution timeout",
                execution_time=timeout
            )
        except MemoryError:
            return ExecutionResult(
                success=False,
                error="Memory limit exceeded"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                stderr=traceback.format_exc()
            )

    def _validate_ast(self, tree: ast.AST):
        """Check for dangerous operations"""
        for node in ast.walk(tree):
            # Block dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.config.allowed_imports:
                        raise SecurityError(f"Import '{alias.name}' not allowed")

            # Block eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.config.blocked_functions:
                        raise SecurityError(f"Function '{node.func.id}' not allowed")

    def _create_safe_globals(self, user_globals: Dict[str, Any]) -> Dict[str, Any]:
        """Create restricted global namespace"""
        safe_builtins = {
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            # ... safe builtins only
        }

        globals = {
            '__builtins__': safe_builtins,
            **(user_globals or {})
        }

        return globals
```

**Shell Execution:**
```python
class ShellExecutionBackend:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.allowed_commands = [
            'ls', 'cat', 'grep', 'find', 'echo',
            'git', 'npm', 'pip', 'docker'  # Configurable
        ]

    async def execute(
        self,
        command: str,
        cwd: str = None,
        env: Dict[str, str] = None
    ) -> ExecutionResult:
        """Execute shell command"""

        # Parse and validate command
        cmd_parts = shlex.split(command)
        if cmd_parts[0] not in self.allowed_commands:
            return ExecutionResult(
                success=False,
                error=f"Command '{cmd_parts[0]}' not allowed"
            )

        # Execute in subprocess
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.max_execution_time
            )

            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout.decode(),
                stderr=stderr.decode(),
                exit_code=process.returncode
            )
        except asyncio.TimeoutError:
            process.kill()
            return ExecutionResult(
                success=False,
                error="Command timeout"
            )
```

**SQL Execution:**
```python
class SQLExecutionBackend:
    def __init__(self, connection_string: str, config: SandboxConfig):
        self.engine = create_engine(connection_string)
        self.config = config

    async def execute(
        self,
        query: str,
        parameters: List[Any] = None
    ) -> ExecutionResult:
        """Execute SQL query"""

        # Validate query type
        query_type = self._get_query_type(query)
        if query_type not in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']:
            return ExecutionResult(
                success=False,
                error=f"Query type '{query_type}' not allowed"
            )

        # Execute with timeout
        try:
            async with self.engine.begin() as conn:
                result = await asyncio.wait_for(
                    conn.execute(text(query), parameters or []),
                    timeout=self.config.max_execution_time
                )

                if query_type == 'SELECT':
                    rows = result.fetchall()
                    return ExecutionResult(
                        success=True,
                        output=rows,
                        row_count=len(rows)
                    )
                else:
                    return ExecutionResult(
                        success=True,
                        output=f"{result.rowcount} rows affected",
                        row_count=result.rowcount
                    )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e)
            )
```

---

### 3. GUI Automation Backend

**Description:** Interact with graphical user interfaces

**Supported Platforms:**
- Web (Playwright, Selenium)
- Desktop (PyAutoGUI, AppleScript, Windows Automation)
- Mobile (Appium)

**Web Automation:**
```python
class WebAutomationBackend:
    def __init__(self, browser: str = "chromium", headless: bool = True):
        self.browser_type = browser
        self.headless = headless
        self.page: Optional[Page] = None

    async def initialize(self):
        """Start browser session"""
        self.playwright = await async_playwright().start()
        browser = await getattr(
            self.playwright,
            self.browser_type
        ).launch(headless=self.headless)
        self.page = await browser.new_page()

    async def navigate(self, url: str) -> ExecutionResult:
        """Navigate to URL"""
        try:
            await self.page.goto(url, wait_until="networkidle")
            return ExecutionResult(
                success=True,
                output=f"Navigated to {url}"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def click(self, selector: str) -> ExecutionResult:
        """Click element"""
        try:
            await self.page.click(selector)
            return ExecutionResult(
                success=True,
                output=f"Clicked {selector}"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def type_text(self, selector: str, text: str) -> ExecutionResult:
        """Type text into element"""
        try:
            await self.page.fill(selector, text)
            return ExecutionResult(
                success=True,
                output=f"Typed into {selector}"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def screenshot(self, path: str = None) -> ExecutionResult:
        """Capture screenshot"""
        try:
            screenshot = await self.page.screenshot(path=path)
            return ExecutionResult(
                success=True,
                output=screenshot if not path else f"Saved to {path}",
                metadata={"screenshot": screenshot}
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def extract_text(self, selector: str) -> ExecutionResult:
        """Extract text from element"""
        try:
            text = await self.page.text_content(selector)
            return ExecutionResult(
                success=True,
                output=text
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def evaluate(self, js_code: str) -> ExecutionResult:
        """Execute JavaScript in page context"""
        try:
            result = await self.page.evaluate(js_code)
            return ExecutionResult(
                success=True,
                output=result
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
```

**Desktop Automation:**
```python
class DesktopAutomationBackend:
    def __init__(self, platform: str = None):
        self.platform = platform or sys.platform

    async def click(self, x: int, y: int) -> ExecutionResult:
        """Click at coordinates"""
        try:
            pyautogui.click(x, y)
            return ExecutionResult(
                success=True,
                output=f"Clicked at ({x}, {y})"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def type_text(self, text: str, interval: float = 0.1) -> ExecutionResult:
        """Type text with delay"""
        try:
            pyautogui.write(text, interval=interval)
            return ExecutionResult(
                success=True,
                output=f"Typed: {text}"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def press_key(self, key: str) -> ExecutionResult:
        """Press keyboard key"""
        try:
            pyautogui.press(key)
            return ExecutionResult(
                success=True,
                output=f"Pressed {key}"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    async def locate_image(self, image_path: str) -> ExecutionResult:
        """Find image on screen"""
        try:
            location = pyautogui.locateCenterOnScreen(image_path)
            if location:
                return ExecutionResult(
                    success=True,
                    output=location,
                    metadata={"x": location[0], "y": location[1]}
                )
            else:
                return ExecutionResult(
                    success=False,
                    error="Image not found"
                )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
```

---

## Unified Execution Interface

```python
@dataclass
class ExecutionResult:
    """Standard result format"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    stderr: Optional[str] = None
    execution_time: Optional[float] = None
    exit_code: Optional[int] = None
    metadata: Dict[str, Any] = None

class ExecutionBackend(ABC):
    """Base class for all execution backends"""

    @abstractmethod
    async def execute(
        self,
        action: Action,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute action and return result"""
        pass

    @abstractmethod
    async def initialize(self):
        """Set up execution environment"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Tear down execution environment"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List supported action types"""
        pass

class ExecutionEngine:
    """Orchestrate multiple backends"""

    def __init__(self):
        self.backends: Dict[str, ExecutionBackend] = {}

    def register_backend(self, name: str, backend: ExecutionBackend):
        self.backends[name] = backend

    async def execute(
        self,
        action: Action,
        backend: str = None
    ) -> ExecutionResult:
        """Execute action using appropriate backend"""

        # Auto-select backend if not specified
        if backend is None:
            backend = self._select_backend(action)

        if backend not in self.backends:
            return ExecutionResult(
                success=False,
                error=f"Backend '{backend}' not found"
            )

        # Execute with logging and monitoring
        start_time = time.time()

        try:
            result = await self.backends[backend].execute(action)
            result.execution_time = time.time() - start_time

            # Log execution
            self._log_execution(action, result, backend)

            return result
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _select_backend(self, action: Action) -> str:
        """Choose appropriate backend for action"""
        if action.type == "tool_call":
            return "tool_calling"
        elif action.type == "code":
            return f"{action.language}_execution"
        elif action.type == "gui":
            return "gui_automation"
        else:
            raise ValueError(f"Unknown action type: {action.type}")
```

---

## Implementation Plan

### Phase 1: Tool-Calling (Weeks 1-2)
- [ ] Implement `ToolDefinition` and registry
- [ ] Build `ToolCallingBackend`
- [ ] Add parameter validation
- [ ] Create standard tool library

### Phase 2: Code Execution (Weeks 3-5)
- [ ] Implement Python sandbox
- [ ] Build Shell executor
- [ ] Add SQL backend
- [ ] Create resource limiting

### Phase 3: GUI Automation (Weeks 6-8)
- [ ] Integrate Playwright for web
- [ ] Add desktop automation (PyAutoGUI)
- [ ] Build screenshot/OCR pipeline
- [ ] Create element locators

### Phase 4: Unification (Weeks 9-10)
- [ ] Build `ExecutionEngine`
- [ ] Implement backend selection logic
- [ ] Add execution logging/tracing
- [ ] Create monitoring dashboards

---

## Security Considerations

1. **Sandboxing:** Isolate code execution
2. **Resource Limits:** Prevent DoS attacks
3. **Input Validation:** Sanitize all inputs
4. **Permission Model:** Fine-grained access control
5. **Audit Logging:** Track all executions

---

## References

### Tools & Libraries
- **Code Execution:** RestrictedPython, Docker, Firecracker
- **GUI Automation:** Playwright, Selenium, Appium, PyAutoGUI
- **Security:** seccomp, AppArmor, SELinux

### Related SPECs
- **SPEC-135:** Multi-Agent Expert Protocol (Execution Expert)
- **SPEC-134:** Perception System (GUI observation)
- **SPEC-137:** Plan-Reflection Loop (execution feedback)

---

**End of SPEC-136**

---

## 📊 Implementation Status

**Last Updated:** January 2025
**Current Status:** 📋 **Not Implemented (0%)**

### ✅ Documentation (100%)

**SPEC Document:**
- ✅ Comprehensive specification document (`SPEC.md`)
- ✅ Defines 3 execution backend types (Tool-Calling, Code Execution, GUI Automation)
- ✅ Unified execution interface (`ExecutionBackend`, `ExecutionEngine`, `ExecutionResult`)
- ✅ Security model (`SandboxConfig`, resource limiting)
- ✅ Implementation plan (4 phases, 10 weeks)
- ✅ Security considerations

### ❌ Missing (100%)

**Phase 1: Tool-Calling (NOT STARTED)**
- ❌ `ToolDefinition` and registry not implemented
- ❌ `ToolCallingBackend` not created
- ❌ Parameter validation not added
- ❌ Standard tool library not created

**Phase 2: Code Execution (NOT STARTED)**
- ❌ Python sandbox not implemented
- ❌ Shell executor not built
- ❌ SQL backend not added
- ❌ Resource limiting not created

**Phase 3: GUI Automation (NOT STARTED)**
- ❌ Playwright integration for web not done
- ❌ Desktop automation (PyAutoGUI) not added
- ❌ Screenshot/OCR pipeline not built
- ❌ Element locators not created

**Phase 4: Unification (NOT STARTED)**
- ❌ `ExecutionEngine` not built
- ❌ Backend selection logic not implemented
- ❌ Execution logging/tracing not added
- ❌ Monitoring dashboards not created

---

## 📋 Implementation Stories

**Story Verification (January 2025):**
- ✅ **US#604:** SPEC-136: Execution System Backends (Done)
  - Confirmed: Related to SPEC-136
  - Status: Done (planning/design phase)
  - Tags: spec-136

**New Stories Created:**
- ✅ **US#873:** SPEC-136 Phase 1: Tool-Calling Backend (Tool Registry & Execution) - HIGH Priority, 10 points, 2 weeks
- ✅ **US#874:** SPEC-136 Phase 2: Code Execution Backend (Python, Shell, SQL Sandboxing) - HIGH Priority, 15 points, 3 weeks
- ✅ **US#875:** SPEC-136 Phase 3: GUI Automation Backend (Web, Desktop, Mobile) - MEDIUM Priority, 13 points, 3 weeks
- ✅ **US#876:** SPEC-136 Phase 4: Execution Engine Unification (Backend Selection, Logging, Monitoring) - MEDIUM Priority, 10 points, 2 weeks

**Total Estimated Effort:** 48 points, 10 weeks

---

## 🎯 Next Steps

1. ✅ **Analysis Complete** - Comprehensive analysis documents created
2. ✅ **Stories Created** - US#873-876 created
3. ⏳ **Begin Phase 1** - Start tool-calling backend implementation (US#873)
4. ⏳ **Update SPEC_INDEX.md** - Change status to "Not Implemented (0%)"
