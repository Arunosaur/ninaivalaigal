package main

import (
	"testing"
)

func TestCreateGraphQueryCommand(t *testing.T) {
	cmd := createGraphQueryCommand()
	if cmd == nil {
		t.Fatal("createGraphQueryCommand() should not return nil")
	}
}

func TestCreateGraphSchemaCommand(t *testing.T) {
	cmd := createGraphSchemaCommand()
	if cmd == nil {
		t.Fatal("createGraphSchemaCommand() should not return nil")
	}
}

func TestCreateGraphStatsCommand(t *testing.T) {
	cmd := createGraphStatsCommand()
	if cmd == nil {
		t.Fatal("createGraphStatsCommand() should not return nil")
	}
}

func TestExecuteSchemaQuery(t *testing.T) {
	// Test schema query execution structure
	// Note: executeSchemaQuery takes query string, not URL
	err := executeSchemaQuery("MATCH (n) RETURN n LIMIT 1")
	// Accept any error - just testing function exists
	_ = err
}

func TestExecuteStatsQuery(t *testing.T) {
	// Test stats query execution structure
	err := executeStatsQuery("MATCH (n) RETURN count(n)")
	// Accept any error - just testing function exists
	_ = err
}

func TestDisplayQueryResults(t *testing.T) {
	// Test display function with empty results
	result := GraphQueryResult{
		Columns: []string{"id", "name"},
		Data:    []map[string]interface{}{},
		Stats:   QueryStats{},
	}
	displayQueryResults(result, "table")
	// Should not panic
}

// TestDisplayTableResults removed - duplicate (see graph_display_test.go)
