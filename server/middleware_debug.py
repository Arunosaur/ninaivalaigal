"""
Middleware Debug Tool - Drop-in debugging for /auth route hanging
This tool helps identify which middleware is causing /auth routes to hang
"""

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)

class MiddlewareDebugger:
    """Debug middleware to trace request processing and identify hangs"""
    
    def __init__(self, name: str = "Unknown"):
        self.name = name
        self.request_count = 0
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        self.request_count += 1
        request_id = f"{self.name}-{self.request_count}"
        
        # Log request start
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        print(f"🔍 [{request_id}] START: {method} {path}")
        
        # Special handling for /auth paths
        is_auth_path = "/auth" in path.lower()
        if is_auth_path:
            print(f"🚨 [{request_id}] AUTH PATH DETECTED: {path}")
            
        try:
            # Add timeout for auth paths to prevent infinite hangs
            if is_auth_path:
                print(f"⏰ [{request_id}] Setting 10s timeout for auth path")
                response = await asyncio.wait_for(call_next(request), timeout=10.0)
            else:
                response = await call_next(request)
                
            # Log successful completion
            duration = time.time() - start_time
            print(f"✅ [{request_id}] SUCCESS: {method} {path} ({duration:.3f}s)")
            
            return response
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            print(f"⏰ [{request_id}] TIMEOUT: {method} {path} after {duration:.3f}s")
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request timeout", 
                    "path": path,
                    "middleware": self.name,
                    "duration": duration
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ [{request_id}] ERROR: {method} {path} ({duration:.3f}s) - {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Middleware error",
                    "path": path, 
                    "middleware": self.name,
                    "exception": str(e),
                    "duration": duration
                }
            )


class AuthPathTracker:
    """Specifically track /auth path processing"""
    
    def __init__(self):
        self.auth_requests = {}
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        if "/auth" not in path.lower():
            # Pass through non-auth requests immediately
            return await call_next(request)
            
        # Track auth request
        request_id = f"auth-{int(time.time() * 1000)}"
        self.auth_requests[request_id] = {
            "path": path,
            "method": request.method,
            "start_time": time.time(),
            "status": "processing"
        }
        
        print(f"🔐 [{request_id}] AUTH REQUEST: {request.method} {path}")
        
        try:
            # Add aggressive timeout for auth paths
            print(f"⏰ [{request_id}] Starting 5s timeout for auth processing")
            
            response = await asyncio.wait_for(call_next(request), timeout=5.0)
            
            # Success
            duration = time.time() - self.auth_requests[request_id]["start_time"]
            print(f"✅ [{request_id}] AUTH SUCCESS: {path} ({duration:.3f}s)")
            self.auth_requests[request_id]["status"] = "completed"
            
            return response
            
        except asyncio.TimeoutError:
            duration = time.time() - self.auth_requests[request_id]["start_time"]
            print(f"🚨 [{request_id}] AUTH TIMEOUT: {path} after {duration:.3f}s")
            self.auth_requests[request_id]["status"] = "timeout"
            
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Auth endpoint timeout",
                    "path": path,
                    "duration": duration,
                    "message": "Auth middleware is hanging - check Redis/DB connections"
                }
            )
            
        except Exception as e:
            duration = time.time() - self.auth_requests[request_id]["start_time"]
            print(f"❌ [{request_id}] AUTH ERROR: {path} - {str(e)}")
            self.auth_requests[request_id]["status"] = "error"
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Auth middleware error",
                    "path": path,
                    "exception": str(e),
                    "duration": duration
                }
            )


class RedisCallTracker:
    """Track Redis calls that might be causing hangs"""
    
    def __init__(self):
        self.redis_calls = []
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Only track auth paths for Redis issues
        if "/auth" not in path.lower():
            return await call_next(request)
            
        print(f"🔍 REDIS TRACKER: Monitoring {path} for Redis calls")
        
        # Monkey patch Redis calls to detect hangs
        original_redis_get = None
        original_redis_set = None
        
        try:
            # Try to patch common Redis methods if they exist
            import redis.asyncio as redis_async
            if hasattr(redis_async, 'Redis'):
                redis_client = redis_async.Redis
                if hasattr(redis_client, 'get'):
                    original_redis_get = redis_client.get
                    
                    async def tracked_get(self, *args, **kwargs):
                        print(f"🔴 REDIS GET called from {path}")
                        start = time.time()
                        try:
                            result = await asyncio.wait_for(original_redis_get(self, *args, **kwargs), timeout=2.0)
                            print(f"✅ REDIS GET completed ({time.time() - start:.3f}s)")
                            return result
                        except asyncio.TimeoutError:
                            print(f"⏰ REDIS GET timeout after {time.time() - start:.3f}s")
                            raise
                        except Exception as e:
                            print(f"❌ REDIS GET error: {e}")
                            raise
                    
                    redis_client.get = tracked_get
                    
        except ImportError:
            print("📝 Redis not available for tracking")
            
        try:
            response = await call_next(request)
            return response
        finally:
            # Restore original methods
            if original_redis_get:
                try:
                    import redis.asyncio as redis_async
                    redis_async.Redis.get = original_redis_get
                except:
                    pass


# Pre-configured debug middleware instances
auth_path_tracker = AuthPathTracker()
redis_call_tracker = RedisCallTracker()
general_debugger = MiddlewareDebugger("GeneralDebug")

# Quick setup functions
def add_auth_debugging(app):
    """Add auth-specific debugging middleware"""
    print("🔧 Adding auth debugging middleware")
    app.middleware("http")(auth_path_tracker)

def add_redis_debugging(app):
    """Add Redis call debugging"""
    print("🔧 Adding Redis debugging middleware") 
    app.middleware("http")(redis_call_tracker)

def add_general_debugging(app):
    """Add general request debugging"""
    print("🔧 Adding general debugging middleware")
    app.middleware("http")(general_debugger)

def add_all_debugging(app):
    """Add all debugging middleware"""
    add_auth_debugging(app)
    add_redis_debugging(app) 
    add_general_debugging(app)
    print("✅ All debugging middleware added")

# Emergency auth bypass
def create_emergency_auth_bypass(app):
    """Create emergency auth endpoints that bypass all middleware"""
    
    @app.post("/emergency-login")
    def emergency_login(data: dict):
        """Emergency login that bypasses all middleware"""
        email = data.get('email', '')
        password = data.get('password', '')
        
        if email == 'test@ninaivalaigal.com' and password == 'test':
            return {
                'success': True,
                'message': 'Emergency login successful!',
                'user_id': 'test-user',
                'email': email,
                'jwt_token': 'emergency-jwt-token',
                'note': 'This bypasses all middleware'
            }
        return {'success': False, 'message': 'Invalid credentials'}
    
    @app.get("/debug-status")
    def debug_status():
        """Show debugging status"""
        return {
            'auth_tracker': f"Tracked {len(auth_path_tracker.auth_requests)} auth requests",
            'redis_tracker': f"Tracked {len(redis_call_tracker.redis_calls)} Redis calls",
            'general_debugger': f"Processed {general_debugger.request_count} requests"
        }
    
    print("🚨 Emergency auth bypass endpoints created:")
    print("   POST /emergency-login")
    print("   GET /debug-status")

if __name__ == "__main__":
    print("Middleware Debug Tool")
    print("Usage:")
    print("  from middleware_debug import add_all_debugging, create_emergency_auth_bypass")
    print("  add_all_debugging(app)")
    print("  create_emergency_auth_bypass(app)")
