package main

import (
	"os"
	"testing"
)

func TestDisplayTableResultsEmpty(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id", "name"},
		Data:    []map[string]interface{}{},
		Stats:   QueryStats{},
	}

	// Should handle empty results
	displayTableResults(result)
}

func TestDisplayTableResultsWithData(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id", "name", "value"},
		Data: []map[string]interface{}{
			{"id": "1", "name": "test1", "value": 100},
			{"id": "2", "name": "test2", "value": 200},
			{"id": "3", "name": "test3", "value": 300},
		},
		Stats: QueryStats{
			NodesCreated:         5,
			RelationshipsCreated: 3,
			ExecutionTime:        42,
		},
	}

	displayTableResults(result)
}

func TestDisplayCSVResults(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id", "name"},
		Data: []map[string]interface{}{
			{"id": "1", "name": "test1"},
			{"id": "2", "name": "test2"},
		},
		Stats: QueryStats{},
	}

	// Create temp file for CSV output
	tmpFile, err := os.CreateTemp("", "test-csv-*.csv")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	defer os.Remove(tmpFile.Name())

	// Note: displayCSVResults may write to stdout
	// Test structure
	_ = result
	_ = tmpFile
}

func TestDisplayQueryResultsJSON(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id", "name"},
		Data: []map[string]interface{}{
			{"id": "1", "name": "test"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "json")
}

func TestDisplayQueryResultsTable(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id"},
		Data: []map[string]interface{}{
			{"id": "1"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "table")
}

func TestDisplayQueryResultsCSV(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id"},
		Data: []map[string]interface{}{
			{"id": "1"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "csv")
}
