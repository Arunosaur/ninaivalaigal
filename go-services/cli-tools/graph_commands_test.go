package main

import (
	"testing"
)

func TestCreateGraphCommand(t *testing.T) {
	cmd := createGraphCommand()

	if cmd == nil {
		t.Fatal("Expected graph command to be created, got nil")
	}

	if cmd.Use != "graph" {
		t.Errorf("Expected command Use to be 'graph', got '%s'", cmd.Use)
	}

	if cmd.Short == "" {
		t.Error("Expected graph command to have Short description")
	}
}

func TestGraphCommandSubcommands(t *testing.T) {
	cmd := createGraphCommand()

	if len(cmd.Commands()) == 0 {
		t.Error("Expected graph command to have subcommands, found none")
	}
}

func TestGraphQueryResult(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"name", "count"},
		Data: []map[string]interface{}{
			{"name": "test", "count": 10},
		},
		Stats: QueryStats{
			NodesCreated: 1,
		},
	}

	if len(result.Columns) == 0 {
		t.Error("Expected query result to have columns")
	}

	if len(result.Data) == 0 {
		t.Error("Expected query result to have data")
	}
}

func TestQueryStats(t *testing.T) {
	stats := QueryStats{
		NodesCreated:         5,
		NodesDeleted:         2,
		RelationshipsCreated: 3,
		ExecutionTime:        100,
	}

	if stats.NodesCreated <= 0 && stats.NodesDeleted == 0 && stats.RelationshipsCreated == 0 {
		t.Error("Expected query stats to be initialized")
	}
}

func TestGraphResponse(t *testing.T) {
	response := GraphResponse{
		Status:  "success",
		Message: "Query executed",
		Results: &GraphQueryResult{
			Columns: []string{"id"},
			Data:    []map[string]interface{}{},
		},
	}

	if response.Status == "" {
		t.Error("Expected graph response to have status")
	}

	if response.Results == nil {
		t.Error("Expected graph response to have results when provided")
	}
}
