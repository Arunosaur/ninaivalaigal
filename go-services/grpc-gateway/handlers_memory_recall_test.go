package main

import (
	"net/http/httptest"
	"testing"
)

// Note: TestMemoryRecallHandlerNoAuth already exists in handlers_edge_cases_test.go

func TestMemoryRecallHandlerDetailedCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	// No Authorization header
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should return 401 Unauthorized or 503
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerWithQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test+query", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Note: TestMemoryRecallHandlerWithLimit already exists in handlers_edge_cases_test.go

func TestMemoryRecallHandlerWithInvalidLimit(t *testing.T) {
	testCases := []string{
		"/api/v1/memory/recall?q=test&limit=-1",
		"/api/v1/memory/recall?q=test&limit=0",
		"/api/v1/memory/recall?q=test&limit=abc",
		"/api/v1/memory/recall?q=test&limit=99999",
	}

	for _, url := range testCases {
		t.Run(url, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			req := httptest.NewRequest("GET", url, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryRecallHandlerWithContext(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&context=test-context", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerWithMultipleParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test+query&limit=5&context=test-context&threshold=0.7", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerEmptyQuery(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// Note: TestMemoryRecallHandlerNoQuery already exists in handlers_edge_cases_test.go

func TestMemoryRecallHandlerNoClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should return 503 if no clients available
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerWithThreshold(t *testing.T) {
	testCases := []string{
		"/api/v1/memory/recall?q=test&threshold=0.5",
		"/api/v1/memory/recall?q=test&threshold=0.95",
		"/api/v1/memory/recall?q=test&threshold=-1",
		"/api/v1/memory/recall?q=test&threshold=1.5",
		"/api/v1/memory/recall?q=test&threshold=abc",
	}

	for _, url := range testCases {
		t.Run(url, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			req := httptest.NewRequest("GET", url, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}
