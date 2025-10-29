# SPEC-079: Personalization Engine (Enhanced)

**Status:** Enhanced
**Created:** 2024 (Original)
**Updated:** 2025-10-29
**Owner:** AI Engineering Team
**Stakeholders:** User Experience, Memory System

---

## Executive Summary

Enhanced personalization engine with MemoryBank-style user memory, personality profiling, preference tracking, and user query history. This transforms Ninaivalaigal from a generic memory system into a deeply personalized AI companion that adapts to individual user patterns and preferences.

---

## Enhancement Overview

### New Capabilities

1. **Personality Profiling:** Understand user communication style and preferences
2. **Preference Tracking:** Learn and adapt to user choices over time
3. **User Query History:** Maintain comprehensive interaction patterns
4. **Adaptive Responses:** Tailor outputs to user preferences
5. **Progressive Learning:** Continuous improvement from user interactions

---

## MemoryBank-Style User Memory

### Architecture

```python
@dataclass
class UserProfile:
    """Comprehensive user profile"""
    user_id: str
    personality_traits: PersonalityProfile
    preferences: PreferenceSet
    interaction_history: InteractionHistory
    expertise_areas: List[str]
    communication_style: CommunicationStyle
    learning_patterns: LearningPatterns
    goals: List[UserGoal]
    created_at: datetime
    last_updated: datetime

class UserMemoryBank:
    """MemoryBank-style storage for user profiles"""

    def __init__(
        self,
        storage: MemoryBackend,
        analytics: AnalyticsEngine
    ):
        self.storage = storage
        self.analytics = analytics
        self.profiles: Dict[str, UserProfile] = {}

    async def get_or_create_profile(
        self,
        user_id: str
    ) -> UserProfile:
        """Retrieve or initialize user profile"""

        if user_id in self.profiles:
            return self.profiles[user_id]

        # Try loading from storage
        stored_profile = await self.storage.load_profile(user_id)

        if stored_profile:
            self.profiles[user_id] = stored_profile
            return stored_profile

        # Create new profile
        profile = UserProfile(
            user_id=user_id,
            personality_traits=PersonalityProfile(),
            preferences=PreferenceSet(),
            interaction_history=InteractionHistory(),
            expertise_areas=[],
            communication_style=CommunicationStyle(),
            learning_patterns=LearningPatterns(),
            goals=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

        self.profiles[user_id] = profile
        await self.storage.save_profile(profile)

        return profile

    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ):
        """Update user profile"""

        profile = await self.get_or_create_profile(user_id)

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.last_updated = datetime.now()

        await self.storage.save_profile(profile)
```

---

## Personality Profiling

### Big Five Personality Traits

```python
@dataclass
class PersonalityProfile:
    """Big Five personality model"""
    openness: float  # 0.0 - 1.0
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

    # Derived traits
    communication_preference: str  # formal, casual, technical
    detail_level: str  # high, medium, low
    pace: str  # fast, moderate, slow
    feedback_style: str  # direct, gentle, neutral

    confidence: float = 0.5  # How confident is this assessment?
    sample_size: int = 0  # Number of interactions analyzed

class PersonalityAnalyzer:
    """Infer personality from interactions"""

    def __init__(self, llm: LLM):
        self.llm = llm

    async def analyze_personality(
        self,
        interactions: List[Interaction],
        current_profile: PersonalityProfile
    ) -> PersonalityProfile:
        """Update personality assessment"""

        if len(interactions) < 10:
            # Not enough data
            return current_profile

        # Analyze communication patterns
        patterns = self._extract_patterns(interactions)

        # Use LLM for nuanced analysis
        prompt = f"""
        Analyze these user interactions to assess personality traits:

        {self._format_interactions(interactions[-20:])}

        Based on the Big Five model, estimate:
        1. Openness (0-1): Curiosity, creativity, open to new ideas
        2. Conscientiousness (0-1): Organization, attention to detail
        3. Extraversion (0-1): Sociability, enthusiasm
        4. Agreeableness (0-1): Compassion, cooperation
        5. Neuroticism (0-1): Emotional stability

        Also infer:
        - Communication preference (formal/casual/technical)
        - Preferred detail level (high/medium/low)
        - Interaction pace (fast/moderate/slow)
        - Feedback style preference (direct/gentle/neutral)

        Provide scores as JSON.
        """

        analysis = await self.llm.generate(prompt)
        new_traits = self._parse_personality(analysis)

        # Blend with existing profile (weighted average)
        blended = self._blend_profiles(
            current_profile,
            new_traits,
            weight=0.3  # 30% new data, 70% existing
        )

        blended.sample_size += len(interactions)
        blended.confidence = min(1.0, blended.sample_size / 100)

        return blended

    def _extract_patterns(
        self,
        interactions: List[Interaction]
    ) -> Dict[str, Any]:
        """Extract behavioral patterns"""

        return {
            "avg_query_length": np.mean([len(i.query) for i in interactions]),
            "question_ratio": sum(1 for i in interactions if "?" in i.query) / len(interactions),
            "formality_score": self._calculate_formality(interactions),
            "technical_density": self._calculate_technical_density(interactions),
            "response_wait_time": np.mean([i.response_time for i in interactions]),
            "follow_up_rate": self._calculate_follow_up_rate(interactions)
        }
```

### Communication Style Adaptation

```python
@dataclass
class CommunicationStyle:
    """How user prefers to communicate"""
    formality: str  # formal, casual, mixed
    verbosity: str  # concise, moderate, detailed
    technical_level: str  # beginner, intermediate, advanced
    emoji_usage: bool
    code_examples_preferred: bool
    explanation_style: str  # step-by-step, conceptual, practical

class ResponseAdapter:
    """Adapt responses to user's style"""

    def adapt_response(
        self,
        base_response: str,
        style: CommunicationStyle
    ) -> str:
        """Tailor response to communication style"""

        adapted = base_response

        # Adjust formality
        if style.formality == "casual":
            adapted = self._casualize(adapted)
        elif style.formality == "formal":
            adapted = self._formalize(adapted)

        # Adjust verbosity
        if style.verbosity == "concise":
            adapted = self._condense(adapted)
        elif style.verbosity == "detailed":
            adapted = self._expand(adapted)

        # Add code examples if preferred
        if style.code_examples_preferred:
            adapted = self._add_code_examples(adapted)

        # Handle emoji preference
        if not style.emoji_usage:
            adapted = self._remove_emojis(adapted)

        return adapted
```

---

## Preference Tracking

### Preference System

```python
@dataclass
class Preference:
    """Single user preference"""
    category: str  # ui, content, behavior, etc.
    key: str
    value: Any
    confidence: float
    learned_from: str  # explicit, implicit
    first_observed: datetime
    last_confirmed: datetime
    frequency: int  # How often this preference is observed

class PreferenceSet:
    """Collection of user preferences"""

    def __init__(self):
        self.preferences: Dict[str, Preference] = {}

    def add_preference(
        self,
        category: str,
        key: str,
        value: Any,
        source: str = "implicit"
    ):
        """Record or update preference"""

        pref_id = f"{category}:{key}"

        if pref_id in self.preferences:
            # Update existing
            pref = self.preferences[pref_id]
            if pref.value == value:
                pref.frequency += 1
                pref.confidence = min(1.0, pref.confidence + 0.05)
                pref.last_confirmed = datetime.now()
            else:
                # Conflicting preference - start fresh
                pref.value = value
                pref.frequency = 1
                pref.confidence = 0.3
        else:
            # New preference
            self.preferences[pref_id] = Preference(
                category=category,
                key=key,
                value=value,
                confidence=0.5 if source == "explicit" else 0.3,
                learned_from=source,
                first_observed=datetime.now(),
                last_confirmed=datetime.now(),
                frequency=1
            )

    def get_preference(
        self,
        category: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Retrieve preference value"""

        pref_id = f"{category}:{key}"
        pref = self.preferences.get(pref_id)

        if pref and pref.confidence > 0.6:
            return pref.value

        return default

    def get_top_preferences(
        self,
        category: str = None,
        min_confidence: float = 0.7
    ) -> List[Preference]:
        """Get high-confidence preferences"""

        prefs = [
            p for p in self.preferences.values()
            if p.confidence >= min_confidence
        ]

        if category:
            prefs = [p for p in prefs if p.category == category]

        return sorted(prefs, key=lambda p: p.confidence, reverse=True)

class PreferenceTracker:
    """Learn preferences from user behavior"""

    def __init__(self):
        self.trackers = {
            "ui": UIPreferenceTracker(),
            "content": ContentPreferenceTracker(),
            "workflow": WorkflowPreferenceTracker()
        }

    async def track_interaction(
        self,
        user_id: str,
        interaction: Interaction,
        profile: UserProfile
    ):
        """Extract preferences from interaction"""

        for tracker in self.trackers.values():
            preferences = await tracker.extract_preferences(interaction)

            for pref in preferences:
                profile.preferences.add_preference(
                    category=pref.category,
                    key=pref.key,
                    value=pref.value,
                    source="implicit"
                )

class UIPreferenceTracker:
    """Track UI preferences"""

    async def extract_preferences(
        self,
        interaction: Interaction
    ) -> List[Preference]:
        """Infer UI preferences"""

        prefs = []

        # View mode preference
        if hasattr(interaction, 'view_mode'):
            prefs.append(Preference(
                category="ui",
                key="preferred_view_mode",
                value=interaction.view_mode,
                confidence=0.4,
                learned_from="implicit",
                first_observed=datetime.now(),
                last_confirmed=datetime.now(),
                frequency=1
            ))

        # Theme preference
        if hasattr(interaction, 'theme'):
            prefs.append(Preference(
                category="ui",
                key="theme",
                value=interaction.theme,
                confidence=0.3,
                learned_from="implicit",
                first_observed=datetime.now(),
                last_confirmed=datetime.now(),
                frequency=1
            ))

        return prefs
```

---

## User Query History

### Query History System

```python
@dataclass
class QueryRecord:
    """Single query record"""
    query_id: str
    user_id: str
    query_text: str
    query_type: str  # search, question, command, etc.
    context: Dict[str, Any]
    response: str
    response_time: float
    user_satisfaction: Optional[float]  # 0-1
    follow_up_queries: List[str]
    timestamp: datetime
    metadata: Dict[str, Any]

class InteractionHistory:
    """Comprehensive interaction tracking"""

    def __init__(self):
        self.queries: List[QueryRecord] = []
        self.sessions: Dict[str, Session] = {}

    def add_query(self, record: QueryRecord):
        """Record new query"""
        self.queries.append(record)

    def get_recent_queries(
        self,
        limit: int = 10,
        query_type: str = None
    ) -> List[QueryRecord]:
        """Get recent queries"""

        queries = self.queries

        if query_type:
            queries = [q for q in queries if q.query_type == query_type]

        return sorted(
            queries,
            key=lambda q: q.timestamp,
            reverse=True
        )[:limit]

    def get_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns"""

        if not self.queries:
            return {}

        return {
            "total_queries": len(self.queries),
            "avg_queries_per_session": self._calc_queries_per_session(),
            "most_common_query_types": self._get_common_types(),
            "peak_hours": self._get_peak_hours(),
            "avg_satisfaction": self._calc_avg_satisfaction(),
            "topics": self._extract_topics()
        }

    def _extract_topics(self) -> List[str]:
        """Extract common topics from queries"""

        # Use simple keyword extraction
        # In production, use NLP topic modeling
        keywords = []
        for query in self.queries:
            words = query.query_text.lower().split()
            keywords.extend([w for w in words if len(w) > 4])

        # Get top keywords
        from collections import Counter
        top_keywords = Counter(keywords).most_common(10)

        return [word for word, count in top_keywords]

class QueryAnalyzer:
    """Analyze query patterns for insights"""

    def analyze_query_evolution(
        self,
        history: InteractionHistory
    ) -> QueryEvolution:
        """Track how user's queries evolve over time"""

        queries = history.queries

        # Group by time periods
        early = queries[:len(queries)//3]
        middle = queries[len(queries)//3:2*len(queries)//3]
        recent = queries[2*len(queries)//3:]

        return QueryEvolution(
            early_topics=self._extract_topics(early),
            middle_topics=self._extract_topics(middle),
            recent_topics=self._extract_topics(recent),
            complexity_trend=self._calculate_complexity_trend(queries),
            specialization=self._calculate_specialization(queries)
        )

    def identify_learning_goals(
        self,
        history: InteractionHistory
    ) -> List[LearningGoal]:
        """Infer what user is trying to learn"""

        topics = history._extract_topics()
        patterns = history.get_query_patterns()

        goals = []

        # Frequent topic = learning goal
        for topic in topics[:5]:
            related_queries = [
                q for q in history.queries
                if topic in q.query_text.lower()
            ]

            if len(related_queries) > 3:
                goals.append(LearningGoal(
                    topic=topic,
                    query_count=len(related_queries),
                    first_query=related_queries[0].timestamp,
                    last_query=related_queries[-1].timestamp,
                    proficiency_estimate=self._estimate_proficiency(related_queries)
                ))

        return goals
```

---

## Schema and Update Lifecycle

### User Profile Schema

```python
class UserProfileSchema:
    """Database schema for user profiles"""

    @staticmethod
    def to_dict(profile: UserProfile) -> Dict[str, Any]:
        """Serialize profile"""
        return {
            "user_id": profile.user_id,
            "personality": {
                "openness": profile.personality_traits.openness,
                "conscientiousness": profile.personality_traits.conscientiousness,
                "extraversion": profile.personality_traits.extraversion,
                "agreeableness": profile.personality_traits.agreeableness,
                "neuroticism": profile.personality_traits.neuroticism,
                "communication_preference": profile.personality_traits.communication_preference,
                "confidence": profile.personality_traits.confidence
            },
            "preferences": {
                k: {
                    "value": v.value,
                    "confidence": v.confidence,
                    "frequency": v.frequency
                }
                for k, v in profile.preferences.preferences.items()
            },
            "interaction_stats": {
                "total_queries": len(profile.interaction_history.queries),
                "query_patterns": profile.interaction_history.get_query_patterns()
            },
            "expertise_areas": profile.expertise_areas,
            "goals": [g.__dict__ for g in profile.goals],
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat()
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> UserProfile:
        """Deserialize profile"""
        # Implementation of reconstruction
        pass

class UpdateLifecycle:
    """Manage profile update lifecycle"""

    def __init__(self, storage: MemoryBackend):
        self.storage = storage
        self.update_queue = asyncio.Queue()

    async def schedule_update(
        self,
        user_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """Queue profile update"""
        await self.update_queue.put({
            "user_id": user_id,
            "type": update_type,
            "data": data,
            "timestamp": datetime.now()
        })

    async def process_updates(self):
        """Background worker to process updates"""

        while True:
            update = await self.update_queue.get()

            try:
                await self._apply_update(update)
            except Exception as e:
                logger.error(f"Failed to apply update: {e}")

            self.update_queue.task_done()

    async def _apply_update(self, update: Dict[str, Any]):
        """Apply single update"""

        profile = await self.storage.load_profile(update["user_id"])

        if update["type"] == "personality":
            profile.personality_traits = update["data"]
        elif update["type"] == "preference":
            profile.preferences.add_preference(**update["data"])
        elif update["type"] == "query":
            profile.interaction_history.add_query(update["data"])

        profile.last_updated = datetime.now()

        await self.storage.save_profile(profile)
```

---

## Personalized Experience Example

```python
class PersonalizedAgent:
    """Agent with personalization"""

    def __init__(
        self,
        user_memory_bank: UserMemoryBank,
        response_adapter: ResponseAdapter
    ):
        self.memory_bank = user_memory_bank
        self.adapter = response_adapter

    async def handle_query(
        self,
        user_id: str,
        query: str
    ) -> str:
        """Process query with personalization"""

        # 1. Load user profile
        profile = await self.memory_bank.get_or_create_profile(user_id)

        # 2. Retrieve relevant context based on preferences
        context = await self._get_personalized_context(
            query,
            profile
        )

        # 3. Generate response
        base_response = await self._generate_response(
            query,
            context,
            profile
        )

        # 4. Adapt to communication style
        adapted_response = self.adapter.adapt_response(
            base_response,
            profile.communication_style
        )

        # 5. Record interaction
        await self._record_interaction(
            user_id,
            query,
            adapted_response,
            profile
        )

        return adapted_response

    async def _get_personalized_context(
        self,
        query: str,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Build context based on user profile"""

        context = {
            "expertise_level": self._infer_expertise(query, profile),
            "preferred_detail_level": profile.personality_traits.detail_level,
            "recent_topics": profile.interaction_history._extract_topics(),
            "learning_goals": profile.goals
        }

        return context
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Weeks 1-2)
- [ ] Implement UserProfile schema
- [ ] Build UserMemoryBank storage
- [ ] Create update lifecycle system

### Phase 2: Personality System (Weeks 3-4)
- [ ] Implement PersonalityAnalyzer
- [ ] Build CommunicationStyle adapter
- [ ] Add personality inference

### Phase 3: Preference Tracking (Weeks 5-6)
- [ ] Build PreferenceSet system
- [ ] Implement preference trackers
- [ ] Add learning algorithms

### Phase 4: Query History (Weeks 7-8)
- [ ] Create InteractionHistory
- [ ] Implement QueryAnalyzer
- [ ] Build pattern detection

### Phase 5: Integration (Weeks 9-10)
- [ ] Integrate with agent system
- [ ] Add personalized responses
- [ ] Create analytics dashboard

---

## References

### Research Papers
1. **MemoryBank** - Long-term memory for LLM agents
2. **Big Five Personality Model** - Trait psychology
3. **Adaptive User Interfaces** - Personalization patterns

### Related SPECs
- **SPEC-040:** Feedback Loop System (learning from interactions)
- **SPEC-135:** Multi-Agent Expert Protocol (Memory Expert)
- **SPEC-031:** Relevance Scoring (personalized relevance)

---

**End of SPEC-079 (Enhanced)**
