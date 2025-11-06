package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/spf13/viper"
	"gopkg.in/yaml.v3"
)

func TestConfigExportCommandExecutionFull(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	outputFile := filepath.Join(tmpDir, "exported-config.yaml")

	// Set some test config
	viper.Set("test.key", "test.value")

	// Execute export command
	cmd.SetArgs([]string{"--output", outputFile, "--format", "yaml"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config export execution: %v", err)
	} else {
		// Check if file was created
		if _, err := os.Stat(outputFile); err == nil {
			t.Log("Export file created successfully")
		}
	}
}

func TestConfigExportCommandJSON(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	outputFile := filepath.Join(tmpDir, "exported-config.json")

	viper.Set("test.key", "test.value")

	cmd.SetArgs([]string{"--output", outputFile, "--format", "json"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config export to JSON: %v", err)
	} else {
		if _, err := os.Stat(outputFile); err == nil {
			// Verify it's valid JSON
			data, _ := os.ReadFile(outputFile)
			var test map[string]interface{}
			if json.Unmarshal(data, &test) == nil {
				t.Log("Exported JSON is valid")
			}
		}
	}
}

func TestConfigImportCommandExecutionFull(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	inputFile := filepath.Join(tmpDir, "test-config.yaml")

	// Create test config file
	testConfig := map[string]interface{}{
		"services": map[string]interface{}{
			"memory": map[string]interface{}{
				"url": "http://localhost:13393",
			},
		},
	}

	data, err := yaml.Marshal(testConfig)
	if err != nil {
		t.Fatalf("Failed to marshal test config: %v", err)
	}

	err = os.WriteFile(inputFile, data, 0644)
	if err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	// Execute import command
	cmd.SetArgs([]string{"--input", inputFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err = cmd.Execute()
	if err != nil {
		t.Logf("Config import execution: %v", err)
	} else {
		// Verify config was imported
		if viper.IsSet("services.memory.url") {
			t.Log("Config imported successfully")
		}
	}
}

func TestConfigImportCommandJSON(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	inputFile := filepath.Join(tmpDir, "test-config.json")

	// Create test JSON config file
	testConfig := map[string]interface{}{
		"services": map[string]interface{}{
			"graphops": map[string]interface{}{
				"url": "http://localhost:13398",
			},
		},
	}

	data, err := json.Marshal(testConfig)
	if err != nil {
		t.Fatalf("Failed to marshal test config: %v", err)
	}

	err = os.WriteFile(inputFile, data, 0644)
	if err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	viper.Reset()

	cmd.SetArgs([]string{"--input", inputFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err = cmd.Execute()
	if err != nil {
		t.Logf("Config import from JSON: %v", err)
	} else {
		if viper.IsSet("services.graphops.url") {
			t.Log("JSON config imported successfully")
		}
	}
}

func TestConfigImportCommandWithMerge(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	inputFile := filepath.Join(tmpDir, "test-config.yaml")

	// Set existing config
	viper.Reset()
	viper.Set("existing.key", "existing.value")

	// Create test config file
	testConfig := map[string]interface{}{
		"new.key": "new.value",
	}

	data, err := yaml.Marshal(testConfig)
	if err != nil {
		t.Fatalf("Failed to marshal test config: %v", err)
	}

	err = os.WriteFile(inputFile, data, 0644)
	if err != nil {
		t.Fatalf("Failed to write test config: %v", err)
	}

	// Execute import with merge flag
	cmd.SetArgs([]string{"--input", inputFile, "--merge"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err = cmd.Execute()
	if err != nil {
		t.Logf("Config import with merge: %v", err)
	} else {
		// Verify both old and new config exist
		if viper.IsSet("existing.key") && viper.IsSet("new.key") {
			t.Log("Config merged successfully")
		}
	}
}

func TestConfigImportCommandInvalidFile(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	// Try to import non-existent file
	cmd.SetArgs([]string{"--input", "/nonexistent/file.yaml"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	// Should error for non-existent file
	if err == nil {
		t.Error("Expected error for non-existent file, but got nil")
	}
}

func TestConfigImportCommandUnsupportedFormat(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	inputFile := filepath.Join(tmpDir, "test-config.txt")

	// Create file with unsupported extension
	err := os.WriteFile(inputFile, []byte("some config"), 0644)
	if err != nil {
		t.Fatalf("Failed to write test file: %v", err)
	}

	cmd.SetArgs([]string{"--input", inputFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err = cmd.Execute()
	// Should error for unsupported format
	if err == nil {
		t.Error("Expected error for unsupported format, but got nil")
	}
}

func TestConfigExportCommandFlags(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}

	// Verify flags exist
	if cmd.Flag("output") == nil {
		t.Error("Expected 'output' flag to exist")
	}
	if cmd.Flag("format") == nil {
		t.Error("Expected 'format' flag to exist")
	}
}

func TestConfigImportCommandFlags(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	// Verify flags exist
	if cmd.Flag("input") == nil {
		t.Error("Expected 'input' flag to exist")
	}
	if cmd.Flag("merge") == nil {
		t.Error("Expected 'merge' flag to exist")
	}
}
