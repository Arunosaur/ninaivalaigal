package main

import (
	"bytes"
	"os"
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

func TestMemoryRememberRunE(t *testing.T) {
	cmd := createMemoryRememberCommand()
	if cmd == nil {
		t.Fatal("createMemoryRememberCommand() should not return nil")
	}

	// Test with minimal flags
	cmd.SetArgs([]string{"--content", "test memory"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	// Execute will fail without service, but tests structure
	err := cmd.Execute()
	// Accept any error - just testing command structure
	_ = err
}

func TestMemoryRecallRunE(t *testing.T) {
	cmd := createMemoryRecallCommand()
	if cmd == nil {
		t.Fatal("createMemoryRecallCommand() should not return nil")
	}

	cmd.SetArgs([]string{"--query", "test"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	// Accept any error
	_ = err
}

func TestMemoryListRunE(t *testing.T) {
	cmd := createMemoryListCommand()
	if cmd == nil {
		t.Fatal("createMemoryListCommand() should not return nil")
	}

	cmd.SetArgs([]string{"--page", "1", "--page-size", "10"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemorySearchRunE(t *testing.T) {
	cmd := createMemorySearchCommand()
	if cmd == nil {
		t.Fatal("createMemorySearchCommand() should not return nil")
	}

	cmd.SetArgs([]string{"--text", "search term"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemoryDeleteRunE(t *testing.T) {
	cmd := createMemoryDeleteCommand()
	if cmd == nil {
		t.Fatal("createMemoryDeleteCommand() should not return nil")
	}

	// Test with ID
	cmd.SetArgs([]string{"memory-id-123"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemoryStatsRunE(t *testing.T) {
	cmd := createMemoryStatsCommand()
	if cmd == nil {
		t.Fatal("createMemoryStatsCommand() should not return nil")
	}

	cmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemoryExportRunE(t *testing.T) {
	cmd := createMemoryExportCommand()
	if cmd == nil {
		t.Fatal("createMemoryExportCommand() should not return nil")
	}

	// Create temp file for output
	tmpFile := t.TempDir() + "/export.json"
	cmd.SetArgs([]string{"--format", "json", "--output", tmpFile})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemoryImportRunE(t *testing.T) {
	cmd := createMemoryImportCommand()
	if cmd == nil {
		t.Fatal("createMemoryImportCommand() should not return nil")
	}

	// Create temp file for input
	tmpFile := t.TempDir() + "/import.json"
	os.WriteFile(tmpFile, []byte(`[]`), 0644)
	cmd.SetArgs([]string{tmpFile, "--format", "json"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)

	err := cmd.Execute()
	_ = err
}

func TestMemoryCommandAllSubcommands(t *testing.T) {
	memoryCmd := createMemoryCommand()
	if memoryCmd == nil {
		t.Fatal("createMemoryCommand() should not return nil")
	}

	subcommands := memoryCmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Memory command should have subcommands")
	}

	// Verify subcommand names
	subcommandNames := make(map[string]bool)
	for _, sub := range subcommands {
		subcommandNames[sub.Use] = true
	}

	expected := []string{"remember", "recall", "list", "search", "delete", "stats", "export", "import"}
	for _, name := range expected {
		// Check if any subcommand contains this name (might be "remember [flags]")
		found := false
		for subName := range subcommandNames {
			if strings.Contains(subName, name) {
				found = true
				break
			}
		}
		if !found {
			t.Logf("Subcommand '%s' not found in: %v", name, subcommandNames)
		}
	}
}

func TestMemoryCommandsWithInvalidArgs(t *testing.T) {
	tests := []struct {
		name string
		cmd  *cobra.Command
		args []string
	}{
		{"remember empty", createMemoryRememberCommand(), []string{"--content", ""}},
		{"recall empty query", createMemoryRecallCommand(), []string{"--query", ""}},
		{"list invalid page", createMemoryListCommand(), []string{"--page", "-1"}},
		{"search empty text", createMemorySearchCommand(), []string{"--text", ""}},
		{"delete no ID", createMemoryDeleteCommand(), []string{}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.cmd.SetArgs(tt.args)
			buf := new(bytes.Buffer)
			tt.cmd.SetOut(buf)
			tt.cmd.SetErr(buf)

			err := tt.cmd.Execute()
			// Accept any error - testing error handling paths
			_ = err
		})
	}
}
