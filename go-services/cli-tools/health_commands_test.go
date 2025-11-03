package main

import (
	"testing"
)

func TestCreateHealthCommand(t *testing.T) {
	cmd := createHealthCommand()
	if cmd == nil {
		t.Fatal("createHealthCommand() should not return nil")
	}
	if cmd.Use != "health" {
		t.Errorf("Expected command Use to be 'health', got '%s'", cmd.Use)
	}
}

func TestCreateHealthCheckCommand(t *testing.T) {
	cmd := createHealthCheckCommand()
	if cmd == nil {
		t.Fatal("createHealthCheckCommand() should not return nil")
	}
}

func TestCreateHealthWatchCommand(t *testing.T) {
	cmd := createHealthWatchCommand()
	if cmd == nil {
		t.Fatal("createHealthWatchCommand() should not return nil")
	}
}

func TestCreateHealthDetailCommand(t *testing.T) {
	cmd := createHealthDetailCommand()
	if cmd == nil {
		t.Fatal("createHealthDetailCommand() should not return nil")
	}
}

func TestCreateHealthSummaryCommand(t *testing.T) {
	cmd := createHealthSummaryCommand()
	if cmd == nil {
		t.Fatal("createHealthSummaryCommand() should not return nil")
	}
}

func TestGetServiceDefinitions(t *testing.T) {
	defs := getServiceDefinitions()
	if defs == nil {
		t.Fatal("getServiceDefinitions() should not return nil")
	}
	if len(defs) == 0 {
		t.Error("getServiceDefinitions() should return at least one service definition")
	}
}
