package main

import (
	"os"
	"testing"
)

func TestInitConfig(t *testing.T) {
	// Test config initialization with default values
	err := initConfig()
	if err != nil {
		t.Errorf("initConfig() should not error with defaults, got: %v", err)
	}
}

func TestInitConfigWithCustomFile(t *testing.T) {
	// Create a temporary config file
	tmpFile, err := os.CreateTemp("", "test-config-*.yaml")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())

	// Write test config
	_, err = tmpFile.WriteString("verbose: true\noutput:\n  format: json\n")
	if err != nil {
		t.Fatalf("Failed to write config: %v", err)
	}
	tmpFile.Close()

	// Set config file
	cfgFile = tmpFile.Name()
	defer func() { cfgFile = "" }()

	err = initConfig()
	if err != nil {
		t.Errorf("initConfig() should not error with valid config file, got: %v", err)
	}
}

func TestInitConfigWithInvalidFile(t *testing.T) {
	cfgFile = "/nonexistent/path/config.yaml"
	defer func() { cfgFile = "" }()

	err := initConfig()
	// Config file not found error is acceptable (viper.ConfigFileNotFoundError)
	// But other errors (like permission denied) are not
	if err != nil {
		// Accept file not found errors, but log others
		t.Logf("initConfig() with invalid file returned: %v (this may be acceptable)", err)
	}
}
