# Trust Scoring System

## Overview

Dynamic trust scoring (0-100) determines what actions are allowed between contexts.

---

## Trust Score Components

| Component | Max Points | Description |
|-----------|------------|-------------|
| **Org Reputation** | 40 | Aggregate trust of owning org (from ACL registry) |
| **Access History** | 30 | Frequency & success rate of prior references |
| **Policy Alignment** | 20 | Whether access matches data-sharing policies (SPEC-050) |
| **Recency Decay** | 10 | Time-based weighting (recent activity = higher trust) |
| **Penalties** | -25 | Security incidents, violations |

**Total**: 0-100 points

## Trust Score Formula

```
trust = (0.4 * org_reputation) + (0.3 * access_history) + (0.2 * policy_alignment) + (0.1 * recency_decay) - penalties
```

### Component Calculations:

**org_reputation**: From ACL registry
- Same user: 100
- Same team: 87.5
- Same org: 75
- Partner org: 50
- External: 12.5

**access_history**: e*M metrics. This component is calculated based on the history of interactions between the two contexts. A higher frequency of successful interactions over a longer period of time results in a higher score.
- `success_rate * frequency_score * duration_factor`
- success_rate: successful_accesses / total_accesses
- frequency_score: log(accesses_per_month + 1) / 5
- duration_factor: min(months_active / 12, 1.0)

**policy_alignment**: From SPEC-050
- Full alignment: 100
- Partial alignment: 50
- No alignment: 0

**recency_decay**: Internal clock. The score decays exponentially based on the number of days since the last interaction.
- `e^(-days_since_last_access / 90) * 100`

---

## Relationship Scoring

| Relationship | Points | Example |
|--------------|--------|---------|
| Same user | 40 | Personal → Personal |
| Same team | 35 | Team A → Team A |
| Same org | 30 | Dept A → Dept B |
| Trusted partner | 20 | Company A ↔ Company B |
| External | 5 | Internal → External API |

---

## Trust Levels & Actions

| Trust Level | Score Range | Allowed Actions |
|-------------|-------------|-----------------|
| **Full Access** | 90-100 | Reference, Clone, Sync |
| **Reference Only** | 70-89 | Reference, Clone |
| **Clone Only** | 50-69 | Clone only |
| **Read Only** | 30-49 | Read metadata only |
| **No Access** | 0-29 | Blocked |

---

## Trust Adjustment Triggers

### **Increase Trust** (+1 to +5):
- Successful access
- Compliance audit pass
- Security certification obtained
- Long-term good behavior

### **Decrease Trust** (-5 to -25):
- Failed access attempt
- Compliance violation
- Security incident
- Data breach

---

## Example Calculation

```
Context: Team A → Partner Org B

Base Scores:
├─ Relationship: 20 (trusted partner)
├─ Historical: 25 (good track record)
├─ Compliance: 18 (SOC2 certified)
└─ Security: 7 (MFA enabled)

Penalties:
└─ Recent incidents: -5 (minor issue 2 months ago)

Total: 20 + 25 + 18 + 7 - 5 = 65

Result: "Clone Only" access level
```

---

## Trust Score API

### Get Trust Score:
```http
GET /context-bridge/trust-score?source=ctx-1&target=ctx-2

Response:
{
  "trust_score": 65,
  "level": "clone_only",
  "allowed_actions": ["clone", "read"],
  "factors": {
    "relationship": 20,
    "historical": 25,
    "compliance": 18,
    "security": 7
  },
  "penalties": -5,
  "recommendations": [
    "Complete annual audit for +2 points",
    "Enable 2FA for +3 points"
  ]
}
```

