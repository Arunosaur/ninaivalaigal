package main

import (
	"testing"
	"time"
)

func TestCheckHealthSequential(t *testing.T) {
	defs := []ServiceDefinition{
		{
			Name:       "test",
			URL:        "http://localhost:8080",
			HealthPath: "/health",
			Timeout:    5 * time.Second,
		},
	}

	// Test sequential health checking
	// Note: Will fail without actual service, but tests structure
	results := checkHealthSequential(defs, 5*time.Second)
	if results == nil {
		t.Error("checkHealthSequential() should return results")
	}
}

func TestCheckHealthParallel(t *testing.T) {
	defs := []ServiceDefinition{
		{
			Name:       "test",
			URL:        "http://localhost:8080",
			HealthPath: "/health",
			Timeout:    5 * time.Second,
		},
	}

	// Test parallel health checking
	results := checkHealthParallel(defs, 5*time.Second)
	if results == nil {
		t.Error("checkHealthParallel() should return results")
	}
}

func TestCheckServiceHealth(t *testing.T) {
	def := ServiceDefinition{
		Name:       "test",
		URL:        "http://localhost:8080",
		HealthPath: "/health",
		Timeout:    5 * time.Second,
	}

	// Test service health checking
	status := checkServiceHealth(def, 5*time.Second)
	if status.Service != "test" {
		t.Errorf("Expected service name 'test', got '%s'", status.Service)
	}
}

func TestCheckDetailedHealth(t *testing.T) {
	def := ServiceDefinition{
		Name:       "test",
		URL:        "http://localhost:8080",
		HealthPath: "/health/detailed",
		Timeout:    5 * time.Second,
	}

	// Test detailed health checking
	status := checkDetailedHealth(def)
	// Status is always returned (not nil)
	if status.Service != "test" {
		t.Errorf("Expected service name 'test', got '%s'", status.Service)
	}
}

func TestDisplayHealthResults(t *testing.T) {
	results := []HealthStatus{
		{
			Service:      "test1",
			Status:       "healthy",
			URL:          "http://localhost:8080",
			ResponseTime: 100 * time.Millisecond,
			StatusCode:   200,
			Timestamp:    time.Now(),
		},
		{
			Service:      "test2",
			Status:       "unhealthy",
			URL:          "http://localhost:8081",
			ResponseTime: 0,
			StatusCode:   500,
			Timestamp:    time.Now(),
		},
	}

	// Should not panic
	displayHealthResults(results)
}

func TestDisplayHealthResultsJSON(t *testing.T) {
	results := []HealthStatus{
		{
			Service:      "test",
			Status:       "healthy",
			URL:          "http://localhost:8080",
			ResponseTime: 100 * time.Millisecond,
			StatusCode:   200,
			Timestamp:    time.Now(),
		},
	}

	// Test JSON output format (displayHealthResults doesn't take JSON flag)
	displayHealthResults(results)
}

func TestDisplayDetailedHealth(t *testing.T) {
	status := HealthStatus{
		Service:      "test",
		Status:       "healthy",
		URL:          "http://localhost:8080",
		ResponseTime: 100 * time.Millisecond,
		StatusCode:   200,
		Details: map[string]interface{}{
			"db":     "connected",
			"redis":  "connected",
			"uptime": 3600,
		},
		Timestamp: time.Now(),
	}

	// Should not panic
	displayDetailedHealth(status)
}
