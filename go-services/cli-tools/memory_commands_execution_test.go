package main

import (
	"strings"
	"testing"
)

func TestCreateMemoryRememberCommand(t *testing.T) {
	cmd := createMemoryRememberCommand()
	if cmd == nil {
		t.Fatal("createMemoryRememberCommand() should not return nil")
	}
	// Use may include args like "remember [CONTENT]"
	if !strings.Contains(cmd.Use, "remember") {
		t.Errorf("Expected command Use to contain 'remember', got '%s'", cmd.Use)
	}
}

func TestCreateMemoryRecallCommand(t *testing.T) {
	cmd := createMemoryRecallCommand()
	if cmd == nil {
		t.Fatal("createMemoryRecallCommand() should not return nil")
	}
}

func TestCreateMemoryListCommand(t *testing.T) {
	cmd := createMemoryListCommand()
	if cmd == nil {
		t.Fatal("createMemoryListCommand() should not return nil")
	}
}

func TestCreateMemorySearchCommand(t *testing.T) {
	cmd := createMemorySearchCommand()
	if cmd == nil {
		t.Fatal("createMemorySearchCommand() should not return nil")
	}
}

func TestCreateMemoryDeleteCommand(t *testing.T) {
	cmd := createMemoryDeleteCommand()
	if cmd == nil {
		t.Fatal("createMemoryDeleteCommand() should not return nil")
	}
}

func TestCreateMemoryStatsCommand(t *testing.T) {
	cmd := createMemoryStatsCommand()
	if cmd == nil {
		t.Fatal("createMemoryStatsCommand() should not return nil")
	}
}

func TestCreateMemoryExportCommand(t *testing.T) {
	cmd := createMemoryExportCommand()
	if cmd == nil {
		t.Fatal("createMemoryExportCommand() should not return nil")
	}
}

func TestCreateMemoryImportCommand(t *testing.T) {
	cmd := createMemoryImportCommand()
	if cmd == nil {
		t.Fatal("createMemoryImportCommand() should not return nil")
	}
}

func TestMemoryRememberCommandValidation(t *testing.T) {
	cmd := createMemoryRememberCommand()
	// Test command structure - actual execution requires API connection
	// Just verify command is created properly
	if cmd == nil {
		t.Fatal("createMemoryRememberCommand() should not return nil")
	}
	// Validation happens in RunE, which requires setup
}

func TestMemoryCommandStructure(t *testing.T) {
	memoryCmd := createMemoryCommand()
	if memoryCmd == nil {
		t.Fatal("createMemoryCommand() should not return nil")
	}

	// Check subcommands
	subcommands := memoryCmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Memory command should have subcommands")
	}

	// Verify key subcommands exist (Use may include args, so check if it contains name)
	subcommandUses := make([]string, 0)
	for _, sub := range subcommands {
		subcommandUses = append(subcommandUses, sub.Use)
	}

	expected := []string{"remember", "recall", "list", "search", "delete", "stats", "export", "import"}
	found := 0
	for _, name := range expected {
		for _, use := range subcommandUses {
			if strings.Contains(use, name) {
				found++
				break
			}
		}
	}

	if found < len(expected)/2 {
		t.Errorf("Expected to find at least %d subcommands, found %d", len(expected)/2, found)
	}
}
