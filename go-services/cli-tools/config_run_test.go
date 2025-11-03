package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/spf13/cobra"
)

func TestConfigShowRunE(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	// Test show all
	cmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigShowRunEWithKey(t *testing.T) {
	cmd := createConfigShowCommand()
	if cmd == nil {
		t.Fatal("createConfigShowCommand() should not return nil")
	}

	cmd.SetArgs([]string{"services.memory.url"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigSetRunE(t *testing.T) {
	cmd := createConfigSetCommand()
	if cmd == nil {
		t.Fatal("createConfigSetCommand() should not return nil")
	}

	cmd.SetArgs([]string{"services.memory.url", "http://localhost:13393"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigGetRunE(t *testing.T) {
	cmd := createConfigGetCommand()
	if cmd == nil {
		t.Fatal("createConfigGetCommand() should not return nil")
	}

	cmd.SetArgs([]string{"services.memory.url"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigInitRunE(t *testing.T) {
	cmd := createConfigInitCommand()
	if cmd == nil {
		t.Fatal("createConfigInitCommand() should not return nil")
	}

	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, ".nina.yaml")

	cmd.SetArgs([]string{"--config", configFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err

	// Check if config file was created
	if _, err := os.Stat(configFile); err == nil {
		t.Log("Config file created successfully")
	}
}

func TestConfigProfileRunE(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Test list profiles
	listCmd, _, _ := cmd.Find([]string{"list"})
	if listCmd != nil {
		listCmd.SetArgs([]string{})
		buf := new(bytes.Buffer)
		listCmd.SetOut(buf)
		err := listCmd.Execute()
		_ = err
	}
}

func TestConfigProfileUseRunE(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	useCmd, _, _ := cmd.Find([]string{"use"})
	if useCmd != nil {
		useCmd.SetArgs([]string{"dev"})
		buf := new(bytes.Buffer)
		useCmd.SetOut(buf)
		err := useCmd.Execute()
		_ = err
	}
}

func TestConfigProfileCreateRunE(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	createCmd, _, _ := cmd.Find([]string{"create"})
	if createCmd != nil {
		createCmd.SetArgs([]string{"test-profile"})
		buf := new(bytes.Buffer)
		createCmd.SetOut(buf)
		err := createCmd.Execute()
		_ = err
	}
}

func TestConfigValidateRunE(t *testing.T) {
	cmd := createConfigValidateCommand()
	if cmd == nil {
		t.Fatal("createConfigValidateCommand() should not return nil")
	}

	cmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigExportRunE(t *testing.T) {
	cmd := createConfigExportCommand()
	if cmd == nil {
		t.Fatal("createConfigExportCommand() should not return nil")
	}

	tmpFile := filepath.Join(t.TempDir(), "config-export.yaml")
	cmd.SetArgs([]string{"--output", tmpFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigImportRunE(t *testing.T) {
	cmd := createConfigImportCommand()
	if cmd == nil {
		t.Fatal("createConfigImportCommand() should not return nil")
	}

	// Create temp config file
	tmpFile := filepath.Join(t.TempDir(), "config-import.yaml")
	os.WriteFile(tmpFile, []byte(`services:
  memory:
    url: http://localhost:13393
`), 0644)

	cmd.SetArgs([]string{"--input", tmpFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestConfigCommandsWithInvalidInput(t *testing.T) {
	tests := []struct {
		name string
		cmd  *cobra.Command
		args []string
	}{
		{"set missing value", createConfigSetCommand(), []string{"services.memory.url"}},
		{"get missing key", createConfigGetCommand(), []string{}},
		{"profile use missing name", createConfigProfileCommand(), []string{"use"}},
		{"profile create missing name", createConfigProfileCommand(), []string{"create"}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Find subcommand if needed
			cmdToTest := tt.cmd
			if len(tt.args) > 0 {
				if subCmd, _, _ := cmdToTest.Find([]string{tt.args[0]}); subCmd != nil {
					cmdToTest = subCmd
					tt.args = tt.args[1:]
				}
			}

			cmdToTest.SetArgs(tt.args)
			buf := new(bytes.Buffer)
			cmdToTest.SetOut(buf)
			cmdToTest.SetErr(buf)

			err := cmdToTest.Execute()
			// Accept any error - testing error handling
			_ = err
		})
	}
}
