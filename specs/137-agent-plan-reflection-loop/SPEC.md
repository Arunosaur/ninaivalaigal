# SPEC-137: Agent Plan-Reflection Loop

**Status:** Draft
**Created:** 2025-10-28
**Updated:** 2025-10-29
**Owner:** AI Engineering Team
**Stakeholders:** Agent Development, AI Research

---

## Executive Summary

Define a formal agent planning and reflection cycle based on the DPPM (Decompose-Plan-Merge) framework, enabling agents to break down complex tasks into manageable subtasks, execute them in parallel, merge results, and reflect on outcomes to improve future performance.

---

## Problem Statement

Current agent systems struggle with:
- **Sequential bottlenecks:** Tasks executed one-by-one waste time
- **Lack of decomposition:** Complex goals not broken down effectively
- **No self-correction:** Agents don't learn from failures
- **Poor plan adaptation:** Cannot adjust plans based on execution feedback
- **Missing reflection:** No systematic analysis of success/failure patterns

This limits agents to simple, linear workflows and prevents them from handling sophisticated multi-step tasks.

---

## Goals

### Primary Goals
1. Formalize DPPM (Decompose-Plan-Merge) cycle
2. Enable parallel subplan generation and execution
3. Implement reflection on execution results
4. Support plan repair and adaptation
5. Build feedback loop for continuous improvement

### Non-Goals
1. Training custom planning models
2. Implementing distributed task schedulers
3. Building human-in-the-loop interfaces (separate concern)

---

## DPPM Framework

### Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DPPM Cycle                            │
│                                                          │
│  ┌──────────────┐                                       │
│  │   DECOMPOSE  │  Break goal into subtasks             │
│  │              │  Identify dependencies                │
│  └──────┬───────┘                                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                       │
│  │     PLAN     │  Create execution plan                │
│  │              │  Assign resources/experts             │
│  └──────┬───────┘  Schedule parallel/sequential steps   │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                       │
│  │   EXECUTE    │  Run subtasks (parallel where possible)│
│  │              │  Collect results                      │
│  └──────┬───────┘                                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                       │
│  │     MERGE    │  Combine subresults                   │
│  │              │  Resolve conflicts                    │
│  └──────┬───────┘                                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                       │
│  │   REFLECT    │  Analyze success/failure              │
│  │              │  Update memory/learn                  │
│  └──────┬───────┘  Suggest improvements                 │
│         │                                                │
│         └──────────► Repeat if needed                   │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Decomposition

### Task Decomposition

```python
@dataclass
class Task:
    """Atomic task unit"""
    id: str
    description: str
    goal: str
    dependencies: List[str]  # IDs of prerequisite tasks
    estimated_duration: int  # seconds
    required_capabilities: List[str]
    priority: int = 5
    metadata: Dict[str, Any] = None

class TaskDecomposer:
    """Break complex goals into subtasks"""

    def decompose(
        self,
        goal: str,
        context: Dict[str, Any],
        strategy: str = "hierarchical"
    ) -> List[Task]:
        """Decompose goal into tasks"""

        # Use LLM to generate decomposition
        prompt = f"""
        Goal: {goal}
        Context: {context}

        Break this goal into 3-7 concrete, actionable subtasks.
        For each task, identify:
        1. Clear description
        2. Dependencies on other tasks
        3. Required capabilities
        4. Estimated duration

        Format as JSON array of tasks.
        """

        response = self.llm.generate(prompt)
        tasks = self._parse_tasks(response)

        # Validate decomposition
        if not self._is_valid_decomposition(tasks, goal):
            # Retry with refinement
            tasks = self._refine_decomposition(tasks, goal)

        return tasks

    def _is_valid_decomposition(
        self,
        tasks: List[Task],
        original_goal: str
    ) -> bool:
        """Check if tasks cover the goal"""

        # Check completeness
        if len(tasks) == 0:
            return False

        # Check for circular dependencies
        if self._has_circular_deps(tasks):
            return False

        # Verify tasks align with goal
        coverage_score = self._calculate_coverage(tasks, original_goal)
        return coverage_score > 0.8

    def _has_circular_deps(self, tasks: List[Task]) -> bool:
        """Detect circular dependencies"""
        task_map = {t.id: t for t in tasks}

        def has_cycle(task_id: str, visited: Set[str]) -> bool:
            if task_id in visited:
                return True

            visited.add(task_id)
            task = task_map[task_id]

            for dep_id in task.dependencies:
                if has_cycle(dep_id, visited.copy()):
                    return True

            return False

        for task in tasks:
            if has_cycle(task.id, set()):
                return True

        return False
```

### Dependency Analysis

```python
class DependencyAnalyzer:
    """Analyze task dependencies"""

    def build_dag(self, tasks: List[Task]) -> nx.DiGraph:
        """Build directed acyclic graph"""
        dag = nx.DiGraph()

        for task in tasks:
            dag.add_node(task.id, task=task)
            for dep_id in task.dependencies:
                dag.add_edge(dep_id, task.id)

        return dag

    def get_execution_levels(self, tasks: List[Task]) -> List[List[Task]]:
        """Group tasks by execution level (for parallelization)"""
        dag = self.build_dag(tasks)

        # Topological sort to get levels
        levels = []
        remaining = set(dag.nodes())

        while remaining:
            # Find tasks with no unfulfilled dependencies
            current_level = [
                task_id for task_id in remaining
                if all(
                    dep not in remaining
                    for dep in dag.predecessors(task_id)
                )
            ]

            if not current_level:
                raise ValueError("Circular dependency detected")

            levels.append([
                dag.nodes[task_id]['task']
                for task_id in current_level
            ])
            remaining -= set(current_level)

        return levels

    def get_critical_path(self, tasks: List[Task]) -> List[Task]:
        """Find longest path (critical path)"""
        dag = self.build_dag(tasks)

        # Add duration weights
        for node in dag.nodes():
            task = dag.nodes[node]['task']
            dag.nodes[node]['duration'] = task.estimated_duration

        # Find longest path
        longest_path = nx.dag_longest_path(
            dag,
            weight='duration'
        )

        return [dag.nodes[task_id]['task'] for task_id in longest_path]
```

---

## Phase 2: Planning

### Execution Plan Generation

```python
@dataclass
class ExecutionPlan:
    """Complete execution plan"""
    id: str
    goal: str
    tasks: List[Task]
    execution_order: List[List[Task]]  # Levels for parallel execution
    critical_path: List[Task]
    estimated_total_time: int
    resource_allocation: Dict[str, str]  # task_id -> expert_id
    created_at: datetime
    metadata: Dict[str, Any] = None

class ExecutionPlanner:
    """Generate optimal execution plans"""

    def __init__(self, experts: Dict[str, Expert]):
        self.experts = experts
        self.dependency_analyzer = DependencyAnalyzer()

    def create_plan(
        self,
        goal: str,
        tasks: List[Task],
        optimization: str = "time"  # or "cost", "quality"
    ) -> ExecutionPlan:
        """Create execution plan from tasks"""

        # Analyze dependencies
        execution_order = self.dependency_analyzer.get_execution_levels(tasks)
        critical_path = self.dependency_analyzer.get_critical_path(tasks)

        # Allocate resources
        resource_allocation = self._allocate_resources(tasks)

        # Calculate total time
        estimated_time = self._estimate_time(execution_order, resource_allocation)

        # Optimize if needed
        if optimization == "time":
            execution_order, resource_allocation = self._optimize_for_time(
                execution_order,
                resource_allocation
            )

        return ExecutionPlan(
            id=f"plan-{uuid.uuid4().hex[:8]}",
            goal=goal,
            tasks=tasks,
            execution_order=execution_order,
            critical_path=critical_path,
            estimated_total_time=estimated_time,
            resource_allocation=resource_allocation,
            created_at=datetime.now()
        )

    def _allocate_resources(
        self,
        tasks: List[Task]
    ) -> Dict[str, str]:
        """Assign experts to tasks"""
        allocation = {}

        for task in tasks:
            # Find best-matching expert
            best_expert = self._find_best_expert(task.required_capabilities)
            allocation[task.id] = best_expert.id

        return allocation

    def _find_best_expert(
        self,
        required_capabilities: List[str]
    ) -> Expert:
        """Match task to expert based on capabilities"""
        best_match = None
        best_score = 0

        for expert in self.experts.values():
            score = len(
                set(required_capabilities) & set(expert.capabilities)
            ) / len(required_capabilities)

            if score > best_score:
                best_score = score
                best_match = expert

        return best_match or self.experts['general']

    def _estimate_time(
        self,
        execution_order: List[List[Task]],
        resource_allocation: Dict[str, str]
    ) -> int:
        """Estimate total execution time"""
        total_time = 0

        for level in execution_order:
            # Time for this level = max time of parallel tasks
            level_time = max(task.estimated_duration for task in level)
            total_time += level_time

        return total_time
```

### Plan Optimization

```python
class PlanOptimizer:
    """Optimize execution plans"""

    def optimize_for_time(
        self,
        plan: ExecutionPlan
    ) -> ExecutionPlan:
        """Minimize execution time"""

        # Try to parallelize more tasks
        optimized_order = self._maximize_parallelism(
            plan.tasks,
            plan.execution_order
        )

        # Re-allocate resources to critical path
        optimized_allocation = self._prioritize_critical_path(
            plan.critical_path,
            plan.resource_allocation
        )

        return ExecutionPlan(
            **{**plan.__dict__,
               'execution_order': optimized_order,
               'resource_allocation': optimized_allocation}
        )

    def optimize_for_cost(
        self,
        plan: ExecutionPlan,
        cost_model: Dict[str, float]
    ) -> ExecutionPlan:
        """Minimize resource costs"""

        # Assign cheaper experts where possible
        optimized_allocation = {}

        for task_id, expert_id in plan.resource_allocation.items():
            # Find cheaper alternative if quality is not critical
            task = next(t for t in plan.tasks if t.id == task_id)
            if task.priority > 5:  # Low priority
                cheaper_expert = self._find_cheaper_expert(
                    task.required_capabilities,
                    cost_model
                )
                optimized_allocation[task_id] = cheaper_expert
            else:
                optimized_allocation[task_id] = expert_id

        return ExecutionPlan(
            **{**plan.__dict__,
               'resource_allocation': optimized_allocation}
        )
```

---

## Phase 3: Parallel Execution

### Parallel Task Executor

```python
class ParallelExecutor:
    """Execute tasks in parallel"""

    def __init__(self, experts: Dict[str, Expert]):
        self.experts = experts

    async def execute_plan(
        self,
        plan: ExecutionPlan
    ) -> ExecutionTrace:
        """Execute plan level by level"""

        trace = ExecutionTrace(plan_id=plan.id, steps=[])

        for level_idx, level in enumerate(plan.execution_order):
            level_start = time.time()

            # Execute all tasks in this level in parallel
            tasks = [
                self._execute_task(task, plan.resource_allocation[task.id])
                for task in level
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            level_duration = time.time() - level_start

            # Record results
            for task, result in zip(level, results):
                step = ExecutionStep(
                    task_id=task.id,
                    level=level_idx,
                    result=result if not isinstance(result, Exception) else None,
                    error=str(result) if isinstance(result, Exception) else None,
                    duration=level_duration / len(level),  # Approximate
                    success=not isinstance(result, Exception)
                )
                trace.steps.append(step)

            # Check if level succeeded
            if any(isinstance(r, Exception) for r in results):
                # Handle partial failure
                trace.status = "partial_failure"
                break

        trace.total_duration = sum(s.duration for s in trace.steps)
        trace.completed_at = datetime.now()

        return trace

    async def _execute_task(
        self,
        task: Task,
        expert_id: str
    ) -> Any:
        """Execute single task"""
        expert = self.experts[expert_id]

        try:
            result = await expert.execute(task)
            return result
        except Exception as e:
            # Log and re-raise
            logger.error(f"Task {task.id} failed: {e}")
            raise
```

---

## Phase 4: Result Merging

### Result Merger

```python
@dataclass
class MergedResult:
    """Combined execution results"""
    goal: str
    success: bool
    output: Any
    intermediate_results: Dict[str, Any]  # task_id -> result
    conflicts: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]

class ResultMerger:
    """Merge results from parallel execution"""

    def merge(
        self,
        trace: ExecutionTrace,
        strategy: str = "sequential"
    ) -> MergedResult:
        """Combine task results"""

        if strategy == "sequential":
            return self._merge_sequential(trace)
        elif strategy == "voting":
            return self._merge_by_voting(trace)
        elif strategy == "weighted":
            return self._merge_weighted(trace)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _merge_sequential(self, trace: ExecutionTrace) -> MergedResult:
        """Merge results in execution order"""
        intermediate_results = {}
        conflicts = []

        for step in trace.steps:
            if step.success:
                intermediate_results[step.task_id] = step.result
            else:
                conflicts.append({
                    'task_id': step.task_id,
                    'error': step.error
                })

        # Determine overall success
        success = len(conflicts) == 0

        # Combine outputs
        final_output = self._combine_outputs(intermediate_results)

        return MergedResult(
            goal=trace.plan.goal,
            success=success,
            output=final_output,
            intermediate_results=intermediate_results,
            conflicts=conflicts,
            confidence=1.0 - (len(conflicts) / len(trace.steps))
        )

    def _merge_by_voting(self, trace: ExecutionTrace) -> MergedResult:
        """Use voting for consensus"""
        results = [s.result for s in trace.steps if s.success]

        if not results:
            return MergedResult(
                goal=trace.plan.goal,
                success=False,
                output=None,
                intermediate_results={},
                conflicts=[],
                confidence=0.0
            )

        # Count votes
        votes = Counter(str(r) for r in results)
        consensus = votes.most_common(1)[0][0]

        confidence = votes[consensus] / len(results)

        return MergedResult(
            goal=trace.plan.goal,
            success=True,
            output=consensus,
            intermediate_results={s.task_id: s.result for s in trace.steps},
            conflicts=[],
            confidence=confidence
        )
```

---

## Phase 5: Reflection

### Reflection Engine

```python
class ReflectionEngine:
    """Analyze execution and learn from outcomes"""

    def reflect(
        self,
        trace: ExecutionTrace,
        merged_result: MergedResult
    ) -> ReflectionOutput:
        """Analyze execution"""

        # Detect issues
        issues = self._detect_issues(trace)

        # Analyze performance
        performance = self._analyze_performance(trace)

        # Generate insights
        insights = self._generate_insights(trace, merged_result, issues)

        # Suggest improvements
        improvements = self._suggest_improvements(trace, issues)

        return ReflectionOutput(
            issues=issues,
            performance=performance,
            insights=insights,
            improvements=improvements
        )

    def _detect_issues(self, trace: ExecutionTrace) -> List[Issue]:
        """Find problems in execution"""
        issues = []

        for step in trace.steps:
            if not step.success:
                issues.append(Issue(
                    type="execution_failure",
                    task_id=step.task_id,
                    description=step.error,
                    severity="high"
                ))

            elif step.duration > step.task.estimated_duration * 2:
                issues.append(Issue(
                    type="performance_degradation",
                    task_id=step.task_id,
                    description=f"Took {step.duration}s, expected {step.task.estimated_duration}s",
                    severity="medium"
                ))

        return issues

    def _analyze_performance(self, trace: ExecutionTrace) -> PerformanceAnalysis:
        """Analyze execution metrics"""
        return PerformanceAnalysis(
            total_time=trace.total_duration,
            estimated_time=trace.plan.estimated_total_time,
            efficiency=trace.plan.estimated_total_time / trace.total_duration,
            parallelism_factor=len(trace.plan.tasks) / len(trace.plan.execution_order),
            success_rate=sum(1 for s in trace.steps if s.success) / len(trace.steps)
        )

    def _suggest_improvements(
        self,
        trace: ExecutionTrace,
        issues: List[Issue]
    ) -> List[Improvement]:
        """Generate improvement suggestions"""
        improvements = []

        # Suggest task re-ordering
        if any(i.type == "performance_degradation" for i in issues):
            improvements.append(Improvement(
                type="reorder_tasks",
                description="Move slow tasks earlier to maximize parallelism"
            ))

        # Suggest expert re-allocation
        failed_tasks = [i.task_id for i in issues if i.type == "execution_failure"]
        if failed_tasks:
            improvements.append(Improvement(
                type="reassign_expert",
                description=f"Try different expert for tasks: {failed_tasks}"
            ))

        return improvements
```

### Learning from Failures

```python
class FailureAnalyzer:
    """Learn from execution failures"""

    def __init__(self, memory_expert: MemoryExpert):
        self.memory = memory_expert

    def analyze_failure(
        self,
        trace: ExecutionTrace,
        reflection: ReflectionOutput
    ) -> FailureReport:
        """Deep analysis of failure"""

        # Categorize failure
        category = self._categorize_failure(trace, reflection)

        # Find similar past failures
        similar_failures = self.memory.recall(
            query=f"failure in {trace.plan.goal}",
            filters={"type": "failure_report"}
        )

        # Identify patterns
        patterns = self._find_patterns(trace, similar_failures)

        # Generate repair strategy
        repair = self._generate_repair_strategy(trace, reflection, patterns)

        # Store for future reference
        report = FailureReport(
            trace_id=trace.id,
            category=category,
            patterns=patterns,
            repair_strategy=repair,
            created_at=datetime.now()
        )

        self.memory.store_memory(
            content=str(report),
            tags=["failure", category, trace.plan.goal],
            context={"type": "failure_report"}
        )

        return report

    def _generate_repair_strategy(
        self,
        trace: ExecutionTrace,
        reflection: ReflectionOutput,
        patterns: List[Pattern]
    ) -> RepairStrategy:
        """Create plan to fix failure"""

        repairs = []

        for issue in reflection.issues:
            if issue.type == "execution_failure":
                # Retry with different approach
                repairs.append(RepairAction(
                    type="retry",
                    target=issue.task_id,
                    modification="Use different expert"
                ))

            elif issue.type == "dependency_violation":
                # Re-order tasks
                repairs.append(RepairAction(
                    type="reorder",
                    target=issue.task_id,
                    modification="Move after dependencies"
                ))

        return RepairStrategy(actions=repairs)
```

---

## Integration Example

```python
async def run_dppm_cycle(goal: str, context: Dict[str, Any]):
    """Complete DPPM cycle"""

    # 1. DECOMPOSE
    decomposer = TaskDecomposer()
    tasks = decomposer.decompose(goal, context)

    # 2. PLAN
    planner = ExecutionPlanner(experts={...})
    plan = planner.create_plan(goal, tasks, optimization="time")

    # 3. EXECUTE (in parallel)
    executor = ParallelExecutor(experts={...})
    trace = await executor.execute_plan(plan)

    # 4. MERGE
    merger = ResultMerger()
    result = merger.merge(trace, strategy="sequential")

    # 5. REFLECT
    reflector = ReflectionEngine()
    reflection = reflector.reflect(trace, result)

    # If failed, analyze and potentially retry
    if not result.success:
        analyzer = FailureAnalyzer(memory_expert={...})
        failure_report = analyzer.analyze_failure(trace, reflection)

        # Repair and retry
        if failure_report.repair_strategy.is_viable:
            repaired_plan = apply_repairs(plan, failure_report.repair_strategy)
            return await run_dppm_cycle(goal, context)  # Recursive retry

    return result
```

---

## Implementation Plan

### Phase 1: Decomposition (Weeks 1-2)
- [ ] Task decomposition logic
- [ ] Dependency analyzer
- [ ] Validation rules

### Phase 2: Planning (Weeks 3-4)
- [ ] Plan generation
- [ ] Resource allocation
- [ ] Plan optimization

### Phase 3: Execution (Weeks 5-6)
- [ ] Parallel executor
- [ ] Progress tracking
- [ ] Error handling

### Phase 4: Merging (Week 7)
- [ ] Result merger
- [ ] Conflict resolution
- [ ] Output combination

### Phase 5: Reflection (Weeks 8-10)
- [ ] Reflection engine
- [ ] Failure analyzer
- [ ] Learning system

---

## References

### Research Papers
1. **ReAct** - Reasoning and Acting framework
2. **Reflexion** - Self-reflection for improvement
3. **Tree of Thoughts** - Deliberative decision making
4. **Plan-and-Solve** - Decomposition strategies
5. **Self-Refine** - Iterative refinement

### Related SPECs
- **SPEC-135:** Multi-Agent Expert Protocol (Planning/Reflection experts)
- **SPEC-136:** Execution System Backends (task execution)
- **SPEC-040:** Feedback Loop System (reflection patterns)

---

**End of SPEC-137**
