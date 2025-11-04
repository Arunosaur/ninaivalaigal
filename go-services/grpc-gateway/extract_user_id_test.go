package main

import (
	"net/http/httptest"
	"testing"
)

func TestExtractUserIDFromBearerToken(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer test-user-id-123")

	userID := enhanced.extractUserID(req)

	// Should extract user ID from Bearer token
	if userID == "" {
		t.Error("Expected user ID to be extracted from Bearer token")
	}
	if userID != "test-user-id-123" {
		t.Errorf("Expected user ID 'test-user-id-123', got '%s'", userID)
	}
}

func TestExtractUserIDNoAuthHeader(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	// No Authorization header

	userID := enhanced.extractUserID(req)

	// Should return empty string when no auth header
	if userID != "" {
		t.Errorf("Expected empty user ID, got '%s'", userID)
	}
}

func TestExtractUserIDInvalidFormat(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "InvalidFormat token")

	userID := enhanced.extractUserID(req)

	// Should return empty string for invalid format
	if userID != "" {
		t.Errorf("Expected empty user ID for invalid format, got '%s'", userID)
	}
}

func TestExtractUserIDBearerWithoutToken(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Set("Authorization", "Bearer ")

	userID := enhanced.extractUserID(req)

	// Should handle empty token
	if userID != "" {
		t.Errorf("Expected empty user ID for empty token, got '%s'", userID)
	}
}

func TestExtractUserIDMultipleHeaders(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/users/me", nil)
	req.Header.Add("Authorization", "Bearer token1")
	req.Header.Add("Authorization", "Bearer token2")

	userID := enhanced.extractUserID(req)

	// Should extract from first header
	if userID == "" {
		t.Error("Expected user ID to be extracted")
	}
}
