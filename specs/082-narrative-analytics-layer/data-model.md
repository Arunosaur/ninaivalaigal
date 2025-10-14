# SPEC-082: Narrative Analytics Data Model

This document defines the data model for tracking user interactions within the Visual Narrative Layer (SPEC-076).

---

## 1. Narrative Events Schema

Events fired from the frontend and backend to track user journeys through a narrative.

**Base Event Schema:**
```json
{
  "eventId": "uuid",
  "timestamp": "iso8601",
  "eventName": "string",
  "userId": "uuid",
  "organizationId": "uuid",
  "narrativeId": "uuid",
  "sessionId": "uuid",
  "payload": {}
}
```

**Narrative-Specific Events:**

- **`narrative.session.start`**: Fired when a user begins interacting with a narrative.
- **`narrative.step.view`**: When a step (a single piece of content) is displayed.
- **`narrative.branch.select`**: When a user chooses a branch or path.
- **`narrative.feedback.submit`**: When a user provides explicit feedback (e.g., a rating or comment) on a narrative step.
- **`narrative.session.abandon`**: Fired if a user leaves a narrative flow mid-way.
- **`narrative.session.complete`**: When a user reaches a designated end-point of a narrative.

**Example Event: `narrative.branch.select`**
```json
{
  "eventId": "evt_narr_6789",
  "timestamp": "2025-10-14T19:00:00Z",
  "eventName": "narrative.branch.select",
  "userId": "user_abc",
  "organizationId": "org_xyz",
  "narrativeId": "nar_123",
  "sessionId": "sess_456",
  "payload": {
    "fromStepId": "step_A",
    "toStepId": "step_B",
    "branchType": "user_choice",
    "decisionTimeMs": 1500
  }
}
```

---

## 2. Aggregation Tables Design

These tables will power the analytics dashboard by providing pre-computed metrics.

**`narrative_daily_summary` Table:**
- **Description**: Aggregates high-level narrative metrics per day.
- **Columns**:
  - `date`: (DATE, PRIMARY KEY)
  - `narrativeId`: (UUID, PRIMARY KEY)
  - `totalSessions`: (INTEGER)
  - `completedSessions`: (INTEGER)
  - `abandonedSessions`: (INTEGER)
  - `avgSessionDuration`: (SECONDS)
  - `uniqueUsers`: (INTEGER)

**`narrative_step_performance` Table:**
- **Description**: Tracks performance and drop-off rates for each step in a narrative.
- **Columns**:
  - `narrativeId`: (UUID, PRIMARY KEY)
  - `stepId`: (STRING, PRIMARY KEY)
  - `totalViews`: (INTEGER)
  - `avgViewDuration`: (SECONDS)
  - `exitCount`: (INTEGER) - How many sessions ended after this step.
  - `feedbackScore`: (DECIMAL) - Average feedback rating.

---

## 3. Time-Series Data Structure

- **Purpose**: For real-time monitoring of narrative engagement.
- **Data Points**:
  - `narrative_step_views`: (count, narrativeId, stepId)
  - `narrative_active_sessions`: (gauge, narrativeId)
- **Resolution**: Stored at a 1-minute resolution for real-time dashboards.

---

## 4. Retention Policies

- **Raw Narrative Events (Event Bus)**: Retained for **14 days**.
- **Aggregated Tables (Data Warehouse)**: Retained for **2 years** to allow for long-term trend analysis of narrative effectiveness.
- **Time-Series Data**: 1-minute resolution retained for **7 days**.
