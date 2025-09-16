# Spec 009: RBAC Policy Enforcement Enhancement

## Overview
Enhance the existing RBAC system with context sensitivity tiers, policy visualization tools, and comprehensive enforcement mechanisms that bridge documentation to code implementation.

## Objectives
- Extend RBAC with context sensitivity tier enforcement
- Add policy visualization tool for effective permissions
- Implement comprehensive `@require_permission` decorator coverage
- Create RBAC guardrails at ORM layer to prevent cross-org data leaks
- Build policy matrix tests for all role/resource combinations
- Add permission inheritance with clear precedence rules

## Architecture

### Enhanced RBAC Components
```
server/rbac/
├── __init__.py
├── permissions.py           # Existing roles, actions, resources
├── policy/
│   ├── __init__.py
│   ├── enforcement.py       # Policy enforcement engine
│   ├── visualization.py     # Policy visualization tools
│   ├── inheritance.py       # Permission inheritance logic
│   └── matrix_tests.py      # Automated policy matrix testing
├── decorators/
│   ├── __init__.py
│   ├── enhanced_decorators.py  # Context-sensitive decorators
│   └── orm_guardrails.py    # Database-level access controls
└── audit/
    ├── __init__.py
    ├── policy_audit.py      # Policy decision auditing
    └── compliance_reports.py # Compliance reporting tools
```

## Technical Specifications

### 1. Context Sensitivity Integration

#### Enhanced Permission Checking
```python
class ContextSensitiveRBACContext(RBACContext):
    def has_permission_with_sensitivity(
        self, 
        resource: Resource, 
        action: Action, 
        context_sensitivity: ContextSensitivity = None,
        resource_id: str = None
    ) -> bool:
        """Check permission with context sensitivity awareness"""
        
        # Get base permission from existing RBAC
        has_base_permission = self.has_permission(resource, action)
        if not has_base_permission:
            return False
        
        # Apply sensitivity tier restrictions
        if context_sensitivity:
            return self._check_sensitivity_access(
                self.user_role, 
                context_sensitivity, 
                action
            )
        
        return True
    
    def _check_sensitivity_access(
        self, 
        role: Role, 
        sensitivity: ContextSensitivity, 
        action: Action
    ) -> bool:
        """Check if role can perform action on given sensitivity tier"""
        from rbac_policy_mapping import ROLE_SENSITIVITY_MATRIX
        
        allowed_tiers = ROLE_SENSITIVITY_MATRIX.get(role, [])
        return sensitivity in allowed_tiers
```

#### Context Sensitivity Decorator
```python
def require_permission_with_sensitivity(
    resource: Resource, 
    action: Action,
    sensitivity_param: str = "sensitivity_tier"
):
    """Enhanced decorator that considers context sensitivity"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'headers') else None)
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")
            
            rbac_context = getattr(request.state, 'rbac_context', None)
            if not rbac_context:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get sensitivity tier from request
            sensitivity_tier = None
            if sensitivity_param in kwargs:
                sensitivity_tier = ContextSensitivity(kwargs[sensitivity_param])
            
            # Check permission with sensitivity
            if not rbac_context.has_permission_with_sensitivity(
                resource, action, sensitivity_tier
            ):
                # Log policy denial with context
                audit_policy_denial(
                    user_id=rbac_context.user_id,
                    resource=resource,
                    action=action,
                    sensitivity_tier=sensitivity_tier,
                    reason="insufficient_role_for_sensitivity"
                )
                
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: {action.name} on {resource.name} "
                           f"(tier: {sensitivity_tier.value if sensitivity_tier else 'none'})"
                )
            
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator
```

### 2. Policy Visualization Tool

#### Permission Matrix Generator
```python
class PolicyVisualizationEngine:
    def generate_permission_matrix(self) -> Dict[str, Any]:
        """Generate comprehensive permission matrix for visualization"""
        matrix = {
            'roles': [role.value for role in Role],
            'resources': [resource.value for resource in Resource],
            'actions': [action.value for action in Action],
            'sensitivity_tiers': [tier.value for tier in ContextSensitivity],
            'permissions': {},
            'inheritance_rules': self._get_inheritance_rules(),
            'effective_permissions': {}
        }
        
        # Generate permission combinations
        for role in Role:
            matrix['permissions'][role.value] = {}
            for resource in Resource:
                matrix['permissions'][role.value][resource.value] = {}
                for action in Action:
                    matrix['permissions'][role.value][resource.value][action.value] = {
                        'allowed': self._check_base_permission(role, resource, action),
                        'sensitivity_access': self._get_sensitivity_access(role),
                        'conditions': self._get_permission_conditions(role, resource, action)
                    }
        
        return matrix
    
    def generate_user_effective_permissions(self, user_id: int) -> Dict[str, Any]:
        """Generate effective permissions for specific user"""
        user_roles = self._get_user_roles(user_id)
        
        effective_permissions = {
            'user_id': user_id,
            'roles': user_roles,
            'scopes': self._get_user_scopes(user_id),
            'permissions': {},
            'restrictions': {},
            'inheritance_chain': {}
        }
        
        # Calculate effective permissions across all roles
        for scope_type, roles in user_roles.items():
            for role in roles:
                self._merge_role_permissions(effective_permissions, role, scope_type)
        
        return effective_permissions
```

#### Web-Based Visualization Interface
```python
@app.get("/rbac/visualization/matrix")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_policy_matrix(request: Request):
    """Get policy matrix for visualization"""
    viz_engine = PolicyVisualizationEngine()
    matrix = viz_engine.generate_permission_matrix()
    
    return {
        "matrix": matrix,
        "generated_at": datetime.utcnow(),
        "version": "1.0"
    }

@app.get("/rbac/visualization/user/{user_id}")
@require_permission(Resource.USER, Action.READ)
async def get_user_permissions_visualization(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get user-specific permission visualization"""
    
    # Check if current user can view target user's permissions
    rbac_context = getattr(request.state, 'rbac_context', None)
    if not rbac_context.can_view_user_permissions(user_id):
        raise HTTPException(status_code=403, detail="Cannot view user permissions")
    
    viz_engine = PolicyVisualizationEngine()
    user_permissions = viz_engine.generate_user_effective_permissions(user_id)
    
    return user_permissions
```

### 3. ORM-Level Guardrails

#### Database Access Control Layer
```python
class RBACQueryGuard:
    """ORM-level guardrails to prevent cross-org data access"""
    
    def __init__(self, rbac_context: RBACContext):
        self.rbac_context = rbac_context
    
    def apply_org_isolation(self, query, model_class):
        """Apply organization-level data isolation"""
        if not hasattr(model_class, 'organization_id'):
            return query
        
        user_org_id = self.rbac_context.organization_id
        if user_org_id:
            # Restrict to user's organization
            query = query.filter(model_class.organization_id == user_org_id)
        elif not self.rbac_context.has_role(Role.SYSTEM):
            # Non-system users without org should see nothing
            query = query.filter(False)  # Empty result set
        
        return query
    
    def apply_team_isolation(self, query, model_class):
        """Apply team-level data isolation"""
        if not hasattr(model_class, 'team_id'):
            return query
        
        user_teams = self.rbac_context.teams
        if user_teams:
            query = query.filter(model_class.team_id.in_(user_teams.keys()))
        elif not self.rbac_context.has_role(Role.ADMIN):
            # Non-admin users without teams should see nothing
            query = query.filter(False)
        
        return query
    
    def apply_context_sensitivity_filter(self, query, model_class):
        """Filter based on context sensitivity and user role"""
        if not hasattr(model_class, 'sensitivity_tier'):
            return query
        
        allowed_tiers = self._get_allowed_sensitivity_tiers()
        query = query.filter(model_class.sensitivity_tier.in_(allowed_tiers))
        
        return query

# Enhanced database manager with RBAC guardrails
class RBACEnhancedDatabaseManager(DatabaseManager):
    def get_session_with_rbac(self, rbac_context: RBACContext):
        """Get database session with RBAC guardrails applied"""
        session = self.get_session()
        session.rbac_guard = RBACQueryGuard(rbac_context)
        return session
    
    def get_memories_with_rbac(self, rbac_context: RBACContext, **filters):
        """Get memories with RBAC filtering applied"""
        session = self.get_session_with_rbac(rbac_context)
        query = session.query(Memory)
        
        # Apply RBAC guardrails
        query = session.rbac_guard.apply_org_isolation(query, Memory)
        query = session.rbac_guard.apply_team_isolation(query, Memory)
        query = session.rbac_guard.apply_context_sensitivity_filter(query, Memory)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(Memory, key):
                query = query.filter(getattr(Memory, key) == value)
        
        return query.all()
```

### 4. Permission Inheritance System

#### Inheritance Rules Engine
```python
class PermissionInheritanceEngine:
    """Manages permission inheritance across scopes"""
    
    INHERITANCE_PRECEDENCE = [
        'global',      # Highest precedence
        'organization',
        'team', 
        'context',     # Lowest precedence
    ]
    
    def calculate_effective_permissions(self, user_roles: Dict[str, Role]) -> Dict[str, Set[Permission]]:
        """Calculate effective permissions considering inheritance"""
        effective_permissions = {}
        
        # Process roles in precedence order (highest first)
        for scope_type in self.INHERITANCE_PRECEDENCE:
            if scope_type in user_roles:
                role = user_roles[scope_type]
                scope_permissions = self._get_role_permissions(role, scope_type)
                
                # Merge with existing permissions (higher precedence wins)
                effective_permissions = self._merge_permissions(
                    effective_permissions, 
                    scope_permissions,
                    precedence=scope_type
                )
        
        return effective_permissions
    
    def _merge_permissions(self, existing: Dict, new_permissions: Dict, precedence: str) -> Dict:
        """Merge permissions with precedence rules"""
        for resource, actions in new_permissions.items():
            if resource not in existing:
                existing[resource] = {}
            
            for action, permission_info in actions.items():
                # Higher precedence always wins
                if action not in existing[resource] or self._has_higher_precedence(precedence, existing[resource][action]['scope']):
                    existing[resource][action] = {
                        'allowed': permission_info['allowed'],
                        'scope': precedence,
                        'conditions': permission_info.get('conditions', [])
                    }
        
        return existing
```

### 5. Policy Matrix Testing

#### Automated Policy Tests
```python
class PolicyMatrixTestSuite:
    """Comprehensive testing of all role/resource/action combinations"""
    
    def test_all_permission_combinations(self):
        """Test every role/resource/action combination"""
        test_results = []
        
        for role in Role:
            for resource in Resource:
                for action in Action:
                    for sensitivity in ContextSensitivity:
                        result = self._test_permission_combination(
                            role, resource, action, sensitivity
                        )
                        test_results.append(result)
        
        return self._generate_test_report(test_results)
    
    def _test_permission_combination(self, role: Role, resource: Resource, action: Action, sensitivity: ContextSensitivity) -> Dict:
        """Test specific permission combination"""
        # Create mock RBAC context
        mock_context = self._create_mock_rbac_context(role)
        
        # Test permission
        expected_result = self._get_expected_permission(role, resource, action, sensitivity)
        actual_result = mock_context.has_permission_with_sensitivity(resource, action, sensitivity)
        
        return {
            'role': role.value,
            'resource': resource.value,
            'action': action.value,
            'sensitivity': sensitivity.value,
            'expected': expected_result,
            'actual': actual_result,
            'passed': expected_result == actual_result,
            'test_timestamp': datetime.utcnow()
        }
    
    def generate_policy_compliance_report(self) -> Dict:
        """Generate compliance report for audit purposes"""
        test_results = self.test_all_permission_combinations()
        
        return {
            'total_combinations_tested': len(test_results),
            'passed_tests': len([r for r in test_results if r['passed']]),
            'failed_tests': len([r for r in test_results if not r['passed']]),
            'compliance_percentage': len([r for r in test_results if r['passed']]) / len(test_results) * 100,
            'failed_combinations': [r for r in test_results if not r['passed']],
            'generated_at': datetime.utcnow(),
            'policy_version': self._get_policy_version()
        }
```

## Database Schema Enhancements

### Policy Audit Table
```sql
CREATE TABLE policy_audits (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    sensitivity_tier VARCHAR(50),
    decision VARCHAR(20) NOT NULL, -- 'allowed', 'denied'
    reason VARCHAR(255),
    context_id INTEGER REFERENCES contexts(id),
    request_id VARCHAR(255),
    effective_role VARCHAR(50),
    scope_type VARCHAR(50),
    scope_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_policy_audits_user_id ON policy_audits(user_id);
CREATE INDEX idx_policy_audits_timestamp ON policy_audits(timestamp);
CREATE INDEX idx_policy_audits_decision ON policy_audits(decision);
CREATE INDEX idx_policy_audits_resource_action ON policy_audits(resource, action);
```

### Enhanced Context Table
```sql
ALTER TABLE contexts ADD COLUMN sensitivity_tier VARCHAR(50) DEFAULT 'internal';
ALTER TABLE contexts ADD COLUMN auto_classified BOOLEAN DEFAULT FALSE;
ALTER TABLE contexts ADD COLUMN classification_confidence FLOAT;
ALTER TABLE contexts ADD COLUMN last_sensitivity_review TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_contexts_sensitivity_tier ON contexts(sensitivity_tier);
```

## API Enhancements

### Enhanced Endpoint Protection
```python
# Example of enhanced endpoint with sensitivity awareness
@app.post("/contexts")
@require_permission_with_sensitivity(Resource.CONTEXT, Action.CREATE, "sensitivity_tier")
async def create_context_with_sensitivity(
    request: Request,
    context_data: ContextCreateWithSensitivity,
    current_user: User = Depends(get_current_user)
):
    """Create context with automatic sensitivity classification"""
    
    # Auto-classify sensitivity if not provided
    if not context_data.sensitivity_tier:
        classifier = ContextSensitivityClassifier()
        context_data.sensitivity_tier = classifier.classify_content(
            context_data.description or context_data.name
        )
    
    # Apply redaction based on sensitivity
    redactor = ContextualRedactor()
    redacted_data = redactor.redact_with_context(
        context_data.dict(), 
        context_data.sensitivity_tier
    )
    
    # Create context with sensitivity metadata
    context = await create_context_with_metadata(
        redacted_data, 
        current_user.id,
        sensitivity_tier=context_data.sensitivity_tier
    )
    
    return {"context": context}

# Policy visualization endpoints
@app.get("/rbac/policy/visualization")
@require_permission(Resource.SYSTEM, Action.READ)
async def get_policy_visualization_data(request: Request):
    """Get data for policy visualization dashboard"""
    viz_engine = PolicyVisualizationEngine()
    return viz_engine.generate_permission_matrix()

@app.get("/rbac/policy/test-results")
@require_permission(Resource.SYSTEM, Action.AUDIT)
async def get_policy_test_results(request: Request):
    """Get automated policy matrix test results"""
    test_suite = PolicyMatrixTestSuite()
    return test_suite.generate_policy_compliance_report()
```

## Implementation Plan

### Phase 1: Context Sensitivity Integration (Week 3)
1. Enhance existing RBAC decorators with sensitivity awareness
2. Implement context sensitivity classification
3. Add sensitivity-based permission checking
4. Create policy audit logging
5. Update existing endpoints with enhanced decorators

### Phase 2: Policy Visualization & ORM Guardrails (Week 4)
1. Build policy visualization engine
2. Create web-based policy matrix viewer
3. Implement ORM-level access controls
4. Add permission inheritance engine
5. Create automated policy matrix tests

## Configuration

### Enhanced RBAC Configuration
```yaml
# server/rbac/policy/config.yaml
rbac_policy:
  sensitivity_enforcement: true
  auto_classification: true
  inheritance_enabled: true
  
  visualization:
    enabled: true
    cache_duration: 300  # 5 minutes
    
  orm_guardrails:
    enabled: true
    strict_isolation: true
    
  audit:
    log_all_decisions: true
    include_context: true
    retention_days: 2555  # 7 years
```

## Testing Strategy

### Policy Matrix Tests
```python
@pytest.mark.parametrize("role,resource,action,sensitivity", [
    (Role.VIEWER, Resource.MEMORY, Action.READ, ContextSensitivity.PUBLIC),
    (Role.MEMBER, Resource.CONTEXT, Action.CREATE, ContextSensitivity.INTERNAL),
    (Role.ADMIN, Resource.SYSTEM, Action.CONFIGURE, ContextSensitivity.RESTRICTED),
    # ... all combinations
])
def test_policy_matrix_combination(role, resource, action, sensitivity):
    """Test specific policy matrix combination"""
    context = create_mock_rbac_context(role)
    expected = get_expected_permission_from_policy_mapping(role, resource, action, sensitivity)
    actual = context.has_permission_with_sensitivity(resource, action, sensitivity)
    assert actual == expected
```

## Success Criteria

### Functional Requirements
- [ ] All existing endpoints enhanced with sensitivity-aware decorators
- [ ] Policy visualization tool shows accurate permission matrix
- [ ] ORM guardrails prevent cross-org data access
- [ ] Permission inheritance follows documented precedence rules
- [ ] Automated policy tests achieve 100% coverage

### Security Requirements
- [ ] No permission bypass possible at database level
- [ ] All policy decisions logged for audit
- [ ] Sensitivity tier enforcement prevents data leaks
- [ ] Cross-org queries blocked by ORM guardrails
- [ ] Permission inheritance cannot escalate privileges

### Compliance Requirements
- [ ] Policy matrix tests generate compliance reports
- [ ] All permission decisions auditable
- [ ] Sensitivity classification meets regulatory requirements
- [ ] Permission changes tracked with full audit trail
- [ ] Visualization tool supports compliance reviews

This specification builds directly on the existing RBAC foundation while adding enterprise-grade policy enforcement, visualization, and compliance capabilities.
