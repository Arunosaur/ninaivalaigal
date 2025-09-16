"""
Security Headers Middleware

Implements HTTP security headers for FastAPI applications.
"""

import os
from typing import Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all HTTP responses"""
    
    def __init__(self, app, custom_headers: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.headers = self._get_default_headers()
        
        # Override with custom headers if provided
        if custom_headers:
            self.headers.update(custom_headers)
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default security headers with environment variable overrides"""
        
        # Content Security Policy
        csp_policy = os.getenv(
            'CSP_POLICY', 
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self'"
        )
        
        # HSTS max age
        hsts_max_age = os.getenv('HSTS_MAX_AGE', '63072000')  # 2 years
        
        return {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # XSS protection (legacy but still useful)
            'X-XSS-Protection': '1; mode=block',
            
            # HSTS (HTTP Strict Transport Security)
            'Strict-Transport-Security': f'max-age={hsts_max_age}; includeSubDomains; preload',
            
            # Content Security Policy
            'Content-Security-Policy': csp_policy,
            
            # Referrer Policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions Policy (formerly Feature Policy)
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
            
            # Cross-Origin policies
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
            
            # Server identification
            'Server': 'Ninaivalaigal/1.0',
            
            # Cache control for sensitive endpoints
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        for header_name, header_value in self.headers.items():
            # Skip cache control headers for static assets
            if self._is_static_asset(request.url.path) and header_name in ['Cache-Control', 'Pragma', 'Expires']:
                continue
            
            response.headers[header_name] = header_value
        
        # Add custom headers based on endpoint
        self._add_endpoint_specific_headers(request, response)
        
        return response
    
    def _is_static_asset(self, path: str) -> bool:
        """Check if the request is for a static asset"""
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf']
        return any(path.lower().endswith(ext) for ext in static_extensions)
    
    def _add_endpoint_specific_headers(self, request: Request, response: Response):
        """Add headers specific to certain endpoints"""
        path = request.url.path
        
        # Extra security for authentication endpoints
        if path.startswith('/auth/'):
            response.headers['X-Robots-Tag'] = 'noindex, nofollow, nosnippet, noarchive'
            
        # API endpoints should not be cached
        if path.startswith('/api/') or path.startswith('/rbac/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
            
        # Admin endpoints get extra protection
        if path.startswith('/admin/'):
            response.headers['X-Robots-Tag'] = 'noindex, nofollow, nosnippet, noarchive'
            response.headers['X-Frame-Options'] = 'DENY'
            
        # Memory endpoints (sensitive data)
        if path.startswith('/memory') or path.startswith('/contexts'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'


class DevelopmentSecurityHeaders(SecurityHeadersMiddleware):
    """Relaxed security headers for development environment"""
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get development-friendly security headers"""
        headers = super()._get_default_headers()
        
        # Relax CSP for development
        headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data: https: http:; connect-src 'self' ws: wss: http: https:"
        
        # Remove HSTS in development
        if 'Strict-Transport-Security' in headers:
            del headers['Strict-Transport-Security']
        
        # Relax cross-origin policies for development
        headers['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
        headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
        
        return headers


def get_security_headers_middleware(development_mode: bool = False):
    """
    Factory function to get appropriate security headers middleware.
    
    Args:
        development_mode: Whether to use development-friendly headers
        
    Returns:
        SecurityHeadersMiddleware instance
    """
    if development_mode or os.getenv('ENVIRONMENT', 'production').lower() == 'development':
        return DevelopmentSecurityHeaders
    else:
        return SecurityHeadersMiddleware
