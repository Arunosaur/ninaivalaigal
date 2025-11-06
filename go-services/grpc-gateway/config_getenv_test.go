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
	if err := os.Setenv("TEST_ENV_VAR", "test-value"); err != nil {
		t.Fatalf("Failed to set env var: %v", err)
	}

	// Test that getEnv retrieves value
	value := getEnv("TEST_ENV_VAR", "default")
	if value != "test-value" {
		t.Errorf("Expected 'test-value', got '%s'", value)
	}

	// Test with empty env var (should return default)
	if err := os.Unsetenv("TEST_ENV_VAR"); err != nil {
		t.Fatalf("Failed to unset env var: %v", err)
	}
	value = getEnv("TEST_ENV_VAR", "default-value")
	if value != "default-value" {
		t.Errorf("Expected 'default-value', got '%s'", value)
	}

	// Test with whitespace (should trim)
	if err := os.Setenv("TEST_ENV_VAR", "  test-value  "); err != nil {
		t.Fatalf("Failed to set env var: %v", err)
	}
	value = getEnv("TEST_ENV_VAR", "default")
	if value != "test-value" {
		t.Errorf("Expected 'test-value' (trimmed), got '%s'", value)
	}

	// Restore original
	if origValue != "" {
		if err := os.Setenv("TEST_ENV_VAR", origValue); err != nil {
			t.Fatalf("Failed to restore env var: %v", err)
		}
	} else {
		if err := os.Unsetenv("TEST_ENV_VAR"); err != nil {
			t.Fatalf("Failed to unset env var: %v", err)
		}
	}
}

func TestGetEnvEmptyDefault(t *testing.T) {
	origValue := os.Getenv("NONEXISTENT_VAR")
	if err := os.Unsetenv("NONEXISTENT_VAR"); err != nil {
		t.Fatalf("Failed to unset env var: %v", err)
	}

	value := getEnv("NONEXISTENT_VAR", "")
	if value != "" {
		t.Errorf("Expected empty string, got '%s'", value)
	}

	if origValue != "" {
		if err := os.Setenv("NONEXISTENT_VAR", origValue); err != nil {
			t.Fatalf("Failed to restore env var: %v", err)
		}
	}
}

func TestGetEnvWhitespaceOnly(t *testing.T) {
	origValue := os.Getenv("TEST_WHITESPACE")
	if err := os.Setenv("TEST_WHITESPACE", "   "); err != nil {
		t.Fatalf("Failed to set env var: %v", err)
	}

	value := getEnv("TEST_WHITESPACE", "default")
	if value != "default" {
		t.Errorf("Expected 'default' for whitespace-only value, got '%s'", value)
	}

	if origValue != "" {
		if err := os.Setenv("TEST_WHITESPACE", origValue); err != nil {
			t.Fatalf("Failed to restore env var: %v", err)
		}
	} else {
		if err := os.Unsetenv("TEST_WHITESPACE"); err != nil {
			t.Fatalf("Failed to unset env var: %v", err)
		}
	}
}

func TestGetEnvTabAndNewline(t *testing.T) {
	origValue := os.Getenv("TEST_TAB_NEWLINE")
	if err := os.Setenv("TEST_TAB_NEWLINE", "\t\nvalue\t\n"); err != nil {
		t.Fatalf("Failed to set env var: %v", err)
	}

	value := getEnv("TEST_TAB_NEWLINE", "default")
	if value != "value" {
		t.Errorf("Expected 'value' (trimmed), got '%s'", value)
	}

	if origValue != "" {
		if err := os.Setenv("TEST_TAB_NEWLINE", origValue); err != nil {
			t.Fatalf("Failed to restore env var: %v", err)
		}
	} else {
		if err := os.Unsetenv("TEST_TAB_NEWLINE"); err != nil {
			t.Fatalf("Failed to unset env var: %v", err)
		}
	}
}
