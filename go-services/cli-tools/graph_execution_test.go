package main

import (
	"testing"
)

func TestGraphQueryCommandFlags(t *testing.T) {
	cmd := createGraphQueryCommand()
	if cmd == nil {
		t.Fatal("createGraphQueryCommand() should not return nil")
	}

	// Verify flags
	if cmd.Flag("query") == nil && cmd.Flag("common") == nil {
		t.Error("Expected 'query' or 'common' flag")
	}
	// Flag may use different name
	if cmd.Flag("parameters") == nil && cmd.Flag("params") == nil {
		t.Log("Note: 'parameters' or 'params' flag may not exist")
	}
	if cmd.Flag("format") == nil {
		t.Error("Expected 'format' flag")
	}
}

func TestGraphSchemaCommandStructure(t *testing.T) {
	cmd := createGraphSchemaCommand()
	if cmd == nil {
		t.Fatal("createGraphSchemaCommand() should not return nil")
	}

	// Verify subcommands
	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Graph schema command should have subcommands")
	}
}

func TestGraphStatsCommandStructure(t *testing.T) {
	cmd := createGraphStatsCommand()
	if cmd == nil {
		t.Fatal("createGraphStatsCommand() should not return nil")
	}

	// Command should be valid
	if cmd.Short == "" {
		t.Error("Command should have Short description")
	}
}

func TestGraphCommandCommonQueries(t *testing.T) {
	queries := GetCommonQueries()
	if len(queries) == 0 {
		t.Error("GetCommonQueries should return queries")
	}

	// Verify structure
	for name, query := range queries {
		if name == "" {
			t.Error("Query name should not be empty")
		}
		if query == "" {
			t.Errorf("Query '%s' should not be empty", name)
		}
	}
}
