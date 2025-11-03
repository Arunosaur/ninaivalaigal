package main

import (
	"testing"
)

func TestDisplayConfigTable(t *testing.T) {
	// Test display function with sample config
	settings := map[string]interface{}{
		"services": map[string]interface{}{
			"memory": map[string]interface{}{
				"url": "http://localhost:13393",
			},
		},
		"verbose": false,
	}

	// Should not panic
	displayConfigTable(settings, false)
}

func TestDisplayConfigTableAll(t *testing.T) {
	settings := map[string]interface{}{
		"services": map[string]interface{}{
			"memory": map[string]interface{}{
				"url": "http://localhost:13393",
			},
		},
		"verbose": false,
	}

	// Test with all=true
	displayConfigTable(settings, true)
}

// TestAddSettingsToTable is tested indirectly through displayConfigTable
// (removed duplicate - see config_display_test.go)

// TestDisplayTableResults removed - duplicate (see graph_display_test.go)
// TestDisplayCSVResults removed - duplicate (see graph_display_test.go)
