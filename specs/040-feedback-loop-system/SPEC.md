# SPEC-040: Feedback Loop System (Enhanced)

**Status:** Enhanced
**Created:** 2024 (Original)
**Updated:** 2025-10-29
**Owner:** AI Engineering Team
**Stakeholders:** Memory System, Agent Development

---

## Executive Summary

Comprehensive feedback loop system for continuous improvement of memory accuracy and agent performance. This enhanced SPEC adds advanced reflection capabilities including Reflexion loops, anticipatory reflection patterns, and verbal reinforcement learning on top of the existing feedback mechanisms.

---

## Original Features (Maintained)

### Implicit Feedback
- Query dwell time tracking
- Memory token click-through analysis
- Navigation patterns and memory re-visitation

### Explicit Feedback
- Thumbs-up/thumbs-down scoring on memory recalls
- Inline feedback form for memory quality notes

### Memory Token Score Adjustment
- Relevance boosting/demotion based on usage signals
- Decay model for stale feedback influence

---

## New Enhancements

### 1. Reflexion Loop Design

**Concept:** Self-reflection mechanism for agents to learn from their mistakes

```python
@dataclass
class ReflexionCycle:
    """One complete reflexion iteration"""
    task: Task
    attempt: int
    trajectory: ExecutionTrace  # What the agent did
    evaluation: EvaluationResult  # Was it successful?
    reflection: str  # What went wrong? How to improve?
    memory_update: MemoryUpdate  # What to remember

class ReflexionEngine:
    """Implement Reflexion pattern"""

    def __init__(self, memory_expert: MemoryExpert):
        self.memory = memory_expert
        self.max_attempts = 3

    async def execute_with_reflexion(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute task with self-reflection"""

        # Recall past attempts on similar tasks
        past_reflections = self.memory.recall(
            query=f"reflection on {task.type}",
            filters={"type": "reflexion"}
        )

        for attempt in range(self.max_attempts):
            # Generate plan with past reflections as context
            plan = self._generate_plan(
                task,
                context,
                past_reflections=past_reflections
            )

            # Execute
            trace = await self._execute_plan(plan)

            # Evaluate outcome
            evaluation = self._evaluate(trace, task.success_criteria)

            if evaluation.success:
                # Store successful strategy
                self.memory.store_memory(
                    content=f"Successful approach: {trace.summary()}",
                    tags=["success", task.type],
                    context={"type": "reflexion", "success": True}
                )
                return TaskResult(success=True, output=trace.output)

            # Generate reflection on failure
            reflection = await self._reflect_on_failure(
                task,
                trace,
                evaluation,
                attempt
            )

            # Store reflection for next iteration
            past_reflections.append(reflection)
            self.memory.store_memory(
                content=reflection.text,
                tags=["reflection", "failure", task.type],
                context={
                    "type": "reflexion",
                    "attempt": attempt,
                    "error": evaluation.error
                }
            )

            # If last attempt, escalate
            if attempt == self.max_attempts - 1:
                return TaskResult(
                    success=False,
                    error="Max attempts reached",
                    reflections=past_reflections
                )

        return TaskResult(success=False, error="Reflexion loop failed")

    async def _reflect_on_failure(
        self,
        task: Task,
        trace: ExecutionTrace,
        evaluation: EvaluationResult,
        attempt: int
    ) -> Reflection:
        """Generate reflection on why task failed"""

        prompt = f"""
        Task: {task.description}
        Attempt: {attempt + 1}

        What I tried:
        {trace.summary()}

        What went wrong:
        {evaluation.error}

        Reflect on:
        1. Why did this approach fail?
        2. What assumptions were incorrect?
        3. What should I try differently next time?
        4. What can I learn from this failure?

        Provide a concise reflection that will help in future attempts.
        """

        reflection_text = await self.llm.generate(prompt)

        return Reflection(
            text=reflection_text,
            task_type=task.type,
            error_type=evaluation.error_type,
            attempt=attempt,
            timestamp=datetime.now()
        )
```

**Reflexion Workflow:**
```
┌─────────────────────────────────────────────┐
│         Reflexion Loop                      │
│                                              │
│  1. Recall past reflections                 │
│  2. Generate plan (informed by reflections) │
│  3. Execute plan                            │
│  4. Evaluate outcome                        │
│  5. If failed:                              │
│     a. Reflect on failure                   │
│     b. Store reflection                     │
│     c. Retry (max 3 attempts)               │
│  6. If succeeded:                           │
│     a. Store successful strategy            │
│     b. Return result                        │
└─────────────────────────────────────────────┘
```

---

### 2. Anticipatory Reflection Patterns

**Concept:** Predict potential issues before they occur

```python
class AnticipatorReflector:
    """Anticipate problems before execution"""

    async def anticipate_issues(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any]
    ) -> List[PotentialIssue]:
        """Identify potential problems in plan"""

        issues = []

        # Check for known failure patterns
        issues.extend(await self._check_failure_patterns(plan))

        # Devil's Advocate: Challenge assumptions
        issues.extend(await self._devils_advocate_analysis(plan))

        # Pre-mortem analysis
        issues.extend(await self._premortem_analysis(plan))

        # Check resource constraints
        issues.extend(await self._check_constraints(plan, context))

        return issues

    async def _devils_advocate_analysis(
        self,
        plan: ExecutionPlan
    ) -> List[PotentialIssue]:
        """Challenge plan assumptions"""

        prompt = f"""
        Plan: {plan.summary()}

        Play devil's advocate. What could go wrong?
        For each step, identify:
        1. Questionable assumptions
        2. Edge cases not handled
        3. Dependencies that might fail
        4. Resource bottlenecks

        Be specific and constructive.
        """

        critique = await self.llm.generate(prompt)
        issues = self._parse_critique(critique)

        return issues

    async def _premortem_analysis(
        self,
        plan: ExecutionPlan
    ) -> List[PotentialIssue]:
        """Imagine the plan has failed - why?"""

        prompt = f"""
        Plan: {plan.summary()}

        Imagine it's 1 week from now and this plan has completely failed.
        What went wrong? Write a "failure report" explaining:
        1. What failed first?
        2. What cascade of failures followed?
        3. What warning signs were missed?
        4. What should have been done differently?
        """

        failure_scenario = await self.llm.generate(prompt)
        issues = self._extract_issues_from_scenario(failure_scenario)

        return issues

    def apply_mitigations(
        self,
        plan: ExecutionPlan,
        issues: List[PotentialIssue]
    ) -> ExecutionPlan:
        """Modify plan to address anticipated issues"""

        mitigated_plan = plan.copy()

        for issue in issues:
            if issue.severity == "high":
                # Add mitigation steps
                mitigation = self._generate_mitigation(issue)
                mitigated_plan.tasks.insert(
                    issue.step_index,
                    mitigation
                )
            elif issue.severity == "medium":
                # Add validation checks
                mitigated_plan.add_checkpoint(issue.step_index)

        return mitigated_plan
```

**Devil's Advocate Pattern:**
```python
class DevilsAdvocate:
    """Challenge plans constructively"""

    async def critique_plan(
        self,
        plan: ExecutionPlan,
        perspective: str = "pessimist"
    ) -> Critique:
        """Generate critical analysis"""

        perspectives = {
            "pessimist": "What's the worst that could happen?",
            "perfectionist": "What details are being overlooked?",
            "pragmatist": "Is this actually feasible?",
            "security": "What are the security risks?",
            "performance": "Will this scale?"
        }

        prompt = f"""
        Plan: {plan.summary()}

        Perspective: {perspectives[perspective]}

        Provide constructive criticism of this plan.
        Identify specific weaknesses and suggest improvements.
        """

        critique_text = await self.llm.generate(prompt)

        return Critique(
            perspective=perspective,
            text=critique_text,
            issues=self._extract_issues(critique_text)
        )
```

---

### 3. Verbal Reinforcement Learning

**Concept:** Learn from human feedback expressed in natural language

```python
class VerbalRL:
    """Learn from verbal feedback"""

    def __init__(self, memory_expert: MemoryExpert):
        self.memory = memory_expert
        self.feedback_history = []

    async def process_verbal_feedback(
        self,
        task: Task,
        execution: ExecutionTrace,
        feedback: str,  # Natural language feedback
        rating: float  # 0.0 to 1.0
    ) -> LearningUpdate:
        """Learn from user's verbal feedback"""

        # Parse feedback
        feedback_analysis = await self._analyze_feedback(feedback)

        # Extract lessons
        lessons = self._extract_lessons(
            task,
            execution,
            feedback_analysis,
            rating
        )

        # Update agent's knowledge
        for lesson in lessons:
            self.memory.store_memory(
                content=lesson.text,
                tags=["lesson", "verbal_feedback", task.type],
                context={
                    "type": "verbal_rl",
                    "rating": rating,
                    "feedback_type": feedback_analysis.type
                }
            )

        # Adjust future behavior
        policy_update = self._generate_policy_update(lessons)

        return LearningUpdate(
            lessons=lessons,
            policy_update=policy_update,
            confidence=feedback_analysis.clarity
        )

    async def _analyze_feedback(self, feedback: str) -> FeedbackAnalysis:
        """Parse and categorize verbal feedback"""

        prompt = f"""
        User Feedback: "{feedback}"

        Analyze this feedback:
        1. What did the user like/dislike?
        2. What specific actions were praised/criticized?
        3. What improvements are suggested?
        4. Overall sentiment (positive/negative/mixed)
        5. Clarity of feedback (clear/vague)

        Provide structured analysis.
        """

        analysis_text = await self.llm.generate(prompt)

        return FeedbackAnalysis(
            sentiment=self._extract_sentiment(analysis_text),
            liked_aspects=self._extract_aspects(analysis_text, "positive"),
            disliked_aspects=self._extract_aspects(analysis_text, "negative"),
            suggestions=self._extract_suggestions(analysis_text),
            clarity=self._assess_clarity(analysis_text),
            type=self._categorize_feedback(analysis_text)
        )

    def _extract_lessons(
        self,
        task: Task,
        execution: ExecutionTrace,
        feedback: FeedbackAnalysis,
        rating: float
    ) -> List[Lesson]:
        """Convert feedback into actionable lessons"""

        lessons = []

        # Positive lessons (what to keep doing)
        if rating > 0.7:
            for aspect in feedback.liked_aspects:
                lessons.append(Lesson(
                    text=f"When doing {task.type}, {aspect} works well",
                    type="positive_reinforcement",
                    confidence=rating
                ))

        # Negative lessons (what to avoid)
        if rating < 0.4:
            for aspect in feedback.disliked_aspects:
                lessons.append(Lesson(
                    text=f"When doing {task.type}, avoid {aspect}",
                    type="negative_feedback",
                    confidence=1.0 - rating
                ))

        # Improvement lessons
        for suggestion in feedback.suggestions:
            lessons.append(Lesson(
                text=f"For {task.type}, try: {suggestion}",
                type="improvement",
                confidence=feedback.clarity
            ))

        return lessons
```

**Learning Pipeline:**
```
User Feedback (Natural Language)
        ↓
Feedback Analysis (Sentiment, Aspects, Suggestions)
        ↓
Lesson Extraction (Actionable insights)
        ↓
Memory Storage (Tagged for retrieval)
        ↓
Policy Update (Adjust future behavior)
        ↓
Improved Performance
```

---

### 4. Error Analysis Memory

**Concept:** Systematic storage and retrieval of error patterns

```python
@dataclass
class ErrorPattern:
    """Recurring error pattern"""
    error_type: str
    context: Dict[str, Any]
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    solutions: List[str]  # What fixed it before
    confidence: float  # How reliable are the solutions

class ErrorAnalysisMemory:
    """Store and learn from errors"""

    def __init__(self, memory_expert: MemoryExpert):
        self.memory = memory_expert
        self.error_index: Dict[str, ErrorPattern] = {}

    def record_error(
        self,
        error: Exception,
        context: ExecutionContext,
        solution: Optional[str] = None
    ):
        """Record error occurrence"""

        error_key = self._generate_error_key(error, context)

        if error_key in self.error_index:
            # Update existing pattern
            pattern = self.error_index[error_key]
            pattern.occurrences += 1
            pattern.last_seen = datetime.now()

            if solution:
                pattern.solutions.append(solution)
                pattern.confidence = min(
                    1.0,
                    pattern.confidence + 0.1
                )
        else:
            # Create new pattern
            pattern = ErrorPattern(
                error_type=type(error).__name__,
                context=self._extract_context(context),
                occurrences=1,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                solutions=[solution] if solution else [],
                confidence=0.5 if solution else 0.1
            )
            self.error_index[error_key] = pattern

        # Store in persistent memory
        self.memory.store_memory(
            content=str(pattern),
            tags=["error_pattern", pattern.error_type],
            context={"type": "error_analysis"}
        )

    def suggest_solution(
        self,
        error: Exception,
        context: ExecutionContext
    ) -> Optional[str]:
        """Suggest solution based on past errors"""

        error_key = self._generate_error_key(error, context)

        if error_key in self.error_index:
            pattern = self.error_index[error_key]

            if pattern.solutions and pattern.confidence > 0.6:
                # Return most recent solution
                return pattern.solutions[-1]

        # Search for similar errors
        similar_errors = self.memory.recall(
            query=f"{type(error).__name__} {str(error)[:100]}",
            filters={"type": "error_analysis"},
            limit=5
        )

        if similar_errors:
            # Extract solutions from similar cases
            solutions = self._extract_solutions(similar_errors)
            if solutions:
                return solutions[0]

        return None

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error analytics"""

        total_errors = sum(p.occurrences for p in self.error_index.values())

        top_errors = sorted(
            self.error_index.values(),
            key=lambda p: p.occurrences,
            reverse=True
        )[:10]

        solved_errors = [
            p for p in self.error_index.values()
            if p.solutions and p.confidence > 0.7
        ]

        return {
            "total_unique_errors": len(self.error_index),
            "total_occurrences": total_errors,
            "top_errors": [
                {"type": p.error_type, "count": p.occurrences}
                for p in top_errors
            ],
            "solved_count": len(solved_errors),
            "solve_rate": len(solved_errors) / len(self.error_index) if self.error_index else 0
        }
```

---

## Integration with Existing Feedback System

### Combined Feedback Architecture

```python
class EnhancedFeedbackSystem:
    """Unified feedback and reflection system"""

    def __init__(
        self,
        memory_expert: MemoryExpert,
        redis_client: Redis
    ):
        # Original components
        self.implicit_tracker = ImplicitFeedbackTracker()
        self.explicit_collector = ExplicitFeedbackCollector()
        self.token_adjuster = TokenScoreAdjuster()

        # New components
        self.reflexion = ReflexionEngine(memory_expert)
        self.anticipator = AnticipatorReflector()
        self.verbal_rl = VerbalRL(memory_expert)
        self.error_memory = ErrorAnalysisMemory(memory_expert)

        self.redis = redis_client

    async def process_task_with_full_feedback(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute task with all feedback mechanisms"""

        # 1. Anticipate issues
        plan = self._generate_plan(task)
        issues = await self.anticipator.anticipate_issues(plan, context)
        mitigated_plan = self.anticipator.apply_mitigations(plan, issues)

        # 2. Execute with reflexion
        result = await self.reflexion.execute_with_reflexion(
            task,
            context
        )

        # 3. Track implicit feedback
        self.implicit_tracker.track_execution(
            task_id=task.id,
            duration=result.execution_time,
            user_interactions=result.user_interactions
        )

        # 4. If failed, record error
        if not result.success:
            self.error_memory.record_error(
                error=result.error,
                context=context,
                solution=result.attempted_solution
            )

        # 5. Queue for explicit feedback collection
        await self.redis.lpush(
            "feedback_queue",
            json.dumps({
                "task_id": task.id,
                "result": result.summary(),
                "timestamp": datetime.now().isoformat()
            })
        )

        return result

    async def learn_from_feedback(
        self,
        task_id: str,
        feedback: str,
        rating: float
    ):
        """Process user feedback"""

        # Get task and execution details
        task = self._get_task(task_id)
        execution = self._get_execution_trace(task_id)

        # Apply verbal RL
        learning_update = await self.verbal_rl.process_verbal_feedback(
            task,
            execution,
            feedback,
            rating
        )

        # Adjust token scores (original feature)
        self.token_adjuster.adjust_based_on_feedback(
            task_id=task_id,
            rating=rating
        )

        # Log for analytics
        await self.redis.lpush(
            "learning_updates",
            json.dumps({
                "task_id": task_id,
                "lessons": [l.text for l in learning_update.lessons],
                "timestamp": datetime.now().isoformat()
            })
        )
```

---

## Metrics & Observability (Enhanced)

### New Metrics

```python
class ReflectionMetrics:
    """Track reflection system performance"""

    def __init__(self, prometheus_client):
        self.prometheus = prometheus_client

        # Reflexion metrics
        self.reflexion_attempts = Counter(
            'reflexion_attempts_total',
            'Total reflexion attempts',
            ['task_type', 'outcome']
        )

        self.reflexion_success_rate = Gauge(
            'reflexion_success_rate',
            'Reflexion success rate by task type',
            ['task_type']
        )

        # Anticipation metrics
        self.issues_anticipated = Counter(
            'issues_anticipated_total',
            'Issues caught by anticipatory reflection',
            ['severity']
        )

        self.anticipation_accuracy = Gauge(
            'anticipation_accuracy',
            'How many anticipated issues actually occurred'
        )

        # Verbal RL metrics
        self.verbal_feedback_count = Counter(
            'verbal_feedback_total',
            'Verbal feedback received',
            ['sentiment']
        )

        self.lessons_learned = Counter(
            'lessons_learned_total',
            'Lessons extracted from feedback',
            ['lesson_type']
        )

        # Error memory metrics
        self.error_recurrence = Counter(
            'error_recurrence_total',
            'Recurring errors',
            ['error_type']
        )

        self.solution_success_rate = Gauge(
            'solution_success_rate',
            'Success rate of suggested solutions'
        )
```

---

## Implementation Plan

### Phase 1: Reflexion Loop (Weeks 1-2)
- [ ] Implement ReflexionEngine
- [ ] Add reflection storage
- [ ] Create evaluation framework

### Phase 2: Anticipatory Reflection (Weeks 3-4)
- [ ] Build AnticipatorReflector
- [ ] Implement Devil's Advocate
- [ ] Add pre-mortem analysis

### Phase 3: Verbal RL (Weeks 5-6)
- [ ] Create VerbalRL system
- [ ] Add feedback parsing
- [ ] Implement lesson extraction

### Phase 4: Error Memory (Weeks 7-8)
- [ ] Build ErrorAnalysisMemory
- [ ] Add pattern detection
- [ ] Create solution suggestions

### Phase 5: Integration (Weeks 9-10)
- [ ] Integrate all systems
- [ ] Add metrics/monitoring
- [ ] Create admin dashboard

---

## References

### Research Papers
1. **Reflexion** - Verbal Reinforcement Learning (Shinn et al., 2023)
2. **Self-Refine** - Iterative refinement with self-feedback
3. **Tree of Thoughts** - Deliberative reasoning
4. **Constitutional AI** - Self-critique and improvement

### Related SPECs
- **SPEC-137:** Agent Plan-Reflection Loop (DPPM integration)
- **SPEC-135:** Multi-Agent Expert Protocol (Reflection Expert)
- **SPEC-031:** Relevance Scoring Model (token adjustment)
- **SPEC-033:** Redis Queue (feedback processing)

---

**End of SPEC-040 (Enhanced)**
