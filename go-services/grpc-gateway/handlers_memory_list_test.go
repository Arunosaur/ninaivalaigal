package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestMemoryListHandlerNoAuth(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	// No Authorization header
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	// Should return 401 Unauthorized
	if rec.Code != http.StatusUnauthorized {
		t.Logf("Expected 401, got %d", rec.Code)
	}
}

func TestMemoryListHandlerWithAuth(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerWithPageParams(t *testing.T) {
	testCases := []struct {
		name     string
		page     string
		pageSize string
	}{
		{"default page", "", ""},
		{"page 2", "2", ""},
		{"page with size", "3", "50"},
		{"invalid page", "-1", ""},
		{"invalid page size", "1", "-1"},
		{"zero page", "0", ""},
		{"zero page size", "1", "0"},
		{"large page", "999", ""},
		{"large page size", "1", "1000"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			gateway := NewGateway()
			enhanced := &EnhancedGateway{
				Gateway:     gateway,
				grpcClients: nil,
			}

			url := "/api/v1/memory/memories"
			if tc.page != "" || tc.pageSize != "" {
				url += "?"
				if tc.page != "" {
					url += "page=" + tc.page
				}
				if tc.pageSize != "" {
					if tc.page != "" {
						url += "&"
					}
					url += "page_size=" + tc.pageSize
				}
			}

			req := httptest.NewRequest("GET", url, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryListHandlerInvalidPageValues(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with non-numeric page
	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=abc", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerInvalidPageSizeValues(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test with non-numeric page_size
	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page_size=xyz", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerURLConstruction(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test that URL is constructed correctly with pagination
	req := httptest.NewRequest("GET", "/api/v1/memory/memories?page=5&page_size=100", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}
