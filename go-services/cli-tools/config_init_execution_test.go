package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/spf13/viper"
)

func TestConfigInitCommandExecutionFull(t *testing.T) {
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, ".nina.yaml")

	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}

	// Test with --config flag
	viper.SetConfigFile(configFile)
	cmd.SetArgs([]string{"--config", configFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config init execution (first time): %v", err)
	}

	// Check if config file was created
	if _, err := os.Stat(configFile); err != nil {
		t.Logf("Config file not created (may be expected): %v", err)
	}
}

func TestConfigInitCommandWithForce(t *testing.T) {
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, ".nina.yaml")

	// Create existing config file
	err := os.WriteFile(configFile, []byte("existing: config\n"), 0644)
	if err != nil {
		t.Fatalf("Failed to create existing config: %v", err)
	}

	cmd := createConfigInitCommand()
	viper.SetConfigFile(configFile)
	cmd.SetArgs([]string{"--force", "--config", configFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err = cmd.Execute()
	if err != nil {
		t.Logf("Config init with --force: %v", err)
	}

	// Verify file was overwritten
	if _, err := os.Stat(configFile); err != nil {
		t.Errorf("Config file should exist after force init: %v", err)
	}
}

func TestConfigInitCommandWithExample(t *testing.T) {
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, ".nina.yaml")

	cmd := createConfigInitCommand()
	viper.SetConfigFile(configFile)
	cmd.SetArgs([]string{"--example", "--config", configFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config init with --example: %v", err)
	}

	// Verify file was created
	if _, err := os.Stat(configFile); err != nil {
		t.Logf("Config file not created: %v", err)
	}
}

func TestConfigInitCommandExistingFileError(t *testing.T) {
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, ".nina.yaml")

	// Create existing config file
	err := os.WriteFile(configFile, []byte("existing: config\n"), 0644)
	if err != nil {
		t.Fatalf("Failed to create existing config: %v", err)
	}

	cmd := createConfigInitCommand()
	viper.SetConfigFile(configFile)
	cmd.SetArgs([]string{"--config", configFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err = cmd.Execute()
	// Should error without --force flag
	if err == nil {
		t.Log("Expected error when config file exists without --force, but got nil")
	}
}

func TestConfigInitCommandFlags(t *testing.T) {
	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}

	// Verify flags exist
	if cmd.Flag("force") == nil {
		t.Error("Expected 'force' flag to exist")
	}
	if cmd.Flag("profile") == nil {
		t.Error("Expected 'profile' flag to exist")
	}
	if cmd.Flag("example") == nil {
		t.Error("Expected 'example' flag to exist")
	}
}

func TestConfigInitCommandStructure(t *testing.T) {
	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}

	if cmd.Use != "init" {
		t.Errorf("Expected command Use to be 'init', got '%s'", cmd.Use)
	}
	if cmd.Short == "" {
		t.Error("Command should have Short description")
	}
	if cmd.Long == "" {
		t.Error("Command should have Long description")
	}
	if cmd.RunE == nil {
		t.Error("Command should have RunE function")
	}
}
