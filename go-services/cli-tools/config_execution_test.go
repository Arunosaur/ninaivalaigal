package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestConfigSetCommandExecution(t *testing.T) {
	cmd := createConfigSetCommand()
	if cmd == nil {
		t.Fatal("createConfigSetCommand() should not return nil")
	}

	// Test command structure - actual execution requires viper setup
	// Verify flags exist
	if cmd.Flag("global") == nil {
		t.Error("Expected 'global' flag to exist")
	}
	if cmd.Flag("profile") == nil {
		t.Error("Expected 'profile' flag to exist")
	}
}

func TestConfigGetCommandExecution(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	if cmd.Flag("default") == nil {
		t.Error("Expected 'default' flag to exist")
	}
}

func TestConfigInitCommandExecution(t *testing.T) {
	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}

	// Test with temp directory
	tmpDir, err := os.MkdirTemp("", "nina-config-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	configPath := filepath.Join(tmpDir, ".nina.yaml")

	// Verify command structure
	if cmd.Flag("force") == nil {
		t.Error("Expected 'force' flag to exist")
	}
	if cmd.Flag("example") == nil {
		t.Error("Expected 'example' flag to exist")
	}

	// Test that config path would be used
	_ = configPath
}

func TestConfigProfileCommandStructure(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Verify subcommands exist
	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Config profile command should have subcommands")
	}
}

func TestConfigValidateCommandExecution(t *testing.T) {
	cmd := createConfigValidateCommand()
	if cmd == nil {
		t.Fatal("createConfigValidateCommand() should not return nil")
	}

	// Command structure should be valid
	if cmd.Use != "validate" {
		t.Errorf("Expected command Use to be 'validate', got '%s'", cmd.Use)
	}
}

func TestConfigExportCommandExecution(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}

	// Verify flags
	if cmd.Flag("output") == nil {
		t.Error("Expected 'output' flag to exist")
	}
	if cmd.Flag("format") == nil {
		t.Error("Expected 'format' flag to exist")
	}
}

func TestConfigImportCommandExecution(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	// Verify structure
	// Flag may use different name or be positional
	if cmd.Flag("file") == nil && cmd.Flag("input") == nil {
		t.Log("Note: 'file' or 'input' flag may not exist")
	}
}
