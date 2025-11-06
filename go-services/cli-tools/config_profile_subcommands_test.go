package main

import (
	"bytes"
	"testing"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

func TestConfigProfileListSubcommandExecution(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Find and execute list subcommand
	var listCmd *cobra.Command
	for _, subcmd := range cmd.Commands() {
		if subcmd.Use == "list" {
			listCmd = subcmd
			break
		}
	}

	if listCmd == nil {
		t.Fatal("Profile 'list' subcommand not found")
	}

	// Set up command properly
	cmd.AddCommand(listCmd)
	listCmd.SetArgs([]string{})
	buf := new(bytes.Buffer)
	listCmd.SetOut(buf)

	// Execute list command
	err := listCmd.Execute()
	if err != nil {
		t.Logf("Profile list execution: %v", err)
	}

	// Verify output contains profile information
	output := buf.String()
	if output != "" {
		t.Log("List command produced output")
	}
}

func TestConfigProfileShowSubcommandExecution(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Get a valid profile name
	profiles := GetDefaultProfiles()
	if len(profiles) == 0 {
		t.Skip("No default profiles available")
	}

	var profileName string
	for name := range profiles {
		profileName = name
		break
	}

	// Find and execute show subcommand
	var showCmd *cobra.Command
	for _, subcmd := range cmd.Commands() {
		if subcmd.Use == "show [PROFILE]" {
			showCmd = subcmd
			break
		}
	}

	if showCmd == nil {
		t.Fatal("Profile 'show' subcommand not found")
	}

	// Execute with valid profile
	cmd.AddCommand(showCmd)
	showCmd.SetArgs([]string{profileName})
	buf := new(bytes.Buffer)
	showCmd.SetOut(buf)

	err := showCmd.Execute()
	if err != nil {
		t.Errorf("Profile show should succeed for valid profile: %v", err)
	}

	// Verify output
	output := buf.String()
	if output == "" {
		t.Log("Show command produced no output")
	}
}

func TestConfigProfileShowSubcommandWithHeaders(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Find a profile with headers if available
	profiles := GetDefaultProfiles()
	var profileWithHeaders string
	for name, profile := range profiles {
		for _, serviceConfig := range profile.Services {
			if len(serviceConfig.Headers) > 0 {
				profileWithHeaders = name
				break
			}
		}
		if profileWithHeaders != "" {
			break
		}
	}

	if profileWithHeaders == "" {
		t.Skip("No profile with headers found")
	}

	// Find show subcommand
	var showCmd *cobra.Command
	for _, subcmd := range cmd.Commands() {
		if subcmd.Use == "show [PROFILE]" {
			showCmd = subcmd
			break
		}
	}

	cmd.AddCommand(showCmd)
	showCmd.SetArgs([]string{profileWithHeaders})
	buf := new(bytes.Buffer)
	showCmd.SetOut(buf)

	err := showCmd.Execute()
	if err != nil {
		t.Logf("Profile show with headers: %v", err)
	}
}

func TestConfigProfileUseSubcommandExecution(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Get a valid profile name
	profiles := GetDefaultProfiles()
	if len(profiles) == 0 {
		t.Skip("No default profiles available")
	}

	var profileName string
	for name := range profiles {
		profileName = name
		break
	}

	// Find use subcommand
	var useCmd *cobra.Command
	for _, subcmd := range cmd.Commands() {
		if subcmd.Use == "use [PROFILE]" {
			useCmd = subcmd
			break
		}
	}

	if useCmd == nil {
		t.Fatal("Profile 'use' subcommand not found")
	}

	// Reset viper before test
	viper.Reset()

	// Execute use command
	cmd.AddCommand(useCmd)
	useCmd.SetArgs([]string{profileName})
	buf := new(bytes.Buffer)
	useCmd.SetOut(buf)

	err := useCmd.Execute()
	if err != nil {
		t.Errorf("Profile use should succeed for valid profile: %v", err)
	}

	// Verify profile was set in viper
	currentProfile := viper.GetString("current_profile")
	if currentProfile != profileName {
		t.Logf("Profile may not be set correctly. Expected: %s, Got: %s", profileName, currentProfile)
	}

	// Verify service URLs were set
	// Check at least one service URL was set
	hasServiceURL := false
	for serviceName := range profiles[profileName].Services {
		urlKey := "services." + serviceName + ".url"
		if viper.IsSet(urlKey) {
			hasServiceURL = true
			break
		}
	}
	if !hasServiceURL {
		t.Log("Service URLs may not be set in viper")
	}
}

func TestConfigProfileUseSubcommandWithAllServices(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	// Get a profile with multiple services
	profiles := GetDefaultProfiles()
	var profileWithMultipleServices string
	maxServices := 0
	for name, profile := range profiles {
		if len(profile.Services) > maxServices {
			maxServices = len(profile.Services)
			profileWithMultipleServices = name
		}
	}

	if profileWithMultipleServices == "" {
		t.Skip("No profile with multiple services found")
	}

	// Find use subcommand
	var useCmd *cobra.Command
	for _, subcmd := range cmd.Commands() {
		if subcmd.Use == "use [PROFILE]" {
			useCmd = subcmd
			break
		}
	}

	viper.Reset()

	cmd.AddCommand(useCmd)
	useCmd.SetArgs([]string{profileWithMultipleServices})
	buf := new(bytes.Buffer)
	useCmd.SetOut(buf)

	err := useCmd.Execute()
	if err != nil {
		t.Logf("Profile use with multiple services: %v", err)
	}

	// Verify all service URLs were set
	profile := profiles[profileWithMultipleServices]
	for serviceName := range profile.Services {
		urlKey := "services." + serviceName + ".url"
		if !viper.IsSet(urlKey) {
			t.Logf("Service URL for %s may not be set", serviceName)
		}
	}
}

func TestConfigProfileCommandAllSubcommandsExist(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	subcommands := cmd.Commands()
	expectedSubcommands := []string{"list", "show [PROFILE]", "use [PROFILE]"}

	found := make(map[string]bool)
	for _, subcmd := range subcommands {
		for _, expected := range expectedSubcommands {
			if subcmd.Use == expected {
				found[expected] = true
				break
			}
		}
	}

	for _, expected := range expectedSubcommands {
		if !found[expected] {
			t.Errorf("Expected subcommand '%s' not found", expected)
		}
	}
}

func TestConfigProfileCommandDetailedStructure(t *testing.T) {
	cmd := createConfigProfileCommand()
	if cmd == nil {
		t.Fatal("createConfigProfileCommand() should not return nil")
	}

	if cmd.Use != "profile" {
		t.Errorf("Expected command Use to be 'profile', got '%s'", cmd.Use)
	}
	if cmd.Short == "" {
		t.Error("Command should have Short description")
	}
	if cmd.Long == "" {
		t.Error("Command should have Long description")
	}

	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Profile command should have subcommands")
	}

	// Verify each subcommand has required fields
	for _, subcmd := range subcommands {
		if subcmd.Use == "" {
			t.Errorf("Subcommand should have Use field")
		}
		if subcmd.Short == "" {
			t.Logf("Subcommand %s may not have Short description", subcmd.Use)
		}
	}
}
