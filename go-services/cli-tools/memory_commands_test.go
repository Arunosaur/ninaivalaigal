package main

import (
	"testing"
)

func TestMemoryCommandExists(t *testing.T) {
	// Test that memory command can be created
	cmd := createMemoryCommand()
	if cmd == nil {
		t.Fatal("Expected memory command to be created, got nil")
	}

	if cmd.Use == "" {
		t.Error("Expected memory command to have Use field set")
	}

	if cmd.Short == "" {
		t.Error("Expected memory command to have Short description")
	}
}

func TestMemoryCommandSubcommands(t *testing.T) {
	cmd := createMemoryCommand()

	// Check that memory command has expected subcommands
	// Note: Subcommand names may vary, this is a basic check
	if len(cmd.Commands()) == 0 {
		t.Error("Expected memory command to have subcommands, found none")
	}
}
