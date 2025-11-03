package main

import (
	"testing"
)

func TestGetDefaultProfiles(t *testing.T) {
	profiles := GetDefaultProfiles()
	if len(profiles) == 0 {
		t.Error("GetDefaultProfiles should return profiles")
	}

	// Verify expected profiles exist
	profileNames := make(map[string]bool)
	for _, p := range profiles {
		profileNames[p.Name] = true
	}

	expected := []string{"smoke", "load", "stress", "spike", "endurance"}
	for _, name := range expected {
		if !profileNames[name] {
			t.Errorf("Expected profile '%s' not found", name)
		}
	}
}

func TestGetNinaivalaigalTargets(t *testing.T) {
	targets := GetNinaivalaigalTargets()
	if len(targets) == 0 {
		t.Error("GetNinaivalaigalTargets should return targets")
	}

	// Verify target structure
	for _, target := range targets {
		if target.Name == "" {
			t.Error("Target should have a name")
		}
		if len(target.Endpoints) == 0 {
			t.Error("Target should have endpoints")
		}
	}
}

// TestLoadTestConfigDefaults removed - duplicate (see config_test.go)
