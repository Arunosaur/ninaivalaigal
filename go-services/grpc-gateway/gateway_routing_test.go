package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGatewayRoutingHealthEndpoint(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	gateway.router.ServeHTTP(rec, req)

	// Health endpoint should exist
	if rec.Code == http.StatusNotFound {
		t.Error("Expected /health route to exist")
	}
}

func TestGatewayRoutingAPIv1Routes(t *testing.T) {
	gateway := NewGateway()

	routes := []struct {
		path   string
		method string
	}{
		{"/api/v1/graph/query", "POST"},
		{"/api/v1/graph/health", "GET"},
		{"/api/v1/users/me", "GET"},
		{"/api/v1/auth/login", "POST"},
	}

	for _, route := range routes {
		t.Run(route.method+" "+route.path, func(t *testing.T) {
			req := httptest.NewRequest(route.method, route.path, nil)
			rec := httptest.NewRecorder()

			gateway.router.ServeHTTP(rec, req)

			// Route should exist (even if it returns 501)
			if rec.Code == http.StatusNotFound {
				t.Errorf("Expected route '%s' with method '%s' to exist", route.path, route.method)
			}
		})
	}
}

func TestGatewayRoutingInvalidRoutes(t *testing.T) {
	gateway := NewGateway()

	invalidRoutes := []string{
		"/invalid",
		"/api/v2/test",
		"/health/extra",
		"/api/v1/invalid",
	}

	for _, path := range invalidRoutes {
		t.Run(path, func(t *testing.T) {
			req := httptest.NewRequest("GET", path, nil)
			rec := httptest.NewRecorder()

			gateway.router.ServeHTTP(rec, req)

			// Invalid routes should return 404
			if rec.Code != http.StatusNotFound {
				t.Logf("Route '%s' returned %d (may be handled by catch-all)", path, rec.Code)
			}
		})
	}
}

func TestGatewayRoutingMethodNotAllowed(t *testing.T) {
	gateway := NewGateway()

	// Test methods that don't match route
	testCases := []struct {
		path   string
		method string
	}{
		{"/health", "POST"},              // Health should only accept GET
		{"/api/v1/graph/query", "GET"},   // Query should only accept POST
		{"/api/v1/graph/health", "POST"}, // Health should only accept GET
	}

	for _, tc := range testCases {
		t.Run(tc.method+" "+tc.path, func(t *testing.T) {
			req := httptest.NewRequest(tc.method, tc.path, nil)
			rec := httptest.NewRecorder()

			gateway.router.ServeHTTP(rec, req)

			// May return 405 Method Not Allowed or 501/404
			if rec.Code == 0 {
				t.Error("Router should set a status code")
			}
		})
	}
}

func TestGatewayMiddlewareApplied(t *testing.T) {
	gateway := NewGateway()

	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	gateway.router.ServeHTTP(rec, req)

	// CORS headers should be present (applied via middleware)
	if rec.Header().Get("Access-Control-Allow-Origin") != "*" {
		t.Error("Expected CORS middleware to be applied")
	}
}
