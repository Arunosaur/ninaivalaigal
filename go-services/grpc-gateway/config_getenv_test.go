package main

import (
	"os"
	"testing"
)

func TestGetEnv(t *testing.T) {
	// Test getEnv function behavior
	// Save original value
	origValue := os.Getenv("TEST_ENV_VAR")

	// Set test value
	os.Setenv("TEST_ENV_VAR", "test-value")

	// Test that getEnv retrieves value
	value := getEnv("TEST_ENV_VAR", "default")
	if value != "test-value" {
		t.Errorf("Expected 'test-value', got '%s'", value)
	}

	// Test with empty env var (should return default)
	os.Unsetenv("TEST_ENV_VAR")
	value = getEnv("TEST_ENV_VAR", "default-value")
	if value != "default-value" {
		t.Errorf("Expected 'default-value', got '%s'", value)
	}

	// Test with whitespace (should trim)
	os.Setenv("TEST_ENV_VAR", "  test-value  ")
	value = getEnv("TEST_ENV_VAR", "default")
	if value != "test-value" {
		t.Errorf("Expected 'test-value' (trimmed), got '%s'", value)
	}

	// Restore original
	if origValue != "" {
		os.Setenv("TEST_ENV_VAR", origValue)
	} else {
		os.Unsetenv("TEST_ENV_VAR")
	}
}

func TestGetEnvEmptyDefault(t *testing.T) {
	origValue := os.Getenv("NONEXISTENT_VAR")
	os.Unsetenv("NONEXISTENT_VAR")

	value := getEnv("NONEXISTENT_VAR", "")
	if value != "" {
		t.Errorf("Expected empty string, got '%s'", value)
	}

	if origValue != "" {
		os.Setenv("NONEXISTENT_VAR", origValue)
	}
}

func TestGetEnvWhitespaceOnly(t *testing.T) {
	origValue := os.Getenv("TEST_WHITESPACE")
	os.Setenv("TEST_WHITESPACE", "   ")

	value := getEnv("TEST_WHITESPACE", "default")
	if value != "default" {
		t.Errorf("Expected 'default' for whitespace-only value, got '%s'", value)
	}

	if origValue != "" {
		os.Setenv("TEST_WHITESPACE", origValue)
	} else {
		os.Unsetenv("TEST_WHITESPACE")
	}
}

func TestGetEnvTabAndNewline(t *testing.T) {
	origValue := os.Getenv("TEST_TAB_NEWLINE")
	os.Setenv("TEST_TAB_NEWLINE", "\t\nvalue\t\n")

	value := getEnv("TEST_TAB_NEWLINE", "default")
	if value != "value" {
		t.Errorf("Expected 'value' (trimmed), got '%s'", value)
	}

	if origValue != "" {
		os.Setenv("TEST_TAB_NEWLINE", origValue)
	} else {
		os.Unsetenv("TEST_TAB_NEWLINE")
	}
}
