package main

import (
	"testing"
)

func TestCreateServerCommand(t *testing.T) {
	cmd := createServerCommand()
	if cmd == nil {
		t.Fatal("createServerCommand() should not return nil")
	}
}

func TestCreateServerStartCommand(t *testing.T) {
	cmd := createServerStartCommand()
	if cmd == nil {
		t.Fatal("createServerStartCommand() should not return nil")
	}
}

func TestCreateServerStopCommand(t *testing.T) {
	cmd := createServerStopCommand()
	if cmd == nil {
		t.Fatal("createServerStopCommand() should not return nil")
	}
}

func TestCreateServerRestartCommand(t *testing.T) {
	cmd := createServerRestartCommand()
	if cmd == nil {
		t.Fatal("createServerRestartCommand() should not return nil")
	}
}

func TestCreateServerStatusCommand(t *testing.T) {
	cmd := createServerStatusCommand()
	if cmd == nil {
		t.Fatal("createServerStatusCommand() should not return nil")
	}
}

func TestCreateServerLogsCommand(t *testing.T) {
	cmd := createServerLogsCommand()
	if cmd == nil {
		t.Fatal("createServerLogsCommand() should not return nil")
	}
}

func TestCreateServerBuildCommand(t *testing.T) {
	cmd := createServerBuildCommand()
	if cmd == nil {
		t.Fatal("createServerBuildCommand() should not return nil")
	}
}
