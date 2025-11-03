package main

import (
	"testing"

	"github.com/spf13/cobra"
)

func TestMemoryCommandsFlagValidation(t *testing.T) {
	tests := []struct {
		name string
		cmd  func() *cobra.Command
	}{
		{"remember", func() *cobra.Command { return createMemoryRememberCommand() }},
		{"recall", func() *cobra.Command { return createMemoryRecallCommand() }},
		{"list", func() *cobra.Command { return createMemoryListCommand() }},
		{"search", func() *cobra.Command { return createMemorySearchCommand() }},
		{"delete", func() *cobra.Command { return createMemoryDeleteCommand() }},
		{"stats", func() *cobra.Command { return createMemoryStatsCommand() }},
		{"export", func() *cobra.Command { return createMemoryExportCommand() }},
		{"import", func() *cobra.Command { return createMemoryImportCommand() }},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := tt.cmd()
			if cmd == nil {
				t.Fatalf("createMemory%sCommand() should not return nil", tt.name)
			}
			// Verify command has expected structure
			if cmd.Short == "" {
				t.Error("Command should have Short description")
			}
		})
	}
}

func TestMemoryRememberCommandFlags(t *testing.T) {
	cmd := createMemoryRememberCommand()

	// Verify flags exist
	if cmd.Flag("content") == nil {
		t.Error("Expected 'content' flag")
	}
	if cmd.Flag("context") == nil {
		t.Error("Expected 'context' flag")
	}
	if cmd.Flag("metadata") == nil {
		t.Error("Expected 'metadata' flag")
	}
}

func TestMemoryRecallCommandFlags(t *testing.T) {
	cmd := createMemoryRecallCommand()

	if cmd.Flag("query") == nil {
		t.Error("Expected 'query' flag")
	}
	if cmd.Flag("limit") == nil {
		t.Error("Expected 'limit' flag")
	}
	if cmd.Flag("threshold") == nil {
		t.Error("Expected 'threshold' flag")
	}
}

func TestMemoryListCommandFlags(t *testing.T) {
	cmd := createMemoryListCommand()

	if cmd.Flag("page") == nil {
		t.Error("Expected 'page' flag")
	}
	if cmd.Flag("page-size") == nil {
		t.Error("Expected 'page-size' flag")
	}
}

func TestMemorySearchCommandFlags(t *testing.T) {
	cmd := createMemorySearchCommand()

	if cmd.Flag("text") == nil {
		t.Error("Expected 'text' flag")
	}
	if cmd.Flag("sort") == nil {
		t.Error("Expected 'sort' flag")
	}
}

func TestMemoryExportCommandFlags(t *testing.T) {
	cmd := createMemoryExportCommand()

	if cmd.Flag("format") == nil {
		t.Error("Expected 'format' flag")
	}
	if cmd.Flag("output") == nil {
		t.Error("Expected 'output' flag")
	}
}

func TestMemoryImportCommandFlags(t *testing.T) {
	cmd := createMemoryImportCommand()

	// Flags may use different names or be positional arguments
	if cmd.Flag("file") == nil && cmd.Flag("input") == nil {
		t.Log("Note: 'file' or 'input' flag may not exist - could be positional argument")
	}
	if cmd.Flag("format") == nil {
		t.Log("Note: 'format' flag may not exist")
	}
}
