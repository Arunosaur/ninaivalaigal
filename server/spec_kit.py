"""
Spec-Kit Framework for Ninaivalaigal
Standardized interfaces and implementations for all system components
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ContextScope(Enum):
    PERSONAL = "personal"
    TEAM = "team"
    ORGANIZATION = "organization"

class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"

@dataclass
class ContextSpec:
    """Standard context specification"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    scope: ContextScope = ContextScope.PERSONAL
    owner_id: Optional[int] = None
    team_id: Optional[int] = None
    organization_id: Optional[int] = None
    visibility: str = "private"
    is_active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class ContextPermissionSpec:
    """Standard context permission specification"""
    context_id: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    organization_id: Optional[int] = None
    permission_level: PermissionLevel = PermissionLevel.READ
    granted_by: Optional[int] = None

@dataclass
class ContextOperationResult:
    """Standard result for context operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

class ContextValidationError(Exception):
    """Context validation error"""
    pass

class ContextPermissionError(Exception):
    """Context permission error"""
    pass

class ContextInterface(ABC):
    """Standard interface for context operations"""
    
    @abstractmethod
    def create_context(self, spec: ContextSpec, user_id: int) -> ContextOperationResult:
        """Create a new context"""
        pass
    
    @abstractmethod
    def get_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        """Get context by ID"""
        pass
    
    @abstractmethod
    def list_contexts(self, user_id: int, scope: Optional[ContextScope] = None) -> ContextOperationResult:
        """List user-accessible contexts"""
        pass
    
    @abstractmethod
    def update_context(self, context_id: int, updates: Dict[str, Any], user_id: int) -> ContextOperationResult:
        """Update context"""
        pass
    
    @abstractmethod
    def delete_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        """Delete context"""
        pass
    
    @abstractmethod
    def resolve_context(self, name: str, user_id: int, scope_hint: Optional[ContextScope] = None) -> ContextOperationResult:
        """Resolve context by name with scope priority"""
        pass
    
    @abstractmethod
    def share_context(self, context_id: int, permission: ContextPermissionSpec, user_id: int) -> ContextOperationResult:
        """Share context with permissions"""
        pass
    
    @abstractmethod
    def transfer_context(self, context_id: int, target_type: str, target_id: int, user_id: int) -> ContextOperationResult:
        """Transfer context ownership"""
        pass
    
    @abstractmethod
    def activate_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        """Set context as active"""
        pass
    
    @abstractmethod
    def deactivate_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        """Deactivate context"""
        pass

class ContextValidator:
    """Standard context validation logic"""
    
    @staticmethod
    def validate_context_spec(spec: ContextSpec) -> None:
        """Validate context specification"""
        if not spec.name or not spec.name.strip():
            raise ContextValidationError("Context name is required")
        
        if len(spec.name) > 255:
            raise ContextValidationError("Context name too long (max 255 characters)")
        
        # Validate scope ownership constraints
        if spec.scope == ContextScope.PERSONAL:
            if not spec.owner_id or spec.team_id or spec.organization_id:
                raise ContextValidationError("Personal context must have owner_id only")
        elif spec.scope == ContextScope.TEAM:
            if not spec.team_id or spec.owner_id or spec.organization_id:
                raise ContextValidationError("Team context must have team_id only")
        elif spec.scope == ContextScope.ORGANIZATION:
            if not spec.organization_id or spec.owner_id or spec.team_id:
                raise ContextValidationError("Organization context must have organization_id only")
    
    @staticmethod
    def validate_permission_spec(permission: ContextPermissionSpec) -> None:
        """Validate permission specification"""
        target_count = sum([
            1 if permission.user_id else 0,
            1 if permission.team_id else 0,
            1 if permission.organization_id else 0
        ])
        
        if target_count != 1:
            raise ContextValidationError("Permission must target exactly one entity (user, team, or organization)")

class ContextResolver:
    """Standard context resolution logic"""
    
    @staticmethod
    def resolve_priority(contexts: List[ContextSpec], user_id: int) -> Optional[ContextSpec]:
        """Resolve context with priority: personal > team > organization > shared"""
        if not contexts:
            return None
        
        # Priority 1: Personal contexts owned by user
        personal = [c for c in contexts if c.scope == ContextScope.PERSONAL and c.owner_id == user_id]
        if personal:
            return personal[0]
        
        # Priority 2: Team contexts (user is member)
        team = [c for c in contexts if c.scope == ContextScope.TEAM]
        if team:
            return team[0]
        
        # Priority 3: Organization contexts
        org = [c for c in contexts if c.scope == ContextScope.ORGANIZATION]
        if org:
            return org[0]
        
        # Priority 4: Shared contexts
        return contexts[0]

class SpecKitContextManager(ContextInterface):
    """Spec-kit compliant context manager implementation"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.validator = ContextValidator()
        self.resolver = ContextResolver()
    
    def create_context(self, spec: ContextSpec, user_id: int) -> ContextOperationResult:
        """Create context through spec-kit interface"""
        try:
            # Validate specification
            self.validator.validate_context_spec(spec)
            
            # Check permissions for non-personal contexts
            if spec.scope == ContextScope.TEAM and spec.team_id:
                if not self._check_team_admin_permission(user_id, spec.team_id):
                    raise ContextPermissionError("Only team admins can create team contexts")
            
            elif spec.scope == ContextScope.ORGANIZATION and spec.organization_id:
                if not self._check_org_admin_permission(user_id):
                    raise ContextPermissionError("Only organization admins can create org contexts")
            
            # Create context using database manager
            context = self.db.create_context(
                name=spec.name,
                description=spec.description,
                user_id=spec.owner_id,
                team_id=spec.team_id,
                organization_id=spec.organization_id,
                scope=spec.scope.value
            )
            
            return ContextOperationResult(
                success=True,
                message=f"Context '{spec.name}' created successfully",
                data={"context": self._context_to_dict(context)}
            )
            
        except (ContextValidationError, ContextPermissionError) as e:
            return ContextOperationResult(
                success=False,
                message=str(e),
                error_code="VALIDATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Context creation failed: {e}")
            return ContextOperationResult(
                success=False,
                message="Internal server error",
                error_code="INTERNAL_ERROR"
            )
    
    def resolve_context(self, name: str, user_id: int, scope_hint: Optional[ContextScope] = None) -> ContextOperationResult:
        """Resolve context by name with scope priority"""
        try:
            # Get all contexts with matching name that user can access
            contexts = self.db.find_contexts_by_name(name, user_id)
            
            if not contexts:
                return ContextOperationResult(
                    success=False,
                    message=f"No accessible context found with name '{name}'",
                    error_code="NOT_FOUND"
                )
            
            # Convert to specs for resolution
            context_specs = [self._context_to_spec(c) for c in contexts]
            
            # Apply scope hint if provided
            if scope_hint:
                filtered = [c for c in context_specs if c.scope == scope_hint]
                if filtered:
                    context_specs = filtered
            
            # Resolve with priority
            resolved = self.resolver.resolve_priority(context_specs, user_id)
            
            return ContextOperationResult(
                success=True,
                message=f"Context '{name}' resolved",
                data={"context": self._spec_to_dict(resolved)}
            )
            
        except Exception as e:
            logger.error(f"Context resolution failed: {e}")
            return ContextOperationResult(
                success=False,
                message="Context resolution failed",
                error_code="RESOLUTION_ERROR"
            )
    
    def _check_team_admin_permission(self, user_id: int, team_id: int) -> bool:
        """Check if user is team admin"""
        # Implementation depends on team management system
        return True  # Placeholder
    
    def _check_org_admin_permission(self, user_id: int) -> bool:
        """Check if user is organization admin"""
        # Implementation depends on organization management system
        return True  # Placeholder
    
    def _context_to_spec(self, context) -> ContextSpec:
        """Convert database context to spec"""
        return ContextSpec(
            id=context.id,
            name=context.name,
            description=context.description,
            scope=ContextScope(context.scope),
            owner_id=context.owner_id,
            team_id=context.team_id,
            organization_id=context.organization_id,
            visibility=context.visibility,
            is_active=context.is_active,
            created_at=context.created_at.isoformat() if context.created_at else None
        )
    
    def _context_to_dict(self, context) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "id": context.id,
            "name": context.name,
            "description": context.description,
            "scope": context.scope,
            "owner_id": context.owner_id,
            "team_id": context.team_id,
            "organization_id": context.organization_id,
            "visibility": context.visibility,
            "is_active": context.is_active,
            "created_at": context.created_at.isoformat() if context.created_at else None
        }
    
    def _spec_to_dict(self, spec: ContextSpec) -> Dict[str, Any]:
        """Convert spec to dictionary"""
        return {
            "id": spec.id,
            "name": spec.name,
            "description": spec.description,
            "scope": spec.scope.value,
            "owner_id": spec.owner_id,
            "team_id": spec.team_id,
            "organization_id": spec.organization_id,
            "visibility": spec.visibility,
            "is_active": spec.is_active,
            "created_at": spec.created_at
        }
    
    def get_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        """Get context by ID"""
        try:
            context = self.db.get_context_by_id(context_id, user_id)
            if not context:
                return ContextOperationResult(
                    success=False,
                    message="Context not found or access denied",
                    error_code="NOT_FOUND"
                )
            
            return ContextOperationResult(
                success=True,
                message="Context retrieved successfully",
                data={"context": self._context_to_dict(context)}
            )
        except Exception as e:
            logger.error(f"Get context failed: {e}")
            return ContextOperationResult(
                success=False,
                message="Failed to retrieve context",
                error_code="INTERNAL_ERROR"
            )
    
    def list_contexts(self, user_id: int, scope: Optional[ContextScope] = None) -> ContextOperationResult:
        """List user-accessible contexts"""
        try:
            contexts = self.db.get_user_contexts(user_id)
            
            # Filter by scope if specified
            if scope:
                contexts = [c for c in contexts if c.get('scope') == scope.value]
            
            context_list = [self._context_dict_to_spec_dict(c) for c in contexts]
            
            return ContextOperationResult(
                success=True,
                message=f"Retrieved {len(context_list)} contexts",
                data={"contexts": context_list}
            )
        except Exception as e:
            logger.error(f"List contexts failed: {e}")
            return ContextOperationResult(
                success=False,
                message="Failed to list contexts",
                error_code="INTERNAL_ERROR"
            )
    
    def _context_dict_to_spec_dict(self, context_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert context dictionary to spec format"""
        return {
            "id": context_dict.get("id"),
            "name": context_dict.get("name"),
            "description": context_dict.get("description"),
            "scope": context_dict.get("scope", "personal"),
            "owner_id": context_dict.get("owner_id"),
            "team_id": context_dict.get("team_id"),
            "organization_id": context_dict.get("organization_id"),
            "visibility": context_dict.get("visibility", "private"),
            "is_active": context_dict.get("is_active", False),
            "created_at": context_dict.get("created_at")
        }
    
    def update_context(self, context_id: int, updates: Dict[str, Any], user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
    
    def delete_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
    
    def share_context(self, context_id: int, permission: ContextPermissionSpec, user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
    
    def transfer_context(self, context_id: int, target_type: str, target_id: int, user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
    
    def activate_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
    
    def deactivate_context(self, context_id: int, user_id: int) -> ContextOperationResult:
        return ContextOperationResult(success=False, message="Not implemented")
