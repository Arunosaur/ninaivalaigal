package main

import (
	"testing"
	"time"
)

// Initialize global config for tests
func init() {
	if config == nil {
		config = NewLoadTestConfig()
	}
}

func TestCreateHTTPCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createHTTPCommand()
	if cmd == nil {
		t.Fatal("createHTTPCommand() should not return nil")
	}
}

func TestCreateGRPCCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createGRPCCommand()
	if cmd == nil {
		t.Fatal("createGRPCCommand() should not return nil")
	}
}

func TestCreateWebSocketCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createWebSocketCommand()
	if cmd == nil {
		t.Fatal("createWebSocketCommand() should not return nil")
	}
}

func TestCreateScenarioCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createScenarioCommand()
	if cmd == nil {
		t.Fatal("createScenarioCommand() should not return nil")
	}
}

func TestCreateMetricsCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createMetricsCommand()
	if cmd == nil {
		t.Fatal("createMetricsCommand() should not return nil")
	}
}

func TestCreateServerCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createServerCommand()
	if cmd == nil {
		t.Fatal("createServerCommand() should not return nil")
	}
}

func TestCreateValidateCommand(t *testing.T) {
	config = NewLoadTestConfig()
	defer func() { config = nil }()

	cmd := createValidateCommand()
	if cmd == nil {
		t.Fatal("createValidateCommand() should not return nil")
	}
}

func TestValidateHTTPConfig(t *testing.T) {
	validConfig := &LoadTestConfig{
		URL:           "http://localhost:8080",
		Method:        "GET",
		Concurrency:   1,
		TotalRequests: 1,
		Timeout:       5 * time.Second,
	}

	err := validateHTTPConfig(validConfig)
	if err != nil {
		t.Errorf("validateHTTPConfig() should not error with valid config, got: %v", err)
	}

	invalidConfig := &LoadTestConfig{
		URL:           "",
		Concurrency:   0,
		TotalRequests: 0,
	}

	err = validateHTTPConfig(invalidConfig)
	if err == nil {
		t.Error("validateHTTPConfig() should error with invalid config")
	}
}

func TestValidateGRPCConfig(t *testing.T) {
	validConfig := &LoadTestConfig{
		URL:           "localhost:50051",
		ProtoFile:     "memory.proto",
		GRPCMethod:    "HealthCheck",
		Concurrency:   1,
		TotalRequests: 1,
		Timeout:       5 * time.Second,
	}

	err := validateGRPCConfig(validConfig)
	if err != nil {
		t.Errorf("validateGRPCConfig() should not error with valid config, got: %v", err)
	}

	invalidConfig := &LoadTestConfig{
		URL: "",
	}

	err = validateGRPCConfig(invalidConfig)
	if err == nil {
		t.Error("validateGRPCConfig() should error with invalid config")
	}
}
