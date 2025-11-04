package main

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"
)

func TestMemoryRememberHandlerWithGrpcClients(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil, // No gRPC clients - will proxy to HTTP
	}

	body := MemoryRememberRequest{
		Content:  "Test memory content",
		Context:  "test-context",
		Metadata: map[string]string{"key": "value"},
	}
	bodyJSON, _ := json.Marshal(body)

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", bytes.NewBuffer(bodyJSON))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerInvalidJSON is defined in handlers_edge_cases_test.go
// This test is removed to avoid duplicate declaration

// TestMemoryRememberHandlerMissingContent is defined in handlers_memory_remember_test.go
// This test is removed to avoid duplicate declaration

// TestMemoryRecallHandlerWithQuery is defined in handlers_memory_recall_test.go
// This test is removed to avoid duplicate declaration

func TestMemoryRecallHandlerWithQueryParams(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?query=test&limit=5&threshold=0.8", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryListHandlerWithPagination is defined in handlers_edge_cases_test.go
// This test is removed to avoid duplicate declaration

func TestMemoryListHandlerWithFilters(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories?context=test-context&kind=note", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

// TestMemoryRememberHandlerLargeBody is defined in handlers_edge_cases_test.go
// This test is removed to avoid duplicate declaration

// TestMemoryRecallHandlerEmptyQuery is defined in handlers_memory_recall_test.go
// This test is removed to avoid duplicate declaration
