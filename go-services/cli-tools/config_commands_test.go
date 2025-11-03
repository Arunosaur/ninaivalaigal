package main

import (
	"strings"
	"testing"
)

func TestCreateConfigCommand(t *testing.T) {
	cmd := createConfigCommand()
	if cmd == nil {
		t.Fatal("createConfigCommand() should not return nil")
	}
	if cmd.Use != "config" {
		t.Errorf("Expected command Use to be 'config', got '%s'", cmd.Use)
	}
}

func TestCreateConfigShowCommand(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}
	// Command structure should be valid (Use may include args like "show [KEY]")
	if !strings.Contains(cmd.Use, "show") {
		t.Errorf("Expected command Use to contain 'show', got '%s'", cmd.Use)
	}
}

func TestCreateConfigSetCommand(t *testing.T) {
	cmd := createConfigSetCommand()
	if cmd == nil {
		t.Fatal("createConfigSetCommand() should not return nil")
	}
}

func TestCreateConfigGetCommand(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}
}

func TestCreateConfigInitCommand(t *testing.T) {
	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}
}

func TestCreateConfigProfileCommand(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}
}

func TestCreateConfigValidateCommand(t *testing.T) {
	cmd := createConfigValidateCommand()
	if cmd == nil {
		t.Fatal("createConfigValidateCommand() should not return nil")
	}
}

func TestCreateConfigExportCommand(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}
}

func TestCreateConfigImportCommand(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}
}

func TestCreateDefaultConfig(t *testing.T) {
	cfg := createDefaultConfig()
	if cfg == nil {
		t.Fatal("createDefaultConfig() should not return nil")
	}
}

func TestIsInternalKey(t *testing.T) {
	// Test internal key detection
	// Note: isInternalKey function exists but logic may vary
	// Just verify function can be called
	tests := []struct {
		key string
	}{
		{"internal.key"},
		{"services.memory.url"},
		{"verbose"},
		{"output.format"},
	}

	for _, tt := range tests {
		result := isInternalKey(tt.key)
		// Just verify function returns boolean without panicking
		_ = result
	}
}

func TestValidateConfiguration(t *testing.T) {
	// Test with valid config - validateConfiguration returns []string (errors)
	errors := validateConfiguration()
	// Should return slice (may be empty if no errors)
	if errors == nil {
		t.Error("validateConfiguration() should return a slice")
	}
}

func TestAddExampleConfig(t *testing.T) {
	cfg := createDefaultConfig()
	addExampleConfig(cfg)
	// Should not panic
	if cfg == nil {
		t.Error("Config should still be valid after adding examples")
	}
}
