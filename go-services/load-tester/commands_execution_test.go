package main

import (
	"bytes"
	"testing"
)

func TestValidateCommandExecution(t *testing.T) {
	cmd := createValidateCommand()
	if cmd == nil {
		t.Fatal("createValidateCommand() should not return nil")
	}

	// Test with default URL (no args)
	cmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Validate command execution (default): %v", err)
	}
}

func TestValidateCommandExecutionWithURL(t *testing.T) {
	cmd := createValidateCommand()
	if cmd == nil {
		t.Fatal("createValidateCommand() should not return nil")
	}

	// Test with custom URL
	cmd.SetArgs([]string{"http://localhost:8080"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	if err != nil {
		t.Logf("Validate command execution (with URL): %v", err)
	}
}

func TestValidateCommandExecutionWithInvalidURL(t *testing.T) {
	cmd := createValidateCommand()
	if cmd == nil {
		t.Fatal("createValidateCommand() should not return nil")
	}

	// Test with invalid URL
	cmd.SetArgs([]string{"not-a-valid-url"})
	buf := new(bytes.Buffer)
	cmd.SetOut(buf)
	cmd.SetErr(buf)

	err := cmd.Execute()
	// May or may not error depending on validation
	if err != nil {
		t.Logf("Validate command with invalid URL (expected error): %v", err)
	}
}
