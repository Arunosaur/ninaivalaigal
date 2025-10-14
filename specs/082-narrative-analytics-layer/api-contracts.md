# SPEC-082: Narrative Analytics API Contracts

This document defines the API endpoints for retrieving narrative analytics data.

---

### GET /narratives/{narrativeId}/summary

**Description**: Retrieves summary metrics for a specific narrative over a given time period.

**Authentication**: Required (JWT, user must have access to the organization).

**Parameters**:
- `narrativeId` (string, path, required): The ID of the narrative.
- `days` (integer, query, optional, default: 7): The number of days to look back for the summary.

**Response**: 200 OK
```json
{
  "narrativeId": "nar_123",
  "timePeriodDays": 7,
  "totalSessions": 1500,
  "completedSessions": 1200,
  "abandonmentRate": 0.2,
  "avgSessionDurationSeconds": 180,
  "uniqueUsers": 850
}
```

---

### GET /narratives/{narrativeId}/step-performance

**Description**: Returns detailed performance metrics for each step within a narrative.

**Authentication**: Required (JWT).

**Parameters**:
- `narrativeId` (string, path, required): The ID of the narrative.

**Response**: 200 OK
```json
{
  "narrativeId": "nar_123",
  "steps": [
    {
      "stepId": "step_A",
      "totalViews": 2000,
      "avgViewDurationSeconds": 30,
      "exitCount": 50,
      "exitRate": 0.025
    },
    {
      "stepId": "step_B",
      "totalViews": 1800,
      "avgViewDurationSeconds": 45,
      "exitCount": 150,
      "exitRate": 0.083
    }
  ]
}
```

---

### GET /narratives/{narrativeId}/path-analysis

**Description**: Provides data on the most common paths users take through a narrative.

**Authentication**: Required (JWT).

**Parameters**:
- `narrativeId` (string, path, required): The ID of the narrative.

**Response**: 200 OK
```json
{
  "narrativeId": "nar_123",
  "paths": [
    {
      "path": ["step_A", "step_B", "step_D_complete"],
      "sessionCount": 800,
      "percentage": 0.53
    },
    {
      "path": ["step_A", "step_C", "step_E_complete"],
      "sessionCount": 400,
      "percentage": 0.27
    }
  ]
}
```
