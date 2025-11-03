package main

import (
	"testing"
	"time"
)

func TestNewLoadTestConfig(t *testing.T) {
	config := NewLoadTestConfig()

	if config == nil {
		t.Fatal("Expected config to be created, got nil")
	}

	// Check default values
	if config.Concurrency <= 0 {
		t.Error("Expected default concurrency to be greater than 0")
	}

	if config.Timeout == 0 {
		t.Error("Expected default timeout to be set")
	}
}

func TestLoadTestConfigDefaults(t *testing.T) {
	config := NewLoadTestConfig()

	// Validate default concurrency is reasonable
	if config.Concurrency < 1 || config.Concurrency > 1000 {
		t.Errorf("Expected default concurrency to be between 1 and 1000, got %d", config.Concurrency)
	}

	// Validate timeout is reasonable
	if config.Timeout < time.Second || config.Timeout > 5*time.Minute {
		t.Errorf("Expected default timeout to be between 1s and 5m, got %v", config.Timeout)
	}
}
