package main

import (
	"testing"
)

func TestConfigProfileCommandSubcommands(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Check subcommands exist
	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Profile command should have subcommands")
	}

	// Find specific subcommands by Use field
	foundList := false
	foundShow := false
	foundUse := false

	for _, subcmd := range subcommands {
		switch subcmd.Use {
		case "list":
			foundList = true
			if subcmd.Short == "" {
				t.Error("List subcommand should have Short description")
			}
			if subcmd.RunE == nil {
				t.Error("List subcommand should have RunE function")
			}
		case "show [PROFILE]":
			foundShow = true
			if subcmd.Short == "" {
				t.Error("Show subcommand should have Short description")
			}
			if subcmd.Args == nil {
				t.Error("Show subcommand should validate args")
			}
		case "use [PROFILE]":
			foundUse = true
			if subcmd.Short == "" {
				t.Error("Use subcommand should have Short description")
			}
			if subcmd.Args == nil {
				t.Error("Use subcommand should validate args")
			}
		}
	}

	if !foundList {
		t.Error("Profile command should have 'list' subcommand")
	}
	if !foundShow {
		t.Error("Profile command should have 'show' subcommand")
	}
	if !foundUse {
		t.Error("Profile command should have 'use' subcommand")
	}
}
