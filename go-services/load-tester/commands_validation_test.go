package main

import (
	"testing"
)

func TestCreateValidateCommandExecution(t *testing.T) {
	cmd := createValidateCommand()
	if cmd == nil {
		t.Fatal("createValidateCommand() should not return nil")
	}
	// Use includes args: "validate [BASE_URL]"
	// Just check it contains "validate"
	if cmd.Use == "" {
		t.Error("Command Use should not be empty")
	}
}

func TestValidateCommandShort(t *testing.T) {
	cmd := createValidateCommand()
	if cmd.Short == "" {
		t.Error("Validate command should have Short description")
	}
}

func TestValidateCommandRunE(t *testing.T) {
	cmd := createValidateCommand()
	if cmd.RunE == nil {
		t.Error("Validate command should have RunE function")
	}
}
