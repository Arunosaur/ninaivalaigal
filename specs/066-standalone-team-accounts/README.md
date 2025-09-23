# SPEC-066: Standalone Team Accounts

**Status**: 📋 **PLANNED** - Ready for Implementation  
**Priority**: High (Enables SaaS Monetization Pipeline)  
**Created**: 2024-09-23  
**Authors**: Arun Rajagopalan  

## Title:
Standalone Team Account Support (No Organization Binding)

## Objective:
Support creation and management of teams that are not tied to any parent organization. These "standalone teams" allow collaborative usage of the memory platform by informal groups, startups, classrooms, or projects without requiring org-level infrastructure.

## Motivation:
Many use cases require group collaboration but do not belong to a formal organization:
- Small project teams or working groups
- Classroom/student collaborations  
- Informal communities or nonprofits
- Startups evaluating the platform pre-onboarding

Requiring an organization setup is a friction point for such users. This SPEC ensures multi-user collaboration is possible without needing an organization entity.

## Scope:
**Inclusions:**
- Team creation without organization requirement
- Team-scoped RBAC (admin, contributor, viewer)
- Team invitation and join flows
- Upgrade path from standalone team to organization
- Team-isolated memory and context management

**Exclusions:**
- Organization-level billing (teams remain free/freemium)
- Cross-team collaboration (handled by SPEC-049/050)
- Advanced org features (audit logs, compliance, etc.)

## Technical Design:

### Architecture:
```
Individual User → Standalone Team → Organization
     (Free)     →    (Free/Freemium)  →  (Enterprise)
```

### Components:
- Extended User model with `standalone_team_id` reference
- Extended Team model with `is_standalone` flag
- Team invitation system with email tokens
- Upgrade workflow from team to organization

### APIs/Endpoints:
- `POST /auth/signup/team-create` - Create team during signup
- `POST /auth/signup/team-join` - Join team during signup  
- `POST /team/create-standalone` - Create team from dashboard
- `GET /team/my` - Get current user's team info
- `POST /team/invite` - Send team invitations
- `POST /team/{id}/upgrade-to-org` - Upgrade team to organization

### Dependencies:
- SPEC-002: Multi-User Authentication (base auth system)
- SPEC-007: Team Collaboration & Roles (existing RBAC)
- SPEC-025: Vendor Admin Console (team analytics)

## User Stories:
- [ ] As a startup founder, I want to create a team account so my co-founders can collaborate on memories
- [ ] As a student, I want to join a classroom team so I can share study materials with classmates
- [ ] As a project lead, I want to invite team members so we can collaborate without setting up an organization
- [ ] As a team admin, I want to upgrade to an organization so we can access billing and advanced features
- [ ] As a vendor admin, I want to track standalone teams so I can analyze conversion opportunities

## Acceptance Criteria:
- [ ] Users can create standalone teams during signup or from dashboard
- [ ] Team invitations work via email with secure tokens
- [ ] RBAC is enforced within team boundaries (admin/contributor/viewer)
- [ ] Team members can only see team-scoped memories and contexts
- [ ] Standalone teams can upgrade to organizations seamlessly
- [ ] Team creation does not require organization metadata
- [ ] Should support graceful degradation if team features are disabled

## Implementation Phases:

### Phase 1: Core Team Model (Week 1)
- Extend database schema for standalone teams
- Update User/Team relationship models
- Basic team creation and membership APIs
- Team-scoped authentication middleware

### Phase 2: Signup Flow Integration (Week 1)
- Add "Create Team" and "Join Team" signup options
- Team invitation system with email tokens
- Frontend UI for team signup flows
- Team dashboard and member management

### Phase 3: Team Operations (Week 2)
- Team member invitation and role management
- Team-scoped memory and context isolation
- Team settings and configuration
- Basic team analytics for vendor admin

### Phase 4: Organization Upgrade Path (Week 1)
- Upgrade workflow from team to organization
- Data migration and role preservation
- Billing integration preparation
- Upgrade analytics and tracking

## Risks and Mitigations:
- **Risk**: Database schema changes affect existing users
- **Mitigation**: Careful migration scripts with rollback capability, extensive testing

- **Risk**: Three signup paths create UX confusion  
- **Mitigation**: Clear UI design with guided onboarding flows

- **Risk**: Team isolation breaks existing functionality
- **Mitigation**: Comprehensive testing of team-scoped features, gradual rollout

- **Risk**: Free teams create resource drain without revenue
- **Mitigation**: Resource limits for standalone teams, conversion tracking

## Success Metrics:
- [ ] Standalone team creation rate (target: 20% of new signups)
- [ ] Team-to-organization conversion rate (target: 15% within 6 months)
- [ ] Average team size before upgrade (target: 3-5 members)
- [ ] User retention in teams vs individual accounts (target: 2x higher)
- [ ] Revenue per converted team (target: $50/month average)

## Dependencies on Existing SPECs:
- **Requires**: SPEC-002 (Authentication), SPEC-007 (Team Roles)
- **Integrates with**: SPEC-025 (Vendor Admin), SPEC-040/041 (AI Features)
- **Enables**: SPEC-026/027 (Billing), SPEC-049/050 (Collaboration)

## Performance Requirements:
- Team creation: <500ms response time
- Team invitation: <200ms email sending
- Team member lookup: <100ms for team-scoped queries
- Upgrade process: <2 seconds end-to-end

## Security Considerations:
- Team invitation tokens expire in 7 days
- Team admin role required for sensitive operations
- Team data isolation enforced at database level
- Audit trail for team membership changes

## Testing Strategy:
- Unit tests: 90% coverage for team management logic
- Integration tests: Full signup flow testing
- Performance tests: Team operations under load
- Security tests: Team isolation and permission boundaries

## Contributors:
- **Owner**: Arun Rajagopalan
- **Reviewers**: Platform Team
- **Stakeholders**: Product, Engineering, Business Development
