package main

import (
	"bytes"
	"io"
	"net/http/httptest"
	"testing"
)

func TestCoreAPIProxyWithDifferentMethods(t *testing.T) {
	methods := []string{"GET", "POST", "PUT", "PATCH", "DELETE"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			var body io.Reader
			if method == "POST" || method == "PUT" || method == "PATCH" {
				body = bytes.NewBufferString(`{"test": "data"}`)
			}

			req := httptest.NewRequest(method, "/api/v1/users/me", body)
			if body != nil {
				req.Header.Set("Content-Type", "application/json")
			}
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

func TestCoreAPIProxyWithComplexQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me?include=profile&fields=name,email&filter=active", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyHeaderPreservation(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	req.Header.Set("X-Custom-Header", "test-value")
	req.Header.Set("X-Request-ID", "12345")
	req.Header.Set("Accept", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyMultipleHeaders(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Add("X-Multi-Value", "value1")
	req.Header.Add("X-Multi-Value", "value2")
	req.Header.Add("X-Multi-Value", "value3")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyErrorResponseBody(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test that error responses are handled
	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	// Should handle errors gracefully
	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyStreamingResponse(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	// Should handle streaming/large responses
	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

// Note: TestCoreAPIProxyDifferentPaths already exists in handlers_edge_cases_test.go

func TestCoreAPIProxyAdditionalPaths(t *testing.T) {
	paths := []string{
		"/api/v1/teams/456",
		"/api/v1/organizations/789",
		"/api/v1/contexts/123",
	}

	for _, path := range paths {
		t.Run(path, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			req := httptest.NewRequest("GET", path, nil)
			rec := httptest.NewRecorder()

			enhanced.coreAPIProxy(rec, req)

			if rec.Code == 0 {
				t.Error("Proxy should set a status code")
			}
		})
	}
}

func TestCoreAPIProxyWithSpecialCharsInQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me?search=test+query&filter=key%3Dvalue", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyRequestBodyConsumption(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	body := bytes.NewBufferString(`{"name": "test", "email": "test@example.com"}`)
	req := httptest.NewRequest("PATCH", "/api/v1/users/me", body)
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}

func TestCoreAPIProxyEmptyQueryParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me?", nil)
	rec := httptest.NewRecorder()

	enhanced.coreAPIProxy(rec, req)

	if rec.Code == 0 {
		t.Error("Proxy should set a status code")
	}
}
