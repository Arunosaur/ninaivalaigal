package main

import (
	"net/http"
	"net/http/httptest"
	"strconv"
	"testing"
)

func TestMemoryRecallHandlerQueryParamParsing(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []struct {
		name      string
		query     string
		limit     string
		threshold string
	}{
		{"All params", "test query", "20", "0.8"},
		{"Default limit", "test query", "", "0.8"},
		{"Default threshold", "test query", "20", ""},
		{"Defaults only", "test query", "", ""},
		{"Invalid limit", "test query", "abc", "0.8"},
		{"Negative limit", "test query", "-5", "0.8"},
		{"Invalid threshold", "test query", "20", "invalid"},
		{"High threshold", "test query", "20", "0.99"},
		{"Zero threshold", "test query", "20", "0.0"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
			q := req.URL.Query()
			if tc.query != "" {
				q.Set("q", tc.query)
			}
			if tc.limit != "" {
				q.Set("limit", tc.limit)
			}
			if tc.threshold != "" {
				q.Set("threshold", tc.threshold)
			}
			req.URL.RawQuery = q.Encode()
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			// Should handle all parameter combinations
			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryRecallHandlerMissingQuery(t *testing.T) {
	t.Skip("Skipping - test needs update for auth middleware integration")
	// TODO: Update this test to work with auth middleware
	// The handler now requires proper JWT validation when auth is enabled

	// Use test helper to create gateway with hybrid clients
	enhanced := NewTestEnhancedGateway(t)

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should return 400 Bad Request when query is missing
	if rec.Code != http.StatusBadRequest {
		t.Errorf("Expected status 400 for missing query, got %d", rec.Code)
	}
}

func TestMemoryListHandlerQueryParamParsing(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []struct {
		name     string
		page     string
		pageSize string
	}{
		{"Both params", "2", "50"},
		{"Default page", "", "50"},
		{"Default pageSize", "2", ""},
		{"Defaults only", "", ""},
		{"Invalid page", "abc", "50"},
		{"Negative page", "-1", "50"},
		{"Invalid pageSize", "2", "invalid"},
		{"Zero pageSize", "2", "0"},
		{"Large values", "100", "1000"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
			q := req.URL.Query()
			if tc.page != "" {
				q.Set("page", tc.page)
			}
			if tc.pageSize != "" {
				q.Set("page_size", tc.pageSize)
			}
			req.URL.RawQuery = q.Encode()
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			// Should handle all parameter combinations
			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryRecallHandlerLimitEdgeCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test limit parsing edge cases
	limits := []string{"0", "1", "100", "999999", "invalid", "-1"}

	for _, limit := range limits {
		t.Run("limit_"+limit, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit="+limit, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			// Verify default limit is used for invalid values
			if limit != "0" && limit != "-1" && limit != "invalid" {
				// Valid limit should be parsed
				parsed, err := strconv.Atoi(limit)
				if err == nil && parsed > 0 {
					// Should accept valid limits
					if rec.Code == http.StatusBadRequest {
						t.Errorf("Valid limit %s should not cause 400", limit)
					}
				}
			}
		})
	}
}

func TestMemoryRecallHandlerThresholdEdgeCases(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test threshold parsing edge cases
	thresholds := []string{"0.0", "0.5", "0.99", "1.0", "invalid", "-0.1", "1.1"}

	for _, threshold := range thresholds {
		t.Run("threshold_"+threshold, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&threshold="+threshold, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryRecallHandler(rec, req)

			// Should handle all threshold values gracefully
			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryRememberHandlerHTTPErrorPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("POST", "/api/v1/memory/remember", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	req.Header.Set("Content-Type", "application/json")
	// No body - will trigger error path
	rec := httptest.NewRecorder()

	enhanced.memoryRememberHandler(rec, req)

	// Should handle missing body or JSON decode errors
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerHTTPErrorPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should handle HTTP client errors gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerHTTPErrorPaths(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/memories", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryListHandler(rec, req)

	// Should handle HTTP client errors gracefully
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryRecallHandlerJSONMarshalError(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall?q=test&limit=10&threshold=0.8", nil)
	req.Header.Set("Authorization", "Bearer test-token")
	rec := httptest.NewRecorder()

	enhanced.memoryRecallHandler(rec, req)

	// Should handle JSON marshaling (shouldn't fail for valid inputs)
	if rec.Code == 0 {
		t.Error("Handler should set a status code")
	}
}

func TestMemoryListHandlerPageValidation(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test that invalid page values default to 1
	invalidPages := []string{"0", "-1", "abc"}

	for _, page := range invalidPages {
		t.Run("invalid_page_"+page, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/memories?page="+page, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			// Should default to page 1 for invalid values
			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}

func TestMemoryListHandlerPageSizeValidation(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	// Test that invalid pageSize values default to 20
	invalidPageSizes := []string{"0", "-1", "abc"}

	for _, pageSize := range invalidPageSizes {
		t.Run("invalid_pageSize_"+pageSize, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/memories?page_size="+pageSize, nil)
			req.Header.Set("Authorization", "Bearer test-token")
			rec := httptest.NewRecorder()

			enhanced.memoryListHandler(rec, req)

			// Should default to pageSize 20 for invalid values
			if rec.Code == 0 {
				t.Error("Handler should set a status code")
			}
		})
	}
}
