# SPEC-063: Agentic Core Execution (Enhanced)

**Status:** Enhanced
**Created:** 2024 (Original)
**Updated:** 2025-10-29
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, System Architecture

---

## Executive Summary

Enhanced specification for Agentic Core Execution that modularizes the agent-core into distinct subsystems: Perceiver, Reasoner, Reflector, and Executor. Each module has well-defined APIs and can be orchestrated through async messaging or queue-based coordination.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                 Agentic Core                            │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Perceiver   │───▶│   Reasoner   │                 │
│  │  (Observe)   │    │  (Decide)    │                 │
│  └──────────────┘    └───────┬──────┘                 │
│         ▲                     │                         │
│         │                     ▼                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │  Reflector   │◀───│   Executor   │                 │
│  │  (Learn)     │    │  (Act)       │                 │
│  └──────────────┘    └──────────────┘                 │
│                                                         │
│         [Orchestration Layer]                          │
└────────────────────────────────────────────────────────┘
```

---

## Module 1: Perceiver

**Purpose:** Observe and understand the environment

### Core API

```python
class Perceiver(ABC):
    """Base perceiver interface"""

    @abstractmethod
    async def perceive(
        self,
        input: PerceptionInput
    ) -> PerceptionResult:
        """Process input and extract meaning"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """List perception capabilities"""
        pass

@dataclass
class PerceptionInput:
    """Input to perceiver"""
    type: str  # text, image, structured, etc.
    data: Any
    context: Dict[str, Any]
    timestamp: datetime

@dataclass
class PerceptionResult:
    """Perceiver output"""
    observations: List[Observation]
    entities: List[Entity]
    relationships: List[Relationship]
    confidence: float
    metadata: Dict[str, Any]
```

### Implementation

```python
class MultimodalPerceiver(Perceiver):
    """Concrete perceiver with multiple modalities"""

    def __init__(self):
        self.text_processor = TextPerceptionModule()
        self.vision_processor = VisionPerceptionModule()
        self.structured_processor = StructuredPerceptionModule()

    async def perceive(
        self,
        input: PerceptionInput
    ) -> PerceptionResult:
        """Route to appropriate processor"""

        if input.type == "text":
            return await self.text_processor.process(input.data)
        elif input.type == "image":
            return await self.vision_processor.process(input.data)
        elif input.type == "structured":
            return await self.structured_processor.process(input.data)
        else:
            raise ValueError(f"Unsupported input type: {input.type}")

    def get_capabilities(self) -> List[str]:
        return ["text", "image", "structured", "multimodal"]

class TextPerceptionModule:
    """Process text inputs"""

    async def process(self, text: str) -> PerceptionResult:
        # NER, sentiment, intent extraction
        entities = await self.extract_entities(text)
        sentiment = await self.analyze_sentiment(text)
        intent = await self.detect_intent(text)

        return PerceptionResult(
            observations=[
                Observation(type="text", content=text)
            ],
            entities=entities,
            relationships=[],
            confidence=0.9,
            metadata={"sentiment": sentiment, "intent": intent}
        )
```

---

## Module 2: Reasoner

**Purpose:** Make decisions based on observations

### Core API

```python
class Reasoner(ABC):
    """Base reasoner interface"""

    @abstractmethod
    async def reason(
        self,
        perception: PerceptionResult,
        goal: Goal,
        context: ReasoningContext
    ) -> Decision:
        """Generate action decision"""
        pass

    @abstractmethod
    async def plan(
        self,
        goal: Goal,
        context: ReasoningContext
    ) -> Plan:
        """Create multi-step plan"""
        pass

@dataclass
class Decision:
    """Reasoning output"""
    action: Action
    reasoning: str  # Explanation
    alternatives: List[Action]  # Other options considered
    confidence: float
    requires_approval: bool

@dataclass
class ReasoningContext:
    """Context for reasoning"""
    memory: MemoryContext
    constraints: List[Constraint]
    preferences: Dict[str, Any]
    history: List[Decision]
```

### Implementation

```python
class LLMReasoner(Reasoner):
    """LLM-based reasoning engine"""

    def __init__(self, llm: LLM, memory: MemoryExpert):
        self.llm = llm
        self.memory = memory

    async def reason(
        self,
        perception: PerceptionResult,
        goal: Goal,
        context: ReasoningContext
    ) -> Decision:
        """Generate decision using LLM"""

        # Recall relevant context
        relevant_memories = await self.memory.recall(
            query=str(perception),
            limit=5
        )

        # Build reasoning prompt
        prompt = self._build_reasoning_prompt(
            perception,
            goal,
            context,
            relevant_memories
        )

        # Generate decision
        response = await self.llm.generate(prompt)

        # Parse and validate
        decision = self._parse_decision(response)

        return decision

    async def plan(
        self,
        goal: Goal,
        context: ReasoningContext
    ) -> Plan:
        """Create multi-step plan"""

        prompt = f"""
        Goal: {goal.description}
        Context: {context}

        Create a step-by-step plan to achieve this goal.
        For each step, specify:
        1. Action to take
        2. Expected outcome
        3. Dependencies on previous steps
        4. Success criteria
        """

        response = await self.llm.generate(prompt)
        plan = self._parse_plan(response)

        return plan

    def _build_reasoning_prompt(
        self,
        perception: PerceptionResult,
        goal: Goal,
        context: ReasoningContext,
        memories: List[Memory]
    ) -> str:
        """Construct reasoning prompt"""

        return f"""
        Observations:
        {self._format_observations(perception)}

        Goal: {goal.description}

        Relevant Context:
        {self._format_memories(memories)}

        Constraints:
        {self._format_constraints(context.constraints)}

        Based on the above, what action should be taken?
        Provide:
        1. Recommended action
        2. Reasoning behind this choice
        3. Alternative options
        4. Confidence level (0-1)
        """
```

---

## Module 3: Executor

**Purpose:** Execute decided actions

### Core API

```python
class Executor(ABC):
    """Base executor interface"""

    @abstractmethod
    async def execute(
        self,
        action: Action,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute action"""
        pass

    @abstractmethod
    async def validate(
        self,
        action: Action
    ) -> ValidationResult:
        """Check if action can be executed"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """List execution capabilities"""
        pass

@dataclass
class ExecutionContext:
    """Context for execution"""
    session_id: str
    timeout: int
    retry_policy: RetryPolicy
    rollback_enabled: bool
    dry_run: bool

@dataclass
class ExecutionResult:
    """Execution output"""
    success: bool
    output: Any
    error: Optional[str]
    duration: float
    side_effects: List[SideEffect]
    metadata: Dict[str, Any]
```

### Implementation

```python
class MultiBackendExecutor(Executor):
    """Executor with multiple backends"""

    def __init__(self):
        self.tool_backend = ToolExecutionBackend()
        self.code_backend = CodeExecutionBackend()
        self.gui_backend = GUIExecutionBackend()

    async def execute(
        self,
        action: Action,
        context: ExecutionContext
    ) -> ExecutionResult:
        """Route to appropriate backend"""

        # Validate first
        validation = await self.validate(action)
        if not validation.valid:
            return ExecutionResult(
                success=False,
                output=None,
                error=validation.error,
                duration=0,
                side_effects=[],
                metadata={}
            )

        # Select backend
        backend = self._select_backend(action)

        # Execute with retry
        if context.retry_policy:
            result = await self._execute_with_retry(
                backend,
                action,
                context.retry_policy
            )
        else:
            result = await backend.execute(action, context)

        return result

    async def validate(
        self,
        action: Action
    ) -> ValidationResult:
        """Pre-execution validation"""

        # Check permissions
        if not self._has_permission(action):
            return ValidationResult(
                valid=False,
                error="Insufficient permissions"
            )

        # Check resource availability
        if not await self._resources_available(action):
            return ValidationResult(
                valid=False,
                error="Required resources unavailable"
            )

        # Check safety
        if not self._is_safe(action):
            return ValidationResult(
                valid=False,
                error="Action may have unsafe side effects"
            )

        return ValidationResult(valid=True)

    def get_capabilities(self) -> List[str]:
        return ["tool_calling", "code_execution", "gui_automation"]
```

---

## Module 4: Reflector

**Purpose:** Learn from outcomes and improve

### Core API

```python
class Reflector(ABC):
    """Base reflector interface"""

    @abstractmethod
    async def reflect(
        self,
        perception: PerceptionResult,
        decision: Decision,
        execution: ExecutionResult,
        goal: Goal
    ) -> Reflection:
        """Analyze outcome and generate insights"""
        pass

    @abstractmethod
    async def update_knowledge(
        self,
        reflection: Reflection
    ):
        """Update agent's knowledge base"""
        pass

@dataclass
class Reflection:
    """Reflection output"""
    outcome_analysis: str  # What happened?
    decision_quality: float  # Was the decision good?
    lessons_learned: List[str]  # What to remember?
    improvements: List[str]  # What to do differently?
    confidence: float
```

### Implementation

```python
class AdaptiveReflector(Reflector):
    """Self-improving reflector"""

    def __init__(self, memory: MemoryExpert):
        self.memory = memory
        self.analyzer = OutcomeAnalyzer()

    async def reflect(
        self,
        perception: PerceptionResult,
        decision: Decision,
        execution: ExecutionResult,
        goal: Goal
    ) -> Reflection:
        """Analyze execution outcome"""

        # Evaluate success
        success_score = self._evaluate_success(
            execution,
            goal.success_criteria
        )

        # Analyze decision quality
        decision_quality = self._analyze_decision(
            decision,
            execution,
            success_score
        )

        # Extract lessons
        lessons = await self._extract_lessons(
            perception,
            decision,
            execution,
            success_score
        )

        # Generate improvements
        improvements = await self._suggest_improvements(
            decision,
            execution,
            lessons
        )

        return Reflection(
            outcome_analysis=self._summarize_outcome(execution),
            decision_quality=decision_quality,
            lessons_learned=lessons,
            improvements=improvements,
            confidence=0.8
        )

    async def update_knowledge(
        self,
        reflection: Reflection
    ):
        """Store lessons in memory"""

        for lesson in reflection.lessons_learned:
            await self.memory.store_memory(
                content=lesson,
                tags=["lesson", "reflection"],
                context={"type": "learning"}
            )

    async def _extract_lessons(
        self,
        perception: PerceptionResult,
        decision: Decision,
        execution: ExecutionResult,
        success_score: float
    ) -> List[str]:
        """Extract actionable lessons"""

        lessons = []

        if success_score > 0.8:
            # Success lesson
            lessons.append(
                f"In situation '{perception.observations[0]}', "
                f"action '{decision.action}' works well"
            )
        elif success_score < 0.3:
            # Failure lesson
            lessons.append(
                f"In situation '{perception.observations[0]}', "
                f"action '{decision.action}' should be avoided. "
                f"Error: {execution.error}"
            )

        return lessons
```

---

## Orchestration Mechanism

### Queue-Based Orchestration

```python
class QueueBasedOrchestrator:
    """Async queue-based coordination"""

    def __init__(
        self,
        perceiver: Perceiver,
        reasoner: Reasoner,
        executor: Executor,
        reflector: Reflector
    ):
        self.perceiver = perceiver
        self.reasoner = reasoner
        self.executor = executor
        self.reflector = reflector

        self.perception_queue = asyncio.Queue()
        self.decision_queue = asyncio.Queue()
        self.execution_queue = asyncio.Queue()
        self.reflection_queue = asyncio.Queue()

    async def start(self):
        """Start orchestration loop"""

        # Start processing tasks
        tasks = [
            self._perception_loop(),
            self._reasoning_loop(),
            self._execution_loop(),
            self._reflection_loop()
        ]

        await asyncio.gather(*tasks)

    async def _perception_loop(self):
        """Process perception queue"""

        while True:
            input = await self.perception_queue.get()

            result = await self.perceiver.perceive(input)

            # Pass to reasoner
            await self.decision_queue.put({
                "perception": result,
                "goal": input.context.get("goal")
            })

    async def _reasoning_loop(self):
        """Process reasoning queue"""

        while True:
            item = await self.decision_queue.get()

            decision = await self.reasoner.reason(
                perception=item["perception"],
                goal=item["goal"],
                context=ReasoningContext()
            )

            # Pass to executor
            await self.execution_queue.put({
                "decision": decision,
                "perception": item["perception"],
                "goal": item["goal"]
            })

    async def _execution_loop(self):
        """Process execution queue"""

        while True:
            item = await self.execution_queue.get()

            result = await self.executor.execute(
                action=item["decision"].action,
                context=ExecutionContext()
            )

            # Pass to reflector
            await self.reflection_queue.put({
                "perception": item["perception"],
                "decision": item["decision"],
                "execution": result,
                "goal": item["goal"]
            })

    async def _reflection_loop(self):
        """Process reflection queue"""

        while True:
            item = await self.reflection_queue.get()

            reflection = await self.reflector.reflect(
                perception=item["perception"],
                decision=item["decision"],
                execution=item["execution"],
                goal=item["goal"]
            )

            # Update knowledge
            await self.reflector.update_knowledge(reflection)
```

### Direct Orchestration

```python
class DirectOrchestrator:
    """Synchronous/direct orchestration"""

    def __init__(
        self,
        perceiver: Perceiver,
        reasoner: Reasoner,
        executor: Executor,
        reflector: Reflector
    ):
        self.perceiver = perceiver
        self.reasoner = reasoner
        self.executor = executor
        self.reflector = reflector

    async def process_task(
        self,
        input: PerceptionInput,
        goal: Goal
    ) -> TaskResult:
        """Execute complete PRER cycle"""

        # 1. Perceive
        perception = await self.perceiver.perceive(input)

        # 2. Reason
        decision = await self.reasoner.reason(
            perception=perception,
            goal=goal,
            context=ReasoningContext()
        )

        # 3. Execute
        execution = await self.executor.execute(
            action=decision.action,
            context=ExecutionContext()
        )

        # 4. Reflect
        reflection = await self.reflector.reflect(
            perception=perception,
            decision=decision,
            execution=execution,
            goal=goal
        )

        # 5. Learn
        await self.reflector.update_knowledge(reflection)

        return TaskResult(
            success=execution.success,
            output=execution.output,
            reflection=reflection
        )
```

---

## Implementation Plan

### Phase 1: Module APIs (Weeks 1-2)
- [ ] Define Perceiver interface
- [ ] Define Reasoner interface
- [ ] Define Executor interface
- [ ] Define Reflector interface

### Phase 2: Implementations (Weeks 3-6)
- [ ] Implement MultimodalPerceiver
- [ ] Implement LLMReasoner
- [ ] Implement MultiBackendExecutor
- [ ] Implement AdaptiveReflector

### Phase 3: Orchestration (Weeks 7-8)
- [ ] Build QueueBasedOrchestrator
- [ ] Build DirectOrchestrator
- [ ] Add monitoring/logging

### Phase 4: Integration (Weeks 9-10)
- [ ] Integrate with existing systems
- [ ] Performance optimization
- [ ] Testing and validation

---

## References

### Related SPECs
- **SPEC-134:** Perception System (Perceiver module)
- **SPEC-136:** Execution Backends (Executor module)
- **SPEC-137:** Plan-Reflection Loop (Reflector module)
- **SPEC-135:** Multi-Agent Protocol (Orchestration)

---

**End of SPEC-063 (Enhanced)**
