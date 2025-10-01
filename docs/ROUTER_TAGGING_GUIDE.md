# Router Tagging Guide

## Purpose
This guide defines which tags should be applied to each router to control documentation visibility based on user roles.

## Tag Categories

### Public Tags (Unauthenticated Access)
- `auth` - Authentication endpoints (signup, login, password reset)
- `health` - Health check and status endpoints

### External Tags (VIEWER Role)
- `memory-public` - Safe memory operations (tokenize, recall)

### Member Tags (MEMBER, MAINTAINER Roles)
- `memory` - Full memory CRUD operations
- `context` - Context management
- `teams` - Team operations

### Admin Tags (ADMIN Role)
- `organizations` - Organization management
- `users` - User management
- `admin` - Admin-specific operations
- `analytics` - Usage analytics

### Staff Tags (OWNER, SYSTEM Roles)
- `metrics` - System metrics
- `ops` - Operational endpoints
- `billing` - Billing and subscriptions
- `audit` - Audit logs
- `queue` - Queue management
- `preload` - Memory preloading
- `session` - Session management

## Router Tag Assignments

### Authentication & Public
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `signup_api.py` | `authentication` | `auth` | Public signup/login |
| `enhanced_signup_api.py` | `enhanced-authentication` | `auth` | Enhanced signup flow |
| `token_api.py` | `token-management` | `auth` | Token operations |
| `memory_health_api.py` | `memory-health` | `health` | Health checks |

### Memory Operations
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `memory_api.py` | `memory` | `memory` | ✅ Correct |
| `memory_suggestions_api.py` | `memory_suggestions` | `memory` | Memory features |
| `memory_injection_api.py` | `memory_injection` | `memory` | Memory operations |
| `memory_acl_api.py` | `memory-acl` | `admin` | Access control (admin) |

### Team & Organization
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `standalone_teams_api.py` | `standalone-teams` | `teams` | Team management |
| `team_invitations_api.py` | `team-invitations` | `teams` | Team operations |
| `team_api_keys_api.py` | `team-api-keys` | `admin` | API key management |
| `team_billing_portal_api.py` | `team-billing-portal` | `billing` | Billing (staff only) |

### Analytics & Insights
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `usage_analytics_api.py` | `usage-analytics` | `analytics` | Usage analytics |
| `admin_analytics_api.py` | `admin-analytics` | `admin` | Admin analytics |
| `insights_api.py` | `dashboard` | `analytics` | Dashboard insights |
| `dashboard_widgets_api.py` | `dashboard` | `analytics` | Dashboard widgets |

### Billing & Subscriptions
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `billing_console_api.py` | `billing-console` | `billing` | Billing operations |
| `billing_engine_integration_api.py` | `billing-engine` | `billing` | Billing engine |
| `invoice_management_api.py` | `invoice-management` | `billing` | Invoice management |
| `standalone_teams_billing_api.py` | `standalone-teams-billing` | `billing` | Team billing |

### Advanced Features (Staff Only)
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `preload_api.py` | `memory-preloading` | `preload` | Memory preloading |
| `session_api.py` | `intelligent-sessions` | `session` | Session management |
| `queue_api.py` | `background-tasks` | `queue` | Queue operations |
| `performance_api.py` | `performance` | `metrics` | Performance metrics |

### Other
| Router | Current Tag | Recommended Tag | Reason |
|--------|-------------|-----------------|--------|
| `timeline_api.py` | `timeline` | `memory` | Timeline features |
| `discussion_api.py` | `discussion` | `memory` | Comments/discussion |
| `gamification_api.py` | `gamification` | `analytics` | Gamification features |
| `graph_intelligence_api.py` | `Graph Intelligence` | `analytics` | Graph intelligence |
| `ai_feedback_api.py` | `ai_feedback` | `ops` | AI feedback (internal) |
| `vendor_admin_api.py` | `vendor_admin` | `admin` | Vendor admin |
| `partner_ecosystem_api.py` | `partner-ecosystem` | `admin` | Partner management |
| `early_adopter_api.py` | `early-adopter-program` | `admin` | Early adopter program |

## Implementation Priority

### Phase 1: Critical Security (Immediate)
1. Tag all authentication routers with `auth`
2. Tag health endpoints with `health`
3. Tag admin/billing routers appropriately

### Phase 2: Role Separation (Next Sprint)
1. Separate member vs admin operations
2. Tag analytics appropriately
3. Tag team operations

### Phase 3: Fine-Grained Control (Future)
1. Split memory operations into public vs internal
2. Add more granular tags
3. Implement endpoint-level `include_in_schema=False` for debug endpoints

## Testing

After tagging routers, verify with:

```bash
# Test unauthenticated access (should see 401)
curl http://localhost:13390/docs

# Test VIEWER role (should see auth, health, memory-public)
# TODO: Add JWT token test

# Test ADMIN role (should see admin endpoints)
# TODO: Add JWT token test
```

## Notes

- Tags are case-sensitive
- Multiple tags per router are allowed
- Use `include_in_schema=False` for debug/internal endpoints
- Always test after changing tags
