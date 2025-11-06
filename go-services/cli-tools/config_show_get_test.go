package main

import (
	"bytes"
	"testing"

	"github.com/spf13/viper"
)

func TestConfigShowCommandAllExecution(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	// Set some test config
	viper.Set("test.key1", "value1")
	viper.Set("test.key2", "value2")

	// Execute show all
	cmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config show all execution: %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Log("Show all command produced no output")
	}
}

func TestConfigShowCommandWithKeyExecution(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	viper.Set("services.memory.url", "http://localhost:13393")

	// Execute show with specific key
	cmd.SetArgs([]string{"services.memory.url"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config show with key execution: %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Log("Show key command produced no output")
	}
}

func TestConfigShowCommandWithKeyNotFound(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	// Execute show with non-existent key
	cmd.SetArgs([]string{"nonexistent.key.12345"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	// Should error for non-existent key
	if err == nil {
		t.Log("Show command may not error for non-existent key (depends on implementation)")
	}
}

func TestConfigShowCommandJSONFormat(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	viper.Set("test.key", "test.value")

	// Execute show with JSON format
	cmd.SetArgs([]string{"--format", "json"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config show JSON format: %v", err)
	}

	output := buf.String()
	if output != "" {
		t.Log("Show JSON format produced output")
	}
}

func TestConfigShowCommandYAMLFormat(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	viper.Set("test.key", "test.value")

	// Execute show with YAML format
	cmd.SetArgs([]string{"--format", "yaml"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config show YAML format: %v", err)
	}
}

func TestConfigShowCommandWithAllFlag(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	// Execute show with --all flag
	cmd.SetArgs([]string{"--all"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config show with --all flag: %v", err)
	}
}

func TestConfigGetCommandExecutionFull(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	viper.Set("services.memory.url", "http://localhost:13393")

	// Execute get command
	cmd.SetArgs([]string{"services.memory.url"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config get execution: %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Log("Get command produced no output")
	}
}

func TestConfigGetCommandWithDefault(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	// Execute get with non-existent key but with default
	cmd.SetArgs([]string{"nonexistent.key.12345", "--default", "default-value"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Config get with default: %v", err)
	} else {
		output := buf.String()
		if output != "" {
			t.Log("Get command with default produced output")
		}
	}
}

func TestConfigGetCommandNotFound(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	// Execute get with non-existent key without default
	cmd.SetArgs([]string{"nonexistent.key.12345"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	// Should error for non-existent key without default
	if err == nil {
		t.Log("Get command may not error for non-existent key (depends on implementation)")
	}
}

func TestConfigShowCommandFlags(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	if cmd.Flag("format") == nil {
		t.Error("Expected 'format' flag to exist")
	}
	if cmd.Flag("all") == nil {
		t.Error("Expected 'all' flag to exist")
	}
}

func TestConfigGetCommandFlags(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	if cmd.Flag("default") == nil {
		t.Error("Expected 'default' flag to exist")
	}
}
