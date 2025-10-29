# SPEC-059: Unified Macro Intelligence (Enhanced)

**Status:** Enhanced
**Created:** 2024 (Original)
**Updated:** 2025-10-29
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, Platform Architecture

---

## Executive Summary

Enhanced specification for Unified Macro Intelligence adding multi-agent expert roles, role-switching protocols, goal passing mechanisms, and shared context management. This extends the original macro intelligence system with collaborative expert capabilities.

---

## Enhancement Overview

### New Expert Roles

**1. Planning Expert**
- Strategic task decomposition
- Resource allocation
- Timeline estimation
- Risk assessment

**2. Memory Expert**
- Context retrieval and storage
- Pattern recognition
- Historical analysis
- Knowledge base curation

**3. Tool Orchestration Expert**
- Tool selection and routing
- API integration management
- Execution coordination
- Result aggregation

---

## Expert Role Definitions

### Planning Expert

```python
class PlanningExpert(Expert):
    """Strategic planning and decomposition"""

    def __init__(self):
        super().__init__(
            role="planner",
            capabilities=[
                "task_decomposition",
                "dependency_analysis",
                "resource_planning",
                "timeline_estimation"
            ]
        )
        self.decomposer = TaskDecomposer()
        self.optimizer = PlanOptimizer()

    async def handle_request(
        self,
        request: ExpertRequest
    ) -> ExpertResponse:
        """Process planning request"""

        if request.action == "decompose":
            tasks = self.decomposer.decompose(
                goal=request.goal,
                context=request.context
            )
            return ExpertResponse(
                result=tasks,
                confidence=0.9
            )

        elif request.action == "optimize":
            optimized_plan = self.optimizer.optimize(
                plan=request.plan,
                optimization=request.optimization_type
            )
            return ExpertResponse(
                result=optimized_plan,
                confidence=0.85
            )

        elif request.action == "estimate":
            estimation = self._estimate_resources(request.plan)
            return ExpertResponse(
                result=estimation,
                confidence=0.75
            )

    async def collaborate(
        self,
        goal: str,
        other_experts: Dict[str, Expert]
    ) -> CollaborationResult:
        """Collaborate with other experts"""

        # 1. Decompose goal
        tasks = self.decomposer.decompose(goal, {})

        # 2. Consult Memory Expert for context
        if "memory" in other_experts:
            context = await other_experts["memory"].recall_context(goal)
            tasks = self._refine_with_context(tasks, context)

        # 3. Consult Tool Orchestrator for feasibility
        if "tool_orchestrator" in other_experts:
            feasibility = await other_experts["tool_orchestrator"].check_feasibility(tasks)
            tasks = self._adjust_for_feasibility(tasks, feasibility)

        return CollaborationResult(
            plan=tasks,
            collaborators=["memory", "tool_orchestrator"],
            confidence=0.9
        )
```

### Memory Expert

```python
class MemoryExpert(Expert):
    """Contextual memory and knowledge management"""

    def __init__(self, memory_backend: MemoryBackend):
        super().__init__(
            role="memory",
            capabilities=[
                "context_retrieval",
                "pattern_recognition",
                "historical_analysis",
                "knowledge_curation"
            ]
        )
        self.backend = memory_backend
        self.pattern_detector = PatternDetector()

    async def recall_context(
        self,
        query: str,
        filters: Dict[str, Any] = None
    ) -> ContextBundle:
        """Retrieve relevant context"""

        # Semantic search
        memories = await self.backend.semantic_search(
            query=query,
            filters=filters,
            limit=10
        )

        # Detect patterns
        patterns = self.pattern_detector.find_patterns(memories)

        # Build context bundle
        return ContextBundle(
            memories=memories,
            patterns=patterns,
            relevance_scores=[m.score for m in memories],
            summary=self._summarize_context(memories)
        )

    async def store_outcome(
        self,
        task: Task,
        outcome: TaskResult
    ):
        """Store task outcome for future reference"""

        await self.backend.store(
            content=f"{task.description}: {outcome.summary()}",
            tags=[task.type, "outcome", outcome.status],
            metadata={
                "success": outcome.success,
                "duration": outcome.duration,
                "confidence": outcome.confidence
            }
        )

    async def analyze_history(
        self,
        task_type: str,
        timeframe: Optional[timedelta] = None
    ) -> HistoricalAnalysis:
        """Analyze past performance on similar tasks"""

        past_tasks = await self.backend.search(
            filters={
                "type": task_type,
                "timestamp": {
                    "gte": datetime.now() - (timeframe or timedelta(days=30))
                }
            }
        )

        success_rate = sum(1 for t in past_tasks if t.success) / len(past_tasks) if past_tasks else 0
        avg_duration = sum(t.duration for t in past_tasks) / len(past_tasks) if past_tasks else 0

        return HistoricalAnalysis(
            task_type=task_type,
            sample_size=len(past_tasks),
            success_rate=success_rate,
            avg_duration=avg_duration,
            common_issues=self._extract_common_issues(past_tasks),
            recommendations=self._generate_recommendations(past_tasks)
        )
```

### Tool Orchestration Expert

```python
class ToolOrchestrationExpert(Expert):
    """Manage and coordinate tool execution"""

    def __init__(self, tool_registry: ToolRegistry):
        super().__init__(
            role="tool_orchestrator",
            capabilities=[
                "tool_selection",
                "execution_coordination",
                "result_aggregation",
                "error_recovery"
            ]
        )
        self.registry = tool_registry
        self.executor = ToolExecutor()

    async def select_tools(
        self,
        task: Task,
        constraints: Dict[str, Any]
    ) -> List[Tool]:
        """Select appropriate tools for task"""

        # Get all available tools
        available_tools = self.registry.list_tools()

        # Score each tool
        scored_tools = []
        for tool in available_tools:
            score = self._score_tool_fitness(
                tool,
                task.requirements,
                constraints
            )
            scored_tools.append((tool, score))

        # Return top-N tools
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, score in scored_tools[:5]]

    async def execute_orchestrated(
        self,
        task: Task,
        tools: List[Tool]
    ) -> OrchestrationResult:
        """Execute task using multiple tools"""

        results = {}

        # Try tools in order of preference
        for tool in tools:
            try:
                result = await self.executor.execute(
                    tool=tool,
                    parameters=task.parameters
                )
                results[tool.name] = result

                if result.success:
                    return OrchestrationResult(
                        success=True,
                        primary_tool=tool.name,
                        result=result.output,
                        attempted_tools=[tool.name]
                    )
            except Exception as e:
                results[tool.name] = {"error": str(e)}
                continue

        # All tools failed
        return OrchestrationResult(
            success=False,
            primary_tool=None,
            result=None,
            attempted_tools=[t.name for t in tools],
            errors=results
        )

    async def check_feasibility(
        self,
        tasks: List[Task]
    ) -> FeasibilityReport:
        """Check if tasks can be executed with available tools"""

        feasible_tasks = []
        infeasible_tasks = []

        for task in tasks:
            matching_tools = await self.select_tools(task, {})
            if matching_tools:
                feasible_tasks.append(task.id)
            else:
                infeasible_tasks.append({
                    "task_id": task.id,
                    "reason": "No matching tools available"
                })

        return FeasibilityReport(
            feasible_count=len(feasible_tasks),
            infeasible_count=len(infeasible_tasks),
            feasible_tasks=feasible_tasks,
            infeasible_tasks=infeasible_tasks,
            overall_feasibility=len(feasible_tasks) / len(tasks) if tasks else 0
        )
```

---

## Role-Switching Protocol

```python
class RoleSwitchingCoordinator:
    """Manage expert role transitions"""

    def __init__(self, experts: Dict[str, Expert]):
        self.experts = experts
        self.current_expert = None
        self.context_stack = []

    async def route_request(
        self,
        request: ExpertRequest
    ) -> ExpertResponse:
        """Route request to appropriate expert"""

        # Determine which expert should handle this
        target_expert = self._select_expert(request)

        # Check if we need to switch
        if target_expert != self.current_expert:
            await self._perform_switch(
                from_expert=self.current_expert,
                to_expert=target_expert,
                request=request
            )

        # Execute request
        response = await target_expert.handle_request(request)

        return response

    async def _perform_switch(
        self,
        from_expert: Optional[Expert],
        to_expert: Expert,
        request: ExpertRequest
    ):
        """Switch active expert"""

        # Save current context
        if from_expert:
            context = await from_expert.get_context()
            self.context_stack.append({
                "expert": from_expert.role,
                "context": context,
                "timestamp": datetime.now()
            })

        # Load new expert with shared context
        if self.context_stack:
            shared_context = self._build_shared_context()
            await to_expert.load_context(shared_context)

        self.current_expert = to_expert

    def _select_expert(self, request: ExpertRequest) -> Expert:
        """Choose expert based on request type"""

        if request.requires_planning:
            return self.experts["planner"]
        elif request.requires_memory:
            return self.experts["memory"]
        elif request.requires_tools:
            return self.experts["tool_orchestrator"]
        else:
            # Default to general expert
            return self.experts.get("general", list(self.experts.values())[0])
```

---

## Goal Passing Mechanism

```python
class GoalPasser:
    """Pass goals between experts"""

    async def pass_goal(
        self,
        goal: Goal,
        from_expert: Expert,
        to_expert: Expert,
        context: SharedContext
    ) -> GoalHandoff:
        """Transfer goal ownership"""

        # Package goal with context
        goal_package = GoalPackage(
            original_goal=goal,
            current_state=from_expert.get_state(),
            context=context,
            history=self._build_history(from_expert),
            constraints=goal.constraints,
            success_criteria=goal.success_criteria
        )

        # Validate handoff
        if not self._can_handle_goal(to_expert, goal):
            return GoalHandoff(
                success=False,
                reason=f"{to_expert.role} cannot handle goal type: {goal.type}"
            )

        # Transfer
        await to_expert.accept_goal(goal_package)

        # Acknowledge
        return GoalHandoff(
            success=True,
            from_expert=from_expert.role,
            to_expert=to_expert.role,
            goal_id=goal.id,
            timestamp=datetime.now()
        )

    async def decompose_and_distribute(
        self,
        complex_goal: Goal,
        experts: Dict[str, Expert]
    ) -> List[GoalHandoff]:
        """Break goal into subgoals and assign to experts"""

        # Use planning expert to decompose
        planner = experts["planner"]
        subgoals = await planner.decompose_goal(complex_goal)

        # Assign each subgoal to appropriate expert
        handoffs = []
        for subgoal in subgoals:
            best_expert = self._find_best_expert(subgoal, experts)
            handoff = await self.pass_goal(
                goal=subgoal,
                from_expert=planner,
                to_expert=best_expert,
                context=SharedContext(parent_goal=complex_goal)
            )
            handoffs.append(handoff)

        return handoffs
```

---

## Shared Context Management

```python
@dataclass
class SharedContext:
    """Context shared across experts"""
    session_id: str
    goal_stack: List[Goal]
    execution_history: List[ExecutionStep]
    shared_memory: Dict[str, Any]
    constraints: Dict[str, Any]
    metadata: Dict[str, Any]

class SharedContextManager:
    """Manage context accessible by all experts"""

    def __init__(self):
        self.contexts: Dict[str, SharedContext] = {}

    def create_context(
        self,
        session_id: str,
        initial_goal: Goal
    ) -> SharedContext:
        """Create new shared context"""

        context = SharedContext(
            session_id=session_id,
            goal_stack=[initial_goal],
            execution_history=[],
            shared_memory={},
            constraints={},
            metadata={"created_at": datetime.now()}
        )

        self.contexts[session_id] = context
        return context

    def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ):
        """Update shared context"""

        if session_id not in self.contexts:
            raise ValueError(f"Context {session_id} not found")

        context = self.contexts[session_id]

        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                context.shared_memory[key] = value

    def get_context(self, session_id: str) -> SharedContext:
        """Retrieve context"""
        return self.contexts.get(session_id)

    def push_goal(self, session_id: str, goal: Goal):
        """Add goal to stack"""
        context = self.contexts[session_id]
        context.goal_stack.append(goal)

    def pop_goal(self, session_id: str) -> Goal:
        """Remove and return top goal"""
        context = self.contexts[session_id]
        return context.goal_stack.pop() if context.goal_stack else None

    def record_execution(
        self,
        session_id: str,
        step: ExecutionStep
    ):
        """Add execution step to history"""
        context = self.contexts[session_id]
        context.execution_history.append(step)
```

---

## Multi-Expert Collaboration Example

```python
async def complex_task_example():
    """Example: Deploy feature with multi-expert collaboration"""

    # Initialize experts
    experts = {
        "planner": PlanningExpert(),
        "memory": MemoryExpert(memory_backend),
        "tool_orchestrator": ToolOrchestrationExpert(tool_registry)
    }

    # Create shared context
    context_mgr = SharedContextManager()
    context = context_mgr.create_context(
        session_id="deploy-123",
        initial_goal=Goal(description="Deploy feature X to production")
    )

    # 1. Planning Expert decomposes goal
    tasks = await experts["planner"].collaborate(
        goal="Deploy feature X",
        other_experts=experts
    )

    # 2. Memory Expert provides historical context
    history = await experts["memory"].analyze_history(
        task_type="deployment",
        timeframe=timedelta(days=90)
    )

    # Apply lessons from history
    if history.success_rate < 0.8:
        # Add extra validation steps
        tasks = add_validation_steps(tasks, history.common_issues)

    # 3. Tool Orchestrator checks feasibility
    feasibility = await experts["tool_orchestrator"].check_feasibility(tasks)

    if feasibility.overall_feasibility < 0.9:
        # Some tasks are infeasible, need replanning
        tasks = await experts["planner"].replan(
            original_tasks=tasks,
            infeasible=feasibility.infeasible_tasks
        )

    # 4. Execute with coordination
    for task in tasks:
        # Tool Orchestrator executes
        result = await experts["tool_orchestrator"].execute_orchestrated(
            task=task,
            tools=await experts["tool_orchestrator"].select_tools(task, {})
        )

        # Memory Expert stores outcome
        await experts["memory"].store_outcome(task, result)

        # Update shared context
        context_mgr.record_execution(
            session_id="deploy-123",
            step=ExecutionStep(task=task, result=result)
        )

    return "Deployment complete with multi-expert collaboration"
```

---

## Implementation Plan

### Phase 1: Expert Roles (Weeks 1-2)
- [ ] Implement PlanningExpert
- [ ] Implement MemoryExpert
- [ ] Implement ToolOrchestrationExpert

### Phase 2: Collaboration (Weeks 3-4)
- [ ] Build RoleSwitchingCoordinator
- [ ] Implement GoalPasser
- [ ] Create collaboration protocols

### Phase 3: Context Management (Weeks 5-6)
- [ ] Build SharedContextManager
- [ ] Implement context passing
- [ ] Add context persistence

### Phase 4: Integration (Weeks 7-8)
- [ ] Integrate with existing macro intelligence
- [ ] Add monitoring/metrics
- [ ] Create orchestration examples

---

## References

### Related SPECs
- **SPEC-135:** Multi-Agent Expert Protocol (expert communication)
- **SPEC-137:** Agent Plan-Reflection Loop (planning integration)
- **SPEC-063:** Agentic Core Execution (execution layer)

---

**End of SPEC-059 (Enhanced)**
