package main

import (
	"testing"
)

func TestCreateLoadTestCommand(t *testing.T) {
	cmd := createLoadTestCommand()
	if cmd == nil {
		t.Fatal("createLoadTestCommand() should not return nil")
	}
}

func TestCreateLoadTestHTTPCommand(t *testing.T) {
	cmd := createLoadTestHTTPCommand()
	if cmd == nil {
		t.Fatal("createLoadTestHTTPCommand() should not return nil")
	}
}

func TestCreateLoadTestScenarioCommand(t *testing.T) {
	cmd := createLoadTestScenarioCommand()
	if cmd == nil {
		t.Fatal("createLoadTestScenarioCommand() should not return nil")
	}
}

func TestCreateLoadTestQuickCommand(t *testing.T) {
	cmd := createLoadTestQuickCommand()
	if cmd == nil {
		t.Fatal("createLoadTestQuickCommand() should not return nil")
	}
}

func TestCreateLoadTestProfileCommand(t *testing.T) {
	cmd := createLoadTestProfileCommand()
	if cmd == nil {
		t.Fatal("createLoadTestProfileCommand() should not return nil")
	}
}

func TestCreateLoadTestValidateCommand(t *testing.T) {
	cmd := createLoadTestValidateCommand()
	if cmd == nil {
		t.Fatal("createLoadTestValidateCommand() should not return nil")
	}
}
