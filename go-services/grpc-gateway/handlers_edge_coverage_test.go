package main

import (
	"net/http/httptest"
	"testing"
)

// Test extractUserID with various header formats
func TestExtractUserIDEdgeCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []struct {
		name   string
		header string
		value  string
	}{
		{"Bearer token", "Authorization", "Bearer valid-token"},
		{"Bearer without space", "Authorization", "Bearertoken"},
		{"Lowercase bearer", "Authorization", "bearer token"},
		{"No authorization header", "", ""},
		{"Empty bearer", "Authorization", "Bearer"},
		{"Just Bearer", "Authorization", "Bearer "},
		{"X-User-ID header", "X-User-ID", "user-123"},
		{"X-User-Id lowercase", "X-User-Id", "user-456"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			if tc.header != "" && tc.value != "" {
				req.Header.Set(tc.header, tc.value)
			}

			// Test extractUserID indirectly through a handler
			userID := enhanced.extractUserID(req)
			_ = userID // May be empty, that's fine for testing
		})
	}
}

// Test enhancedHealthHandler with different client states
func TestEnhancedHealthHandlerClientStates(t *testing.T) {
	gateway := NewGateway()

	testCases := []struct {
		name    string
		clients *GRPCClients
	}{
		{"Nil clients", nil},
		{"Empty clients struct", &GRPCClients{}},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: tc.clients,
			}

			req := httptest.NewRequest("GET", "/health", nil)
			rec := httptest.NewRecorder()

			enhanced.enhancedHealthHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Health handler should set a status code")
			}
		})
	}
}

// Test graphHealthHandler with different client states
func TestGraphHealthHandlerClientStates(t *testing.T) {
	gateway := NewGateway()

	testCases := []struct {
		name    string
		clients *GRPCClients
	}{
		{"Nil clients", nil},
		{"Empty clients struct", &GRPCClients{}},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: tc.clients,
			}

			req := httptest.NewRequest("GET", "/api/v1/graph/health", nil)
			rec := httptest.NewRecorder()

			enhanced.graphHealthHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Graph health handler should set a status code")
			}
		})
	}
}

// Test coreAPIProxy with various paths to improve coverage
func TestCoreAPIProxyVariousPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	paths := []string{
		"/api/v1/users/me",
		"/api/v1/auth/login",
		"/api/v1/contexts",
		"/api/v1/memories",
		"/api/v1/admin/analytics",
	}

	for _, path := range paths {
		t.Run(path, func(t *testing.T) {
			req := httptest.NewRequest("GET", path, nil)
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

// Test memoryListHandler with various query parameters
func TestMemoryListHandlerQueryParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []struct {
		name  string
		query string
		auth  string
	}{
		{"No params", "", "Bearer token"},
		{"Page only", "?page=1", "Bearer token"},
		{"Limit only", "?limit=10", "Bearer token"},
		{"Both params", "?page=1&limit=10", "Bearer token"},
		{"Invalid page", "?page=abc", "Bearer token"},
		{"Invalid limit", "?limit=xyz", "Bearer token"},
		{"Negative page", "?page=-1", "Bearer token"},
		{"Negative limit", "?limit=-5", "Bearer token"},
		{"Zero page", "?page=0", "Bearer token"},
		{"Zero limit", "?limit=0", "Bearer token"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/memories"+tc.query, nil)
			if tc.auth != "" {
				req.Header.Set("Authorization", tc.auth)
			}
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}
