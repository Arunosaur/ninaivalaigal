# SPEC-082: Narrative Analytics Queries

This document provides example aggregation queries for the Narrative Analytics Layer.

---

## 1. Daily Narrative Summary

**Description**: This query populates the `narrative_daily_summary` table by aggregating raw session data.

```sql
-- This is a conceptual query. The exact syntax will depend on the data warehouse.
INSERT INTO narrative_daily_summary (date, narrativeId, totalSessions, completedSessions, abandonedSessions, avgSessionDuration, uniqueUsers)
SELECT
    DATE(timestamp) as date,
    narrativeId,
    COUNT(DISTINCT sessionId) as totalSessions,
    COUNT(DISTINCT CASE WHEN eventName = 'narrative.session.complete' THEN sessionId END) as completedSessions,
    COUNT(DISTINCT CASE WHEN eventName = 'narrative.session.abandon' THEN sessionId END) as abandonedSessions,
    AVG(sessionDurationSeconds) as avgSessionDuration,
    COUNT(DISTINCT userId) as uniqueUsers
FROM raw_narrative_events
GROUP BY 1, 2;
```

---

## 2. Step Drop-off Analysis

**Description**: This query calculates the drop-off rate for each step in a narrative, which is crucial for identifying confusing or unengaging content.

```sql
WITH step_views AS (
    SELECT
        narrativeId,
        payload->>'stepId' as stepId,
        COUNT(DISTINCT sessionId) as totalViews
    FROM raw_narrative_events
    WHERE eventName = 'narrative.step.view'
    GROUP BY 1, 2
),
step_exits AS (
    SELECT
        narrativeId,
        payload->>'fromStepId' as stepId,
        COUNT(DISTINCT sessionId) as exitCount
    FROM raw_narrative_events
    WHERE eventName = 'narrative.session.abandon'
    GROUP BY 1, 2
)
SELECT
    sv.narrativeId,
    sv.stepId,
    sv.totalViews,
    COALESCE(se.exitCount, 0) as exitCount,
    (COALESCE(se.exitCount, 0) * 1.0 / sv.totalViews) as exitRate
FROM step_views sv
LEFT JOIN step_exits se ON sv.narrativeId = se.narrativeId AND sv.stepId = se.stepId;
```

---

## 3. Common Path Analysis

**Description**: Identifies the most common sequences of steps (paths) that users take within a narrative.

```sql
-- This query is complex and often requires window functions or sessionization logic.
SELECT
    narrativeId,
    path,
    COUNT(sessionId) as sessionCount
FROM (
    SELECT
        sessionId,
        narrativeId,
        ARRAY_AGG(payload->>'stepId' ORDER BY timestamp) as path
    FROM raw_narrative_events
    WHERE eventName = 'narrative.step.view'
    GROUP BY 1, 2
)
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 10;
```
