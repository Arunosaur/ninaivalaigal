# SPEC-135: Multi-Agent Expert Protocol

**Status:** Draft
**Created:** 2025-10-28
**Updated:** 2025-10-28
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, System Architecture

---

## Executive Summary

Define a formal protocol for multi-agent collaboration in Ninaivalaigal, enabling specialized expert agents to work together on complex tasks. This SPEC establishes message schemas, routing logic, expert roles, and collaboration patterns that allow agents to leverage specialized capabilities while maintaining coherent execution.

---

## Problem Statement

Current single-agent architectures face limitations:
- **Jack-of-all-trades problem:** One agent trying to handle all tasks leads to mediocre performance
- **Lack of specialization:** Cannot leverage domain-specific expertise effectively
- **No collaboration mechanism:** Agents cannot delegate tasks or share intermediate results
- **Limited scalability:** Complex tasks require coordination that single agents struggle with

This prevents Ninaivalaigal from tackling sophisticated workflows that require multiple perspectives or specialized skills.

---

## Goals

### Primary Goals
1. Formalize expert-agent communication protocol
2. Define specialized expert roles and responsibilities
3. Enable seamless task delegation and collaboration
4. Implement intelligent routing and fallback strategies

### Non-Goals
1. Training expert models from scratch
2. Implementing specific expert backends (covered in SPEC-136)
3. Building agent marketplace or discovery

---

## Expert Roles

### 1. Planning Expert

**Responsibilities:**
- Break down complex goals into actionable steps
- Generate execution plans with dependencies
- Optimize task scheduling
- Handle plan refinement and adaptation

**Capabilities:**
```python
class PlanningExpert:
    def decompose_task(
        self,
        goal: str,
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """Break goal into steps"""
        pass

    def optimize_plan(
        self,
        plan: ExecutionPlan,
        constraints: List[Constraint]
    ) -> ExecutionPlan:
        """Optimize step ordering and resource allocation"""
        pass

    def adapt_plan(
        self,
        plan: ExecutionPlan,
        execution_result: ExecutionResult
    ) -> ExecutionPlan:
        """Adjust plan based on execution feedback"""
        pass
```

**Example Interaction:**
```
User: "Deploy the new feature to production"

Planning Expert:
1. Run test suite
2. Build Docker image
3. Push to registry
4. Update K8s manifests
5. Apply to staging
6. Run smoke tests
7. Apply to production
8. Verify deployment
```

---

### 2. Memory Expert

**Responsibilities:**
- Store and retrieve contextual information
- Manage working memory during task execution
- Index and search past interactions
- Provide relevant context for decision-making

**Capabilities:**
```python
class MemoryExpert:
    def store_memory(
        self,
        content: str,
        tags: List[str],
        context: Dict[str, Any]
    ) -> MemoryID:
        """Store new memory"""
        pass

    def recall(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Retrieve relevant memories"""
        pass

    def update_context(
        self,
        session_id: str,
        new_info: Dict[str, Any]
    ) -> None:
        """Update working memory for session"""
        pass

    def get_working_memory(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get current context"""
        pass
```

**Integration with Ninaivalaigal:**
```python
# Leverage existing memory infrastructure
memory_expert = MemoryExpert(
    backend="ninaivalaigal",  # Use existing GraphOps + pgvector
    config=MemoryConfig(
        embedding_model="text-embedding-3-small",
        graph_db="apache_age",
        vector_db="pgvector"
    )
)
```

---

### 3. Execution Expert

**Responsibilities:**
- Execute individual plan steps
- Interact with tools and APIs
- Handle low-level operations
- Report execution results

**Capabilities:**
```python
class ExecutionExpert:
    def execute_step(
        self,
        step: PlanStep,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single step"""
        pass

    def execute_tool_call(
        self,
        tool: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Call external tool"""
        pass

    def interact_with_gui(
        self,
        action: GUIAction
    ) -> ActionResult:
        """Perform GUI interaction"""
        pass
```

**Tool Registry:**
```python
execution_expert.register_tool(
    name="run_command",
    handler=CommandExecutor(),
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string", "optional": True}
        }
    }
)
```

---

### 4. Reflection Expert

**Responsibilities:**
- Analyze execution results
- Detect errors and anomalies
- Suggest corrections and improvements
- Learn from failures

**Capabilities:**
```python
class ReflectionExpert:
    def analyze_result(
        self,
        step: PlanStep,
        result: ExecutionResult
    ) -> Analysis:
        """Analyze execution outcome"""
        pass

    def detect_errors(
        self,
        execution_trace: List[ExecutionResult]
    ) -> List[Error]:
        """Identify failures or issues"""
        pass

    def suggest_repair(
        self,
        error: Error,
        context: Dict[str, Any]
    ) -> RepairStrategy:
        """Propose fix for error"""
        pass

    def learn_from_failure(
        self,
        failure: Failure,
        resolution: Resolution
    ) -> None:
        """Store failure pattern for future reference"""
        pass
```

**Reflection Patterns:**
- **Post-hoc Reflection:** Analyze after execution
- **Anticipatory Reflection:** Predict issues before execution
- **Verbal Reinforcement:** Learn from human feedback

---

### 5. Error Handler Expert

**Responsibilities:**
- Handle exceptions and failures gracefully
- Implement retry logic with exponential backoff
- Route errors to appropriate experts
- Maintain system stability

**Capabilities:**
```python
class ErrorHandlerExpert:
    def handle_error(
        self,
        error: Exception,
        context: ExecutionContext
    ) -> ErrorResponse:
        """Handle error and determine recovery strategy"""
        pass

    def retry_with_backoff(
        self,
        operation: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> Any:
        """Retry failed operation"""
        pass

    def escalate_error(
        self,
        error: Error,
        escalation_level: str
    ) -> None:
        """Escalate to human or higher-level expert"""
        pass
```

**Error Classification:**
```python
class ErrorType(Enum):
    RETRIABLE = "retriable"  # Network timeout, rate limit
    REPAIRABLE = "repairable"  # Logic error, needs plan adjustment
    FATAL = "fatal"  # Unrecoverable, needs human intervention
    IGNORABLE = "ignorable"  # Non-critical, continue execution
```

---

## Message Schema

### Core Message Structure

```python
@dataclass
class AgentMessage:
    """Base message for inter-agent communication"""
    id: str  # Unique message ID
    sender: str  # Sending agent/expert ID
    receiver: str  # Target agent/expert ID
    type: MessageType  # Request, response, broadcast, etc.
    content: Dict[str, Any]  # Payload
    context: Dict[str, Any]  # Execution context
    timestamp: datetime
    parent_id: Optional[str] = None  # For threading
    priority: int = 5  # 1 (highest) to 10 (lowest)
    requires_response: bool = True

class MessageType(Enum):
    REQUEST = "request"  # Ask for action
    RESPONSE = "response"  # Reply to request
    BROADCAST = "broadcast"  # Notify all
    ERROR = "error"  # Report failure
    STATUS = "status"  # Progress update
    DELEGATION = "delegation"  # Delegate subtask
```

### Message Examples

**1. Task Delegation**
```python
delegation_msg = AgentMessage(
    id="msg-001",
    sender="planner",
    receiver="executor",
    type=MessageType.DELEGATION,
    content={
        "task": "run_tests",
        "parameters": {
            "test_suite": "integration",
            "environment": "staging"
        },
        "timeout": 300
    },
    context={
        "session_id": "sess-123",
        "parent_task": "deploy_feature",
        "step_index": 1
    },
    requires_response=True
)
```

**2. Execution Result**
```python
result_msg = AgentMessage(
    id="msg-002",
    sender="executor",
    receiver="planner",
    type=MessageType.RESPONSE,
    parent_id="msg-001",
    content={
        "status": "success",
        "result": {
            "tests_passed": 45,
            "tests_failed": 0,
            "duration": 123.5
        },
        "logs": "..."
    },
    context={
        "session_id": "sess-123"
    }
)
```

**3. Error Report**
```python
error_msg = AgentMessage(
    id="msg-003",
    sender="executor",
    receiver="error_handler",
    type=MessageType.ERROR,
    content={
        "error_type": "network_timeout",
        "error_message": "Connection to API timed out",
        "retry_count": 2,
        "is_retriable": True
    },
    context={
        "session_id": "sess-123",
        "failed_operation": "api_call"
    },
    priority=2  # High priority
)
```

**4. Memory Query**
```python
memory_query_msg = AgentMessage(
    id="msg-004",
    sender="executor",
    receiver="memory",
    type=MessageType.REQUEST,
    content={
        "operation": "recall",
        "query": "previous deployment configuration",
        "filters": {
            "tags": ["deployment", "production"],
            "date_range": {"start": "2025-10-01"}
        },
        "limit": 5
    },
    context={
        "session_id": "sess-123"
    }
)
```

---

## Message Routing

### Routing Logic

```python
class MessageRouter:
    def __init__(self):
        self.experts: Dict[str, Expert] = {}
        self.message_queue: Queue[AgentMessage] = Queue()
        self.routing_table: Dict[str, str] = {}

    def register_expert(self, role: str, expert: Expert):
        """Register expert with routing table"""
        self.experts[role] = expert
        self.routing_table[role] = expert.id

    def route(self, message: AgentMessage) -> None:
        """Route message to appropriate expert"""
        if message.receiver in self.experts:
            self.experts[message.receiver].receive(message)
        elif message.receiver == "broadcast":
            self.broadcast(message)
        else:
            raise RoutingError(f"Unknown receiver: {message.receiver}")

    def broadcast(self, message: AgentMessage) -> None:
        """Send message to all experts"""
        for expert in self.experts.values():
            expert.receive(message)
```

### Priority Queue

```python
class PriorityMessageQueue:
    def __init__(self):
        self.queue: PriorityQueue[Tuple[int, AgentMessage]] = PriorityQueue()

    def enqueue(self, message: AgentMessage):
        # Lower priority number = higher priority
        self.queue.put((message.priority, message))

    def dequeue(self) -> AgentMessage:
        _, message = self.queue.get()
        return message
```

---

## Collaboration Patterns

### 1. Sequential Delegation

**Pattern:** Task A → Task B → Task C

```python
async def sequential_workflow(goal: str):
    # Planning phase
    plan = await planner.create_plan(goal)

    # Sequential execution
    for step in plan.steps:
        result = await executor.execute(step)

        # Reflection after each step
        analysis = await reflector.analyze(step, result)

        if analysis.has_errors:
            repair = await reflector.suggest_repair(analysis.error)
            result = await executor.execute(repair)

        # Store result in memory
        await memory.store(result)

    return "Complete"
```

### 2. Parallel Execution

**Pattern:** Task A splits into [B1, B2, B3] → Merge

```python
async def parallel_workflow(goal: str):
    # Decompose into parallel subtasks
    plan = await planner.decompose(goal, strategy="parallel")

    # Execute in parallel
    tasks = [executor.execute(step) for step in plan.parallel_steps]
    results = await asyncio.gather(*tasks)

    # Merge results
    merged = await planner.merge_results(results)

    return merged
```

### 3. Query-Response

**Pattern:** Agent asks Memory Expert for context

```python
async def query_workflow(question: str):
    # Executor needs context
    memory_query = AgentMessage(
        sender="executor",
        receiver="memory",
        type=MessageType.REQUEST,
        content={
            "operation": "recall",
            "query": question
        }
    )

    # Memory Expert responds
    response = await memory.handle_message(memory_query)

    # Use context in execution
    result = await executor.execute_with_context(
        task,
        context=response.content
    )

    return result
```

### 4. Error Recovery

**Pattern:** Execution fails → Error Handler → Reflection → Retry

```python
async def error_recovery_workflow(task: Task):
    try:
        result = await executor.execute(task)
    except Exception as e:
        # Handle error
        error_response = await error_handler.handle(e)

        if error_response.is_retriable:
            # Retry with backoff
            result = await error_handler.retry_with_backoff(
                lambda: executor.execute(task)
            )
        elif error_response.is_repairable:
            # Get repair strategy
            repair = await reflector.suggest_repair(e)
            result = await executor.execute(repair.new_task)
        else:
            # Escalate to human
            await error_handler.escalate(e)
            raise

    return result
```

---

## Fallback Strategies

### 1. Expert Unavailable

```python
class FallbackStrategy:
    def __init__(self):
        self.fallback_map: Dict[str, str] = {
            "planner": "general_agent",  # Use general LLM
            "memory": "local_cache",  # Use in-memory cache
            "executor": "basic_executor",  # Limited capabilities
        }

    def get_fallback(self, expert: str) -> str:
        return self.fallback_map.get(expert, "general_agent")
```

### 2. Timeout Handling

```python
async def execute_with_timeout(
    expert: Expert,
    message: AgentMessage,
    timeout: int = 30
):
    try:
        return await asyncio.wait_for(
            expert.process(message),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        # Use fallback or return partial result
        return fallback_expert.process_simple(message)
```

### 3. Consensus Mechanism

```python
async def consensus_decision(question: str, experts: List[Expert]):
    """Ask multiple experts and take majority vote"""
    responses = await asyncio.gather(*[
        expert.answer(question) for expert in experts
    ])

    # Vote
    votes = Counter([r.answer for r in responses])
    consensus = votes.most_common(1)[0][0]

    return consensus
```

---

## Implementation Plan

### Phase 1: Core Protocol (Weeks 1-2)
- [ ] Implement `AgentMessage` data structures
- [ ] Build `MessageRouter` with priority queue
- [ ] Create base `Expert` interface
- [ ] Set up message threading and tracing

### Phase 2: Expert Roles (Weeks 3-4)
- [ ] Implement `PlanningExpert`
- [ ] Implement `MemoryExpert` (integrate with existing infra)
- [ ] Implement `ExecutionExpert`
- [ ] Implement `ReflectionExpert`
- [ ] Implement `ErrorHandlerExpert`

### Phase 3: Collaboration Patterns (Weeks 5-6)
- [ ] Build sequential workflow engine
- [ ] Build parallel execution engine
- [ ] Implement query-response pattern
- [ ] Create error recovery logic

### Phase 4: Fallback & Resilience (Weeks 7-8)
- [ ] Implement fallback strategies
- [ ] Add timeout handling
- [ ] Build consensus mechanism
- [ ] Create circuit breakers

---

## Testing Strategy

```python
# Test message routing
def test_message_routing():
    router = MessageRouter()
    planner = PlanningExpert()
    router.register_expert("planner", planner)

    msg = AgentMessage(
        sender="user",
        receiver="planner",
        type=MessageType.REQUEST,
        content={"goal": "test"}
    )

    router.route(msg)
    assert planner.received_messages[-1] == msg

# Test sequential workflow
async def test_sequential_workflow():
    result = await sequential_workflow("Deploy feature X")
    assert result == "Complete"

# Test error recovery
async def test_error_recovery():
    faulty_task = Task(action="fail_once")
    result = await error_recovery_workflow(faulty_task)
    assert result.success  # Should succeed after retry
```

---

## References

### Research Papers
1. **AutoGPT** - Multi-agent autonomous system
2. **MetaGPT** - Multi-agent software development framework
3. **Reflexion** - Language agents with verbal reinforcement learning
4. **CAMEL** - Communicative agents for "mind" exploration
5. **ChatDev** - Multi-agent collaborative software development

### Related SPECs
- **SPEC-137:** Agent Plan-Reflection Loop (DPPM cycle)
- **SPEC-134:** Perception System (Perception Expert)
- **SPEC-136:** Execution Backends (Execution Expert tools)

---

**End of SPEC-135**

---

## 📊 Implementation Status

**Last Updated:** January 2025
**Current Status:** 📋 **Not Implemented (0%)**

### ✅ Documentation (100%)

**SPEC Document:**
- ✅ Comprehensive specification document (`SPEC.md`)
- ✅ Defines 5 expert roles (Planning, Memory, Execution, Reflection, Error Handler)
- ✅ Message schema (`AgentMessage`, `MessageType`)
- ✅ Message routing (`MessageRouter`, `PriorityMessageQueue`)
- ✅ Collaboration patterns (Sequential, Parallel, Query-Response, Error Recovery)
- ✅ Fallback strategies
- ✅ Implementation plan (4 phases, 8 weeks)
- ✅ Testing strategy

### ❌ Missing (100%)

**Phase 1: Core Protocol (NOT STARTED)**
- ❌ `AgentMessage` data structures not implemented
- ❌ `MessageRouter` with priority queue not created
- ❌ Base `Expert` interface not created
- ❌ Message threading and tracing not implemented

**Phase 2: Expert Roles (NOT STARTED)**
- ❌ `PlanningExpert` not implemented
- ❌ `MemoryExpert` not implemented (should integrate with existing infra)
- ❌ `ExecutionExpert` not implemented
- ❌ `ReflectionExpert` not implemented
- ❌ `ErrorHandlerExpert` not implemented

**Phase 3: Collaboration Patterns (NOT STARTED)**
- ❌ Sequential workflow engine not built
- ❌ Parallel execution engine not built
- ❌ Query-response pattern not implemented
- ❌ Error recovery logic not created

**Phase 4: Fallback & Resilience (NOT STARTED)**
- ❌ Fallback strategies not implemented
- ❌ Timeout handling not added
- ❌ Consensus mechanism not built
- ❌ Circuit breakers not created

---

## 📋 Implementation Stories

**Story Verification (January 2025):**
- ✅ **US#603:** SPEC-135: Multi-Agent Expert Protocol (Done)
  - Confirmed: Related to SPEC-135
  - Status: Done (planning/design phase)
  - Tags: spec-135

**New Stories Created:**
- ✅ **US#869:** SPEC-135 Phase 1: Core Protocol (Message Schema & Routing) - HIGH Priority, 10 points, 2 weeks
- ✅ **US#870:** SPEC-135 Phase 2: Expert Roles (Planning, Memory, Execution, Reflection, Error Handler) - HIGH Priority, 15 points, 2 weeks
- ✅ **US#871:** SPEC-135 Phase 3: Collaboration Patterns (Sequential, Parallel, Query-Response, Error Recovery) - MEDIUM Priority, 13 points, 2 weeks
- ✅ **US#872:** SPEC-135 Phase 4: Fallback & Resilience (Timeouts, Consensus, Circuit Breakers) - MEDIUM Priority, 10 points, 2 weeks

**Total Estimated Effort:** 48 points, 8 weeks

---

## 🎯 Next Steps

1. ✅ **Analysis Complete** - Comprehensive analysis documents created
2. ✅ **Stories Created** - US#869-872 created
3. ⏳ **Begin Phase 1** - Start core protocol implementation (US#869)
4. ⏳ **Update SPEC_INDEX.md** - Change status to "Not Implemented (0%)"
5. ⏳ **Coordinate with SPEC-059** - Ensure expert role consistency
