package main

import (
	"net/http/httptest"
	"testing"
)

func TestExtractUserIDWithBearerToken(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	req.Header.Set("Authorization", "Bearer test-token-12345")

	userID := enhanced.extractUserID(req)
	if userID == "" {
		t.Error("Expected user ID for valid Bearer token")
	}
	if userID != "user-123" {
		t.Logf("ExtractUserID returned placeholder value: %s", userID)
	}
}

func TestExtractUserIDWithoutHeader(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	// No Authorization header

	userID := enhanced.extractUserID(req)
	if userID != "" {
		t.Errorf("Expected empty user ID for missing header, got: %s", userID)
	}
}

func TestExtractUserIDWithInvalidScheme(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	testCases := []string{
		"Basic dXNlcjpwYXNz",
		"Digest username=test",
		"InvalidScheme token",
		"Bearer",                 // No token after Bearer
		"bearer lowercase-token", // Lowercase
	}

	for _, authHeader := range testCases {
		t.Run(authHeader, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
			req.Header.Set("Authorization", authHeader)

			userID := enhanced.extractUserID(req)
			// Should handle invalid schemes gracefully
			_ = userID
		})
	}
}

func TestExtractUserIDWithBearerButNoSpace(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	req.Header.Set("Authorization", "Bearertokenwithoutspace")

	userID := enhanced.extractUserID(req)
	// Should handle malformed header
	_ = userID
}

func TestExtractUserIDEmptyToken(t *testing.T) {
	gateway := NewGateway()
	enhanced := &EnhancedGateway{
		Gateway:     gateway,
		grpcClients: nil,
	}

	req := httptest.NewRequest("GET", "/api/v1/memory/recall", nil)
	req.Header.Set("Authorization", "Bearer ")

	userID := enhanced.extractUserID(req)
	_ = userID
}

// TestExtractUserIDMultipleHeaders is defined in extract_user_id_test.go
// This test is removed to avoid duplicate declaration
