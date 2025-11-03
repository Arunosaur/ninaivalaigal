package main

import (
	"testing"
	"time"
)

func TestGetDefaultProfiles(t *testing.T) {
	profiles := GetDefaultProfiles()

	// Check that default profiles exist
	if len(profiles) == 0 {
		t.Error("Expected at least one default profile, got 0")
	}

	// Check required profiles
	expectedProfiles := []string{"local", "docker", "production"}
	for _, expected := range expectedProfiles {
		if _, exists := profiles[expected]; !exists {
			t.Errorf("Expected profile '%s' not found", expected)
		}
	}

	// Validate local profile
	localProfile := profiles["local"]
	if localProfile.Name != "Local Development" {
		t.Errorf("Expected local profile name 'Local Development', got '%s'", localProfile.Name)
	}

	// Validate profile has services
	if len(localProfile.Services) == 0 {
		t.Error("Expected local profile to have services configured")
	}

	// Validate memory service in local profile
	memoryService, exists := localProfile.Services["memory"]
	if !exists {
		t.Error("Expected memory service in local profile")
	} else {
		if memoryService.URL == "" {
			t.Error("Expected memory service to have URL configured")
		}
		if memoryService.Timeout == 0 {
			t.Error("Expected memory service to have timeout configured")
		}
	}
}

func TestGetMemoryTargets(t *testing.T) {
	targets := GetMemoryTargets()

	if len(targets) == 0 {
		t.Error("Expected memory targets to be non-empty")
	}

	// Check required endpoints
	requiredEndpoints := []string{"remember", "recall", "memories", "search", "health"}
	for _, endpoint := range requiredEndpoints {
		if _, exists := targets[endpoint]; !exists {
			t.Errorf("Expected memory target '%s' not found", endpoint)
		}
	}

	// Validate endpoint paths start with /api
	for endpoint, path := range targets {
		if path[:4] != "/api" {
			t.Errorf("Expected endpoint '%s' path to start with /api, got '%s'", endpoint, path)
		}
	}
}

func TestGetGraphTargets(t *testing.T) {
	targets := GetGraphTargets()

	if len(targets) == 0 {
		t.Error("Expected graph targets to be non-empty")
	}

	// Check required endpoints
	requiredEndpoints := []string{"query", "health", "stats"}
	for _, endpoint := range requiredEndpoints {
		if _, exists := targets[endpoint]; !exists {
			t.Errorf("Expected graph target '%s' not found", endpoint)
		}
	}

	// Validate endpoint paths
	for endpoint, path := range targets {
		if path[:4] != "/api" {
			t.Errorf("Expected endpoint '%s' path to start with /api, got '%s'", endpoint, path)
		}
	}
}

func TestGetCommonQueries(t *testing.T) {
	queries := GetCommonQueries()

	if len(queries) == 0 {
		t.Error("Expected common queries to be non-empty")
	}

	// Check required queries
	requiredQueries := []string{"count-nodes", "count-relations", "node-types"}
	for _, query := range requiredQueries {
		if _, exists := queries[query]; !exists {
			t.Errorf("Expected query '%s' not found", query)
		}
	}

	// Validate queries are non-empty
	for name, query := range queries {
		if query == "" {
			t.Errorf("Expected query '%s' to be non-empty", name)
		}
	}
}

func TestGetLoadTestProfiles(t *testing.T) {
	profiles := GetLoadTestProfiles()

	if len(profiles) == 0 {
		t.Error("Expected load test profiles to be non-empty")
	}

	// Check required profiles
	requiredProfiles := []string{"smoke", "light", "moderate", "heavy"}
	for _, profile := range requiredProfiles {
		if _, exists := profiles[profile]; !exists {
			t.Errorf("Expected load test profile '%s' not found", profile)
		}
	}

	// Validate smoke profile structure
	if smoke, exists := profiles["smoke"].(map[string]interface{}); exists {
		if _, hasConcurrency := smoke["concurrency"]; !hasConcurrency {
			t.Error("Expected smoke profile to have concurrency setting")
		}
		if _, hasRequests := smoke["requests"]; !hasRequests {
			t.Error("Expected smoke profile to have requests setting")
		}
	}
}

func TestServiceConfig(t *testing.T) {
	config := ServiceConfig{
		URL:     "http://localhost:8080",
		Timeout: 30 * time.Second,
		Headers: map[string]string{
			"Content-Type": "application/json",
		},
		Auth: AuthConfig{
			Type:  "bearer",
			Token: "test-token",
		},
	}

	if config.URL == "" {
		t.Error("Expected URL to be set")
	}
	if config.Timeout == 0 {
		t.Error("Expected timeout to be set")
	}
	if len(config.Headers) == 0 {
		t.Error("Expected headers to be set")
	}
	if config.Auth.Type == "" {
		t.Error("Expected auth type to be set")
	}
}

func TestAuthConfig(t *testing.T) {
	authConfig := AuthConfig{
		Type:   "bearer",
		Token:  "test-token",
		Key:    "api-key",
		Secret: "secret-key",
	}

	if authConfig.Type == "" {
		t.Error("Expected auth type to be set")
	}
}

func TestOutputConfig(t *testing.T) {
	outputConfig := OutputConfig{
		Format: "json",
		Colors: true,
		Pager:  false,
	}

	if outputConfig.Format == "" {
		t.Error("Expected output format to be set")
	}
}
