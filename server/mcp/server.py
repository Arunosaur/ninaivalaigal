"""
MCP Server Core for ninaivalaigal
Extracted from monolithic mcp_server.py for better organization

This addresses external code review feedback:
- Break down monolithic files (mcp_server.py 929 lines → focused modules)
- Improve code organization and maintainability
"""

import os
import sys
import jwt
import subprocess
import json

# Add server directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import MCP, fallback to mock if not available
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("e^m")
    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP not available, using mock implementation")
    class MockMCP:
        def __init__(self, name):
            self.name = name
            self.tools = {}
            self.resources = {}
            self.prompts = {}
        
        def tool(self):
            def decorator(func):
                self.tools[func.__name__] = func
                return func
            return decorator
        
        def resource(self, uri):
            def decorator(func):
                self.resources[uri] = func
                return func
            return decorator
        
        def prompt(self):
            def decorator(func):
                self.prompts[func.__name__] = func
                return func
            return decorator
        
        def run(self):
            print(f"Mock MCP server '{self.name}' would run with:")
            print(f"  Tools: {list(self.tools.keys())}")
            print(f"  Resources: {list(self.resources.keys())}")
            print(f"  Prompts: {list(self.prompts.keys())}")
    
    mcp = MockMCP("e^m")
    MCP_AVAILABLE = False

# JWT token handling for user authentication
def get_user_from_jwt():
    """Extract user ID from JWT token with proper verification"""
    token = os.getenv("NINAIVALAIGAL_USER_TOKEN")
    if not token:
        return int(os.getenv("NINAIVALAIGAL_USER_ID", "1"))  # Fallback

    try:
        # Get JWT secret from environment
        jwt_secret = os.getenv("JWT_SECRET", "fallback-secret-key")
        
        # Decode JWT token
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if user_id:
            return int(user_id)
        else:
            print("⚠️ No user_id found in JWT token, using fallback")
            return int(os.getenv("NINAIVALAIGAL_USER_ID", "1"))
            
    except jwt.ExpiredSignatureError:
        print("⚠️ JWT token expired, using fallback user ID")
        return int(os.getenv("NINAIVALAIGAL_USER_ID", "1"))
    except jwt.InvalidTokenError:
        print("⚠️ Invalid JWT token, using fallback user ID")
        return int(os.getenv("NINAIVALAIGAL_USER_ID", "1"))
    except Exception as e:
        print(f"⚠️ Error decoding JWT: {e}, using fallback user ID")
        return int(os.getenv("NINAIVALAIGAL_USER_ID", "1"))

# Default user ID
DEFAULT_USER_ID = get_user_from_jwt()

def get_dynamic_database_url():
    """Get database URL with dynamic container IP resolution"""
    # Check if we have environment override first
    env_db_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_db_url:
        return env_db_url
    
    # Try to get dynamic container IPs (works for both Apple Container CLI and Docker)
    try:
        # First try Apple Container CLI
        container_cmd = "container"
        if subprocess.run(["which", "container"], capture_output=True).returncode != 0:
            # Fallback to Docker if container CLI not available
            container_cmd = "docker"
        
        # Check if we're running in container mode (containers available)
        result = subprocess.run(
            [container_cmd, "ps" if container_cmd == "docker" else "list"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode == 0:
            # Try to get PgBouncer IP first (preferred for connection pooling)
            try:
                pgb_result = subprocess.run(
                    [container_cmd, "inspect", "nv-pgbouncer"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if pgb_result.returncode == 0:
                    pgb_data = json.loads(pgb_result.stdout)
                    if pgb_data and len(pgb_data) > 0:
                        pgb_ip = pgb_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = f"postgresql://nina:change_me_securely@{pgb_ip}:6432/nina"
                        print(f"🔗 MCP using PgBouncer at {pgb_ip}:6432")
                        return db_url
            except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, IndexError):
                pass
            
            # Fallback to direct database connection
            try:
                db_result = subprocess.run(
                    [container_cmd, "inspect", "nv-db"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if db_result.returncode == 0:
                    db_data = json.loads(db_result.stdout)
                    if db_data and len(db_data) > 0:
                        db_ip = db_data[0]["networks"][0]["address"].split("/")[0]
                        db_url = f"postgresql://nina:change_me_securely@{db_ip}:5432/nina"
                        print(f"🔗 MCP using direct DB at {db_ip}:5432")
                        return db_url
            except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, IndexError):
                pass
    
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Final fallback to localhost (for development)
    print("⚠️ MCP falling back to localhost database connection")
    return "postgresql://nina:change_me_securely@localhost:5433/nina"

# Lazy-loaded components to avoid circular imports
_components_cache = None

def get_initialized_components():
    """Get initialized database and other components with lazy loading"""
    global _components_cache
    
    if _components_cache is not None:
        return _components_cache
    
    try:
        from database import DatabaseManager
        
        # Try to load config, fallback to defaults
        try:
            from main import load_config
            config = load_config()
        except ImportError:
            config = {"database_url": "sqlite:///./mem0.db"}
        
        # Initialize database with dynamic URL resolution
        database_url = get_dynamic_database_url()
        db = DatabaseManager(database_url)
        
        # Try to initialize optional components
        spec_context_manager = None
        approval_manager = None
        auto_recorder = None
        
        try:
            from spec_kit import SpecKitContextManager
            spec_context_manager = SpecKitContextManager(db)
        except ImportError:
            print("⚠️ SpecKitContextManager not available")
        
        try:
            from approval_workflow import ApprovalWorkflowManager
            approval_manager = ApprovalWorkflowManager(db)
        except ImportError:
            print("⚠️ ApprovalWorkflowManager not available")
        
        try:
            from auto_recording import get_auto_recorder
            auto_recorder = get_auto_recorder(db)
        except ImportError:
            print("⚠️ AutoRecorder not available")
        
        _components_cache = {
            'config': config,
            'db': db,
            'spec_context_manager': spec_context_manager,
            'approval_manager': approval_manager,
            'auto_recorder': auto_recorder,
            'DEFAULT_USER_ID': DEFAULT_USER_ID
        }
        
        return _components_cache
        
    except ImportError as e:
        print(f"⚠️ Could not initialize components: {e}")
        # Return minimal mock components
        class MockDB:
            def get_memories(self, *args, **kwargs):
                return []
            def get_all_contexts(self, *args, **kwargs):
                return []
            def add_memory(self, *args, **kwargs):
                return 1
        
        _components_cache = {
            'config': {},
            'db': MockDB(),
            'spec_context_manager': None,
            'approval_manager': None,
            'auto_recorder': None,
            'DEFAULT_USER_ID': DEFAULT_USER_ID
        }
        
        return _components_cache
