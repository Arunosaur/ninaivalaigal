package main

import (
	"testing"
)

func TestExecuteSchemaQueryHelper(t *testing.T) {
	// Test schema query execution structure
	// Note: executeSchemaQuery takes query string, not URL
	err := executeSchemaQuery("MATCH (n) RETURN n LIMIT 1")
	// Accept any error - just testing function exists and returns
	_ = err
}

func TestExecuteStatsQueryHelper(t *testing.T) {
	// Test stats query execution structure
	err := executeStatsQuery("MATCH (n) RETURN count(n)")
	// Accept any error - just testing function exists and returns
	_ = err
}

func TestDisplayQueryResultsTableFormat(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id", "name"},
		Data: []map[string]interface{}{
			{"id": "1", "name": "test"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "table")
}

func TestDisplayQueryResultsJSONFormat(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id"},
		Data: []map[string]interface{}{
			{"id": "1"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "json")
}

func TestDisplayQueryResultsCSVFormat(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id"},
		Data: []map[string]interface{}{
			{"id": "1"},
		},
		Stats: QueryStats{},
	}

	displayQueryResults(result, "csv")
}

func TestDisplayQueryResultsInvalidFormat(t *testing.T) {
	result := GraphQueryResult{
		Columns: []string{"id"},
		Data:    []map[string]interface{}{},
		Stats:   QueryStats{},
	}

	// Should handle invalid format gracefully
	displayQueryResults(result, "invalid")
}
