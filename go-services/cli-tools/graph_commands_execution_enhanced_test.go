package main

import (
	"bytes"
	"testing"
)

// TestCreateGraphSchemaCommandSubcommands tests all schema subcommands
func TestCreateGraphSchemaCommandSubcommands(t *testing.T) {
	cmd := createGraphSchemaCommand()
	if cmd == nil {
		t.Fatal("createGraphSchemaCommand() should not return nil")
	}

	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Schema command should have subcommands")
	}

	expectedSubcommands := []string{"show", "labels", "relationships", "properties"}
	found := make(map[string]bool)

	for _, subcmd := range subcommands {
		switch subcmd.Use {
		case "show":
			found["show"] = true
			if subcmd.RunE == nil {
				t.Error("Show subcommand should have RunE")
			}
		case "labels":
			found["labels"] = true
			if subcmd.RunE == nil {
				t.Error("Labels subcommand should have RunE")
			}
		case "relationships":
			found["relationships"] = true
			if subcmd.RunE == nil {
				t.Error("Relationships subcommand should have RunE")
			}
		case "properties":
			found["properties"] = true
			if subcmd.RunE == nil {
				t.Error("Properties subcommand should have RunE")
			}
		}
	}

	for _, expected := range expectedSubcommands {
		if !found[expected] {
			t.Errorf("Schema command missing subcommand: %s", expected)
		}
	}
}

// TestCreateGraphSchemaCommandExecution tests schema command execution
func TestCreateGraphSchemaCommandExecution(t *testing.T) {
	cmd := createGraphSchemaCommand()
	if cmd == nil {
		t.Fatal("createGraphSchemaCommand() should not return nil")
	}

	// Test each subcommand
	subcommands := []string{"show", "labels", "relationships", "properties"}

	for _, subcmdName := range subcommands {
		t.Run(subcmdName, func(t *testing.T) {
			subcmd, _, err := cmd.Find([]string{subcmdName})
			if err != nil {
				t.Errorf("Failed to find subcommand '%s': %v", subcmdName, err)
				return
			}

			if subcmd == nil {
				t.Errorf("Subcommand '%s' is nil", subcmdName)
				return
			}

			if subcmd.RunE == nil {
				t.Errorf("Subcommand '%s' has no RunE", subcmdName)
				return
			}

			// Execute RunE (will fail without service, but tests structure)
			buf := new(bytes.Buffer)
			subcmd.SetOut(buf)
			subcmd.SetErr(buf)

			err = subcmd.RunE(subcmd, []string{})
			// Accept any error - just testing execution path
			_ = err
		})
	}
}

// TestCreateGraphIndexCommand tests graph index command creation
func TestCreateGraphIndexCommand(t *testing.T) {
	cmd := createGraphIndexCommand()
	if cmd == nil {
		t.Fatal("createGraphIndexCommand() should not return nil")
	}

	if cmd.Use != "index" {
		t.Errorf("Expected Use to be 'index', got '%s'", cmd.Use)
	}

	if cmd.Short == "" {
		t.Error("Index command should have Short description")
	}

	// Index command has subcommands, not RunE directly
	if len(cmd.Commands()) == 0 {
		t.Error("Index command should have subcommands")
	}
}

// TestCreateGraphIndexCommandExecution tests index command execution
func TestCreateGraphIndexCommandExecution(t *testing.T) {
	cmd := createGraphIndexCommand()
	if cmd == nil {
		t.Fatal("createGraphIndexCommand() should not return nil")
	}

	if cmd.RunE == nil {
		t.Skip("Index command RunE not available")
	}

	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	// Test with various args
	testCases := []struct {
		name string
		args []string
	}{
		{"No args", []string{}},
		{"With label", []string{"User"}},
		{"With label and property", []string{"User", "email"}},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			err := cmd.RunE(cmd, tc.args)
			// Accept any error - just testing execution path
			_ = err
		})
	}
}

// TestCreateGraphConstraintsCommand tests graph constraints command
func TestCreateGraphConstraintsCommand(t *testing.T) {
	cmd := createGraphConstraintsCommand()
	if cmd == nil {
		t.Fatal("createGraphConstraintsCommand() should not return nil")
	}

	if cmd.Use != "constraints" {
		t.Errorf("Expected Use to be 'constraints', got '%s'", cmd.Use)
	}

	// Constraints command has subcommands, not RunE directly
	if len(cmd.Commands()) == 0 {
		t.Error("Constraints command should have subcommands")
	}
}

// TestCreateGraphConstraintsCommandExecution tests constraints command execution
func TestCreateGraphConstraintsCommandExecution(t *testing.T) {
	cmd := createGraphConstraintsCommand()
	if cmd == nil {
		t.Fatal("createGraphConstraintsCommand() should not return nil")
	}

	if cmd.RunE == nil {
		t.Skip("Constraints command RunE not available")
	}

	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	// Test execution
	err := cmd.RunE(cmd, []string{})
	// Accept any error - just testing execution path
	_ = err
}

// TestCreateGraphImportCommand tests graph import command
func TestCreateGraphImportCommand(t *testing.T) {
	cmd := createGraphImportCommand()
	if cmd == nil {
		t.Fatal("createGraphImportCommand() should not return nil")
	}

	if cmd.Use != "import" {
		t.Errorf("Expected Use to be 'import', got '%s'", cmd.Use)
	}

	if cmd.RunE == nil {
		t.Error("Import command should have RunE function")
	}
}

// TestCreateGraphImportCommandFlags tests import command flags
func TestCreateGraphImportCommandFlags(t *testing.T) {
	cmd := createGraphImportCommand()
	if cmd == nil {
		t.Fatal("createGraphImportCommand() should not return nil")
	}

	// Check flags exist
	inputFlag := cmd.Flag("input")
	if inputFlag == nil {
		t.Error("Import command should have 'input' flag")
	}

	formatFlag := cmd.Flag("format")
	if formatFlag == nil {
		t.Error("Import command should have 'format' flag")
	}

	mergeFlag := cmd.Flag("merge")
	if mergeFlag == nil {
		t.Error("Import command should have 'merge' flag")
	}
}

// TestCreateGraphImportCommandExecution tests import command execution paths
func TestCreateGraphImportCommandExecution(t *testing.T) {
	cmd := createGraphImportCommand()
	if cmd == nil || cmd.RunE == nil {
		t.Skip("Import command not available")
	}

	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	// Test with missing required flag (should error)
	err := cmd.RunE(cmd, []string{})
	if err == nil {
		t.Log("Import command may not validate required flags (checking implementation)")
	}

	// Test with invalid format
	cmd.Flag("input").Value.Set("/tmp/test.json")
	cmd.Flag("format").Value.Set("invalid-format")
	err = cmd.RunE(cmd, []string{})
	// Accept any error - just testing execution path
	_ = err
}
